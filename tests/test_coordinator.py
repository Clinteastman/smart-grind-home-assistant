"""Tests for resilient Smart Grind coordinator availability."""

from unittest.mock import Mock, patch

from homeassistant.core import HomeAssistant

from custom_components.smart_grind.const import WS_UNAVAILABLE_GRACE_SECONDS
from custom_components.smart_grind.coordinator import SmartGrindCoordinator
from custom_components.smart_grind.models import SmartGrindConnectionError

from .conftest import LIVE_STATE


async def test_brief_disconnect_keeps_last_state_available(hass: HomeAssistant) -> None:
    """A reconnect inside the grace period must not flicker every entity."""
    coordinator = SmartGrindCoordinator(hass, Mock())
    coordinator.async_set_updated_data(LIVE_STATE)

    with patch("custom_components.smart_grind.coordinator.monotonic", return_value=100.0):
        coordinator._handle_connection_error(SmartGrindConnectionError("closed"))

    assert coordinator.last_update_success
    assert coordinator.data == LIVE_STATE


async def test_sustained_disconnect_becomes_unavailable(hass: HomeAssistant) -> None:
    """A real outage must still mark coordinator entities unavailable."""
    coordinator = SmartGrindCoordinator(hass, Mock())
    coordinator.async_set_updated_data(LIVE_STATE)
    coordinator._disconnect_started = 100.0

    with patch(
        "custom_components.smart_grind.coordinator.monotonic",
        return_value=100.0 + WS_UNAVAILABLE_GRACE_SECONDS,
    ):
        coordinator._handle_connection_error(SmartGrindConnectionError("closed"))

    assert not coordinator.last_update_success
    assert coordinator.data == LIVE_STATE


async def test_new_state_clears_disconnect_grace(hass: HomeAssistant) -> None:
    """A recovered push update resets the outage timer and coordinator error."""
    coordinator = SmartGrindCoordinator(hass, Mock())
    coordinator.async_set_updated_data(LIVE_STATE)
    coordinator._disconnect_started = 100.0
    coordinator.async_set_update_error(SmartGrindConnectionError("closed"))

    await coordinator._async_receive_state(LIVE_STATE)

    assert coordinator._disconnect_started is None
    assert coordinator.last_update_success
