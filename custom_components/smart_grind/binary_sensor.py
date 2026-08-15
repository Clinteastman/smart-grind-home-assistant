"""Binary sensors for Smart Grind by Weight."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity

from . import SmartGrindConfigEntry
from .coordinator import SmartGrindCoordinator
from .entity import SmartGrindEntity
from .models import SmartGrindState


@dataclass(frozen=True, slots=True)
class SmartGrindBinarySensorDefinition:
    key: str
    value: Callable[[SmartGrindState], bool]


BINARY_SENSORS = (
    SmartGrindBinarySensorDefinition("grinding", lambda state: state.active),
    SmartGrindBinarySensorDefinition("motor", lambda state: state.motor_running),
)


async def async_setup_entry(hass, entry: SmartGrindConfigEntry, async_add_entities) -> None:
    """Set up Smart Grind binary sensors."""
    async_add_entities(
        SmartGrindBinarySensor(entry.runtime_data, definition) for definition in BINARY_SENSORS
    )


class SmartGrindBinarySensor(SmartGrindEntity, BinarySensorEntity):
    """A live Smart Grind binary sensor."""

    _attr_device_class = BinarySensorDeviceClass.RUNNING

    def __init__(
        self,
        coordinator: SmartGrindCoordinator,
        definition: SmartGrindBinarySensorDefinition,
    ) -> None:
        super().__init__(coordinator, definition.key)
        self._definition = definition
        self._attr_translation_key = definition.key

    @property
    def is_on(self) -> bool | None:
        """Return the latest pushed state."""
        return self._definition.value(self.coordinator.data) if self.coordinator.data else None
