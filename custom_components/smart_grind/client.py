"""Async client for the Smart Grind local HTTP and WebSocket API."""

from __future__ import annotations

import asyncio
import contextlib
import json
from collections.abc import Awaitable, Callable
from typing import Any

from aiohttp import ClientError, ClientSession, ClientWebSocketResponse, WSMsgType
from yarl import URL

from .const import COMMAND_TIMEOUT_SECONDS, DEFAULT_PORT
from .models import (
    SmartGrindCommandError,
    SmartGrindConnectionError,
    SmartGrindDeviceStatus,
    SmartGrindProtocolError,
    SmartGrindSettings,
    SmartGrindState,
)

StateCallback = Callable[[SmartGrindState], Awaitable[None] | None]


class SmartGrindClient:
    """Communicate with one Smart Grind device."""

    def __init__(self, host: str, session: ClientSession, port: int = DEFAULT_PORT) -> None:
        """Initialize the client."""
        self.host = host.rstrip(".")
        self.port = port
        self._session = session
        self._base_url = URL.build(scheme="http", host=self.host, port=self.port)
        self._websocket: ClientWebSocketResponse | None = None
        self._request_id = 0
        self._pending: dict[int, tuple[str, asyncio.Future[dict[str, Any]]]] = {}
        self.status: SmartGrindDeviceStatus | None = None
        self.settings: SmartGrindSettings | None = None

    def _url(self, path: str) -> URL:
        return self._base_url.with_path(path)

    async def async_get_status(self) -> SmartGrindDeviceStatus:
        """Fetch device identity, version, and capabilities."""
        try:
            async with self._session.get(self._url("/api/v1/status")) as response:
                response.raise_for_status()
                payload = await response.json(content_type=None)
        except (TimeoutError, ClientError, json.JSONDecodeError) as exc:
            raise SmartGrindConnectionError(f"Cannot reach Smart Grind at {self.host}") from exc
        if not isinstance(payload, dict) or payload.get("api") != "v1":
            raise SmartGrindProtocolError("Device does not expose the Smart Grind v1 API")
        self.status = SmartGrindDeviceStatus.from_payload(payload)
        return self.status

    async def async_get_settings(self) -> SmartGrindSettings:
        """Fetch profile names, targets, and active mode."""
        try:
            async with self._session.get(self._url("/api/v1/settings")) as response:
                response.raise_for_status()
                payload = await response.json(content_type=None)
        except (TimeoutError, ClientError, json.JSONDecodeError) as exc:
            raise SmartGrindConnectionError(f"Cannot read settings from {self.host}") from exc
        if not isinstance(payload, dict) or payload.get("api") != "v1":
            raise SmartGrindProtocolError("Invalid Smart Grind settings response")
        self.settings = SmartGrindSettings.from_payload(payload)
        return self.settings

    async def async_connect(self) -> None:
        """Open the local push connection."""
        await self.async_disconnect()
        try:
            self._websocket = await self._session.ws_connect(
                self._url("/ws"), heartbeat=20, autoping=True, max_msg_size=4096
            )
        except (TimeoutError, ClientError) as exc:
            raise SmartGrindConnectionError(f"Cannot connect to {self.host}") from exc

    async def async_listen(self, callback: StateCallback) -> None:
        """Receive state and command acknowledgements until disconnected."""
        websocket = self._websocket
        if websocket is None:
            raise SmartGrindConnectionError("WebSocket is not connected")

        try:
            async for message in websocket:
                if message.type is WSMsgType.TEXT:
                    await self._async_process_message(message.data, callback)
                elif message.type in {WSMsgType.CLOSED, WSMsgType.CLOSE, WSMsgType.ERROR}:
                    break
        except (TimeoutError, ClientError) as exc:
            raise SmartGrindConnectionError("Smart Grind push connection failed") from exc
        finally:
            await self.async_disconnect()
        raise SmartGrindConnectionError("Smart Grind push connection closed")

    async def _async_process_message(self, raw: str, callback: StateCallback) -> None:
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise SmartGrindProtocolError("Smart Grind sent invalid JSON") from exc
        if not isinstance(payload, dict):
            raise SmartGrindProtocolError("Smart Grind sent a non-object message")

        message_type = payload.get("type")
        if message_type == "state":
            result = callback(SmartGrindState.from_payload(payload))
            if result is not None:
                await result
            return
        if message_type != "ack":
            return

        request_id = payload.get("rid")
        pending: tuple[str, asyncio.Future[dict[str, Any]]] | None = None
        if isinstance(request_id, int):
            pending = self._pending.get(request_id)
        else:
            action = payload.get("action")
            pending = next((item for item in self._pending.values() if item[0] == action), None)
        if pending is not None and not pending[1].done():
            pending[1].set_result(payload)

    async def async_command(self, action: str, **parameters: Any) -> None:
        """Send a command and wait for its correlated acknowledgement."""
        websocket = self._websocket
        if websocket is None or websocket.closed:
            raise SmartGrindConnectionError("Smart Grind is not connected")

        self._request_id = (self._request_id + 1) & 0xFFFFFFFF
        request_id = self._request_id
        future: asyncio.Future[dict[str, Any]] = asyncio.get_running_loop().create_future()
        self._pending[request_id] = (action, future)
        payload = {"type": "command", "action": action, "rid": request_id, **parameters}
        try:
            await websocket.send_json(
                payload,
                dumps=lambda value: json.dumps(value, separators=(",", ":")),
            )
            acknowledgement = await asyncio.wait_for(future, COMMAND_TIMEOUT_SECONDS)
        except (TimeoutError, ClientError) as exc:
            raise SmartGrindConnectionError(f"No acknowledgement for {action}") from exc
        finally:
            self._pending.pop(request_id, None)

        if not acknowledgement.get("accepted", False):
            raise SmartGrindCommandError(str(acknowledgement.get("reason", "Command rejected")))

    def supports(self, command: str) -> bool:
        """Return whether the device advertises a command."""
        return self.status is not None and command in self.status.commands

    async def async_select_profile(self, profile: int) -> None:
        """Select a profile, using the push protocol when available."""
        if self.supports("select_profile"):
            await self.async_command("select_profile", profile=profile)
        else:
            try:
                async with self._session.post(
                    self._url("/api/v1/profile"), data={"profile": str(profile)}
                ) as response:
                    response.raise_for_status()
            except (TimeoutError, ClientError) as exc:
                raise SmartGrindConnectionError("Could not select profile") from exc
        await self.async_get_settings()

    async def async_set_mode(self, mode: str) -> None:
        """Select weight or time mode."""
        if not self.supports("set_mode"):
            raise SmartGrindCommandError("This firmware does not support changing grind mode")
        await self.async_command("set_mode", mode=mode)
        await self.async_get_settings()

    async def async_disconnect(self) -> None:
        """Close the connection and fail outstanding commands."""
        websocket, self._websocket = self._websocket, None
        if websocket is not None and not websocket.closed:
            with contextlib.suppress(ClientError):
                await websocket.close()
        for _, future in self._pending.values():
            if not future.done():
                future.set_exception(SmartGrindConnectionError("Smart Grind disconnected"))
        self._pending.clear()
