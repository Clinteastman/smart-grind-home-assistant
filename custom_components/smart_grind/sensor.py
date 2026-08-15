"""Sensors for Smart Grind by Weight."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.const import PERCENTAGE, UnitOfInformation, UnitOfMass, UnitOfTime
from homeassistant.helpers.entity import EntityCategory

from . import SmartGrindConfigEntry
from .coordinator import SmartGrindCoordinator
from .entity import SmartGrindEntity
from .models import SmartGrindState


@dataclass(frozen=True, slots=True)
class SmartGrindSensorDefinition:
    """Describe one state-derived sensor."""

    key: str
    value: Callable[[SmartGrindState], float | int | str]
    unit: str | None = None
    device_class: SensorDeviceClass | None = None
    state_class: SensorStateClass | None = None
    category: EntityCategory | None = None
    enabled: bool = True
    precision: int | None = None


SENSORS = (
    SmartGrindSensorDefinition(
        "weight",
        lambda state: state.weight,
        UnitOfMass.GRAMS,
        SensorDeviceClass.WEIGHT,
        SensorStateClass.MEASUREMENT,
        precision=2,
    ),
    SmartGrindSensorDefinition(
        "flow",
        lambda state: state.flow,
        "g/s",
        state_class=SensorStateClass.MEASUREMENT,
        precision=2,
    ),
    SmartGrindSensorDefinition(
        "progress",
        lambda state: state.progress,
        PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SmartGrindSensorDefinition(
        "phase",
        lambda state: state.phase,
        device_class=SensorDeviceClass.ENUM,
    ),
    SmartGrindSensorDefinition(
        "target_weight",
        lambda state: state.target_weight,
        UnitOfMass.GRAMS,
        SensorDeviceClass.WEIGHT,
        precision=1,
    ),
    SmartGrindSensorDefinition(
        "target_time",
        lambda state: state.target_time_ms / 1000,
        UnitOfTime.SECONDS,
        SensorDeviceClass.DURATION,
        precision=1,
    ),
    SmartGrindSensorDefinition(
        "free_heap",
        lambda state: state.free_heap,
        UnitOfInformation.BYTES,
        SensorDeviceClass.DATA_SIZE,
        SensorStateClass.MEASUREMENT,
        EntityCategory.DIAGNOSTIC,
        enabled=False,
    ),
)


async def async_setup_entry(hass, entry: SmartGrindConfigEntry, async_add_entities) -> None:
    """Set up Smart Grind sensors."""
    async_add_entities(SmartGrindSensor(entry.runtime_data, definition) for definition in SENSORS)


class SmartGrindSensor(SmartGrindEntity, SensorEntity):
    """A live Smart Grind sensor."""

    def __init__(
        self, coordinator: SmartGrindCoordinator, definition: SmartGrindSensorDefinition
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, definition.key)
        self._definition = definition
        self._attr_translation_key = definition.key
        self._attr_native_unit_of_measurement = definition.unit
        self._attr_device_class = definition.device_class
        self._attr_state_class = definition.state_class
        self._attr_entity_category = definition.category
        self._attr_entity_registry_enabled_default = definition.enabled
        self._attr_suggested_display_precision = definition.precision
        if definition.device_class is SensorDeviceClass.ENUM:
            self._attr_options = [
                "idle",
                "preparing",
                "priming",
                "grinding",
                "paused",
                "coasting",
                "final_settling",
                "completed",
                "timeout",
            ]

    @property
    def native_value(self) -> float | int | str | None:
        """Return the latest pushed value."""
        return self._definition.value(self.coordinator.data) if self.coordinator.data else None
