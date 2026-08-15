"""Opt-in acceptance test against a physical Smart Grind device."""

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
from custom_components.smart_grind.models import SmartGrindCommandError

LIVE_HOST = os.environ.get("SMART_GRIND_LIVE_HOST")
LIVE_DEVICE_ID = os.environ.get("SMART_GRIND_LIVE_DEVICE_ID", "684a8d858428")
LIVE_COMMAND_TEST = os.environ.get("SMART_GRIND_LIVE_COMMAND_TEST") == "1"

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
    status = coordinator.client.status
    assert status is not None
    assert status.device_id == LIVE_DEVICE_ID.replace(":", "")
    assert status.protocol == 1
    assert status.commands >= {
        "start",
        "start_manual",
        "stop",
        "dismiss",
        "tare",
        "select_profile",
        "set_mode",
    }
    assert coordinator.data is not None
    assert coordinator.data.phase in {"idle", "grinding", "stopping", "completed", "timeout"}

    registry = er.async_get(hass)
    entity_ids = {
        entity.entity_id
        for entity in registry.entities.values()
        if entity.config_entry_id == entry.entry_id
    }
    assert len(entity_ids) == 16
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

    if LIVE_COMMAND_TEST:
        assert coordinator.data.phase == "idle"
        assert coordinator.data.motor_running is False
        settings = coordinator.client.settings
        assert settings is not None
        original_profile = settings.current_profile
        original_mode = settings.grind_mode

        # Exercise accepted controller-backed commands without changing the
        # user's effective configuration or starting the motor.
        await coordinator.async_select_profile(original_profile)
        await coordinator.async_set_mode(original_mode)
        refreshed = await coordinator.client.async_get_settings()
        assert refreshed.current_profile == original_profile
        assert refreshed.grind_mode == original_mode

        with pytest.raises(SmartGrindCommandError, match="grinder is not active"):
            await coordinator.async_command("stop")
        with pytest.raises(SmartGrindCommandError, match="nothing to dismiss"):
            await coordinator.async_command("dismiss")

    assert await hass.config_entries.async_unload(entry.entry_id)
