"""Shared entity support for Smart Grind by Weight."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEFAULT_NAME, DOMAIN
from .coordinator import SmartGrindCoordinator


class SmartGrindEntity(CoordinatorEntity[SmartGrindCoordinator]):
    """Base entity tied to one Smart Grind device."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: SmartGrindCoordinator, key: str) -> None:
        """Initialize common identity and device metadata."""
        super().__init__(coordinator)
        status = coordinator.client.status
        if status is None:
            raise RuntimeError("Smart Grind status is not loaded")
        self._attr_unique_id = f"{status.device_id}_{key}"
        self._attr_device_info = DeviceInfo(
            configuration_url=f"http://{coordinator.client.host}/",
            hw_version=status.hardware_revision.upper(),
            identifiers={(DOMAIN, status.device_id)},
            manufacturer="Smart Grind by Weight community",
            model=status.model,
            name=DEFAULT_NAME,
            sw_version=status.firmware_version,
        )
