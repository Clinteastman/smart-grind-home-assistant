"""Opt-in, read-only acceptance test against a physical Smart Grind device."""

from __future__ import annotations

import asyncio
import os

import pytest
import pytest_socket
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.smart_grind.const import CONF_DEVICE_ID, DOMAIN

LIVE_HOST = os.environ.get("SMART_GRIND_LIVE_HOST")
LIVE_DEVICE_ID = os.environ.get("SMART_GRIND_LIVE_DEVICE_ID", "684a8d858428")

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(not LIVE_HOST, reason="SMART_GRIND_LIVE_HOST is not set"),
]


async def test_live_grinder_loads_and_publishes_state(
    hass: HomeAssistant, socket_enabled: None
) -> None:
    """Load the integration and receive state without issuing a command."""
    pytest_socket.socket_allow_hosts(["127.0.0.1", LIVE_HOST], allow_unix_socket=True)
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Smart Grind by Weight",
        unique_id=LIVE_DEVICE_ID,
        data={
            CONF_HOST: LIVE_HOST,
            CONF_PORT: 80,
            CONF_DEVICE_ID: LIVE_DEVICE_ID,
        },
    )
    entry.add_to_hass(hass)

    async with asyncio.timeout(20):
        assert await hass.config_entries.async_setup(entry.entry_id)

    coordinator = entry.runtime_data
    assert coordinator.client.status is not None
    assert coordinator.client.status.device_id == LIVE_DEVICE_ID.replace(":", "")
    assert coordinator.data is not None
    assert coordinator.data.phase in {"idle", "grinding", "stopping", "completed", "timeout"}

    registry = er.async_get(hass)
    entity_ids = {
        entity.entity_id
        for entity in registry.entities.values()
        if entity.config_entry_id == entry.entry_id
    }
    assert any(
        entity_id.startswith("sensor.smart_grind_by_weight_weight") for entity_id in entity_ids
    )
    assert any(
        entity_id.startswith("binary_sensor.smart_grind_by_weight_grinding")
        for entity_id in entity_ids
    )
    assert any(
        entity_id.startswith("select.smart_grind_by_weight_profile") for entity_id in entity_ids
    )

    assert await hass.config_entries.async_unload(entry.entry_id)
