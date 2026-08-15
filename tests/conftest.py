"""Shared Home Assistant fixtures for Smart Grind tests."""

from collections.abc import AsyncGenerator

import pytest

from custom_components.smart_grind.coordinator import SmartGrindCoordinator
from custom_components.smart_grind.models import (
    SmartGrindDeviceStatus,
    SmartGrindProfile,
    SmartGrindSettings,
    SmartGrindState,
)

pytest_plugins = "pytest_homeassistant_custom_component"

DEVICE_STATUS = SmartGrindDeviceStatus(
    device_id="684a8d858428",
    model="ESP32-S3-Touch-AMOLED-1.64",
    hardware_revision="v2",
    firmware_version="1.5.3",
    firmware_build=7,
    firmware_commit="abc123",
    hostname="smartgrind",
    ip_address="192.0.2.10",
    protocol=1,
    commands=frozenset(
        {
            "start",
            "start_manual",
            "stop",
            "dismiss",
            "tare",
            "select_profile",
            "set_mode",
        }
    ),
)

SETTINGS = SmartGrindSettings(
    current_profile=1,
    grind_mode="weight",
    profiles=(
        SmartGrindProfile(0, "Single", 9.0, 5.0),
        SmartGrindProfile(1, "Double", 18.0, 10.0),
        SmartGrindProfile(2, "Custom", 21.5, 12.0),
    ),
)

LIVE_STATE = SmartGrindState(
    sequence=1,
    timestamp_ms=1000,
    active=False,
    phase="idle",
    grind_mode="weight",
    profile=1,
    progress=0,
    target_weight=18.0,
    target_time_ms=10000,
    weight=0.0,
    flow=0.0,
    motor_running=False,
    free_heap=109188,
)


@pytest.fixture(autouse=True)
async def automatically_enable_custom_integrations(
    enable_custom_integrations: None,
) -> AsyncGenerator[None]:
    """Allow Home Assistant to load the custom component under test."""
    yield


@pytest.fixture
def mock_coordinator_start(monkeypatch: pytest.MonkeyPatch):
    """Set coordinator data without opening a network socket."""

    async def async_start(coordinator: SmartGrindCoordinator) -> None:
        coordinator.client.status = DEVICE_STATUS
        coordinator.client.settings = SETTINGS
        coordinator.async_set_updated_data(LIVE_STATE)

    monkeypatch.setattr(SmartGrindCoordinator, "async_start", async_start)
