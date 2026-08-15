"""Tests for correlated Smart Grind WebSocket commands."""

from __future__ import annotations

import asyncio
import json
from typing import Any

import pytest

from custom_components.smart_grind.client import SmartGrindClient
from custom_components.smart_grind.models import SmartGrindCommandError


class FakeWebSocket:
    """Minimal command-capable WebSocket test double."""

    def __init__(
        self, client: SmartGrindClient, accepted: bool = True, legacy: bool = False
    ) -> None:
        self.client = client
        self.accepted = accepted
        self.legacy = legacy
        self.closed = False
        self.sent: list[dict[str, Any]] = []

    async def send_json(self, payload: dict[str, Any], dumps) -> None:
        self.sent.append(payload)
        acknowledgement = {
            "api": "v1",
            "type": "ack",
            "action": payload["action"],
            "accepted": self.accepted,
            "reason": "accepted" if self.accepted else "grinder is not idle",
        }
        if not self.legacy:
            acknowledgement["rid"] = payload["rid"]
        asyncio.get_running_loop().call_soon(
            asyncio.create_task,
            self.client._async_process_message(json.dumps(acknowledgement), lambda state: None),
        )

    async def close(self) -> None:
        self.closed = True


@pytest.mark.parametrize("legacy", [False, True])
async def test_command_matches_acknowledgement(legacy: bool) -> None:
    client = SmartGrindClient("192.0.2.10", object())
    websocket = FakeWebSocket(client, legacy=legacy)
    client._websocket = websocket

    await client.async_command("tare")

    assert websocket.sent[0]["action"] == "tare"
    assert isinstance(websocket.sent[0]["rid"], int)


async def test_rejected_command_raises() -> None:
    client = SmartGrindClient("192.0.2.10", object())
    client._websocket = FakeWebSocket(client, accepted=False)

    with pytest.raises(SmartGrindCommandError, match="grinder is not idle"):
        await client.async_command("start")
