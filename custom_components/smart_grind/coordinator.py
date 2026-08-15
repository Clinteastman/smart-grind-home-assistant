"""Local-push coordinator for Smart Grind by Weight."""

from __future__ import annotations

import asyncio
import contextlib
import logging
from time import monotonic

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import SmartGrindClient
from .const import DOMAIN, WS_RECONNECT_MAX_SECONDS, WS_RECONNECT_MIN_SECONDS
from .models import SmartGrindError, SmartGrindState

_LOGGER = logging.getLogger(__name__)


class SmartGrindCoordinator(DataUpdateCoordinator[SmartGrindState]):
    """Keep a resilient push connection to one grinder."""

    def __init__(self, hass: HomeAssistant, client: SmartGrindClient) -> None:
        """Initialize the coordinator."""
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=None, always_update=False)
        self.client = client
        self._listener_task: asyncio.Task[None] | None = None
        self._first_state = asyncio.Event()
        self._last_publish = 0.0
        self._last_semantic_state: tuple[object, ...] | None = None

    async def async_start(self) -> None:
        """Validate the device and start its reconnecting listener."""
        await self.client.async_get_status()
        await self.client.async_get_settings()
        self._listener_task = self.hass.async_create_background_task(
            self._async_listen_forever(), f"{DOMAIN}_websocket"
        )
        try:
            await asyncio.wait_for(self._first_state.wait(), timeout=8)
        except TimeoutError as exc:
            await self.async_shutdown()
            raise UpdateFailed("Timed out waiting for the first grinder state") from exc

    async def _async_listen_forever(self) -> None:
        delay = WS_RECONNECT_MIN_SECONDS
        while True:
            try:
                await self.client.async_connect()
                await self.client.async_get_status()
                await self.client.async_get_settings()
                delay = WS_RECONNECT_MIN_SECONDS
                await self.client.async_listen(self._async_receive_state)
            except asyncio.CancelledError:
                raise
            except SmartGrindError as exc:
                self.async_set_update_error(UpdateFailed(str(exc)))
                await asyncio.sleep(delay)
                delay = min(delay * 2, WS_RECONNECT_MAX_SECONDS)

    async def _async_receive_state(self, state: SmartGrindState) -> None:
        """Publish push data at a recorder-friendly rate and on semantic changes."""
        now = monotonic()
        semantic_state = (
            state.active,
            state.phase,
            state.grind_mode,
            state.profile,
            state.motor_running,
            state.target_weight,
            state.target_time_ms,
        )
        interval = 0.25 if state.active else 2.0
        if (
            self.data is None
            or semantic_state != self._last_semantic_state
            or now - self._last_publish >= interval
        ):
            self._last_publish = now
            self._last_semantic_state = semantic_state
            self.async_set_updated_data(state)
        self._first_state.set()

    async def async_command(self, action: str) -> None:
        """Send a device command."""
        await self.client.async_command(action)

    async def async_select_profile(self, profile: int) -> None:
        """Change the active dose profile."""
        await self.client.async_select_profile(profile)

    async def async_set_mode(self, mode: str) -> None:
        """Change weight/time mode."""
        await self.client.async_set_mode(mode)

    async def async_shutdown(self) -> None:
        """Stop background work and close the socket."""
        if self._listener_task is not None:
            self._listener_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._listener_task
            self._listener_task = None
        await self.client.async_disconnect()
