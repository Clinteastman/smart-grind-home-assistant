"""Control buttons for Smart Grind by Weight."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity
from homeassistant.exceptions import HomeAssistantError

from . import SmartGrindConfigEntry
from .coordinator import SmartGrindCoordinator
from .entity import SmartGrindEntity
from .models import SmartGrindError


@dataclass(frozen=True, slots=True)
class SmartGrindButtonDefinition:
    key: str
    action: str
    requires_capability: bool = False


BUTTONS = (
    SmartGrindButtonDefinition("start", "start"),
    SmartGrindButtonDefinition("start_manual", "start_manual", True),
    SmartGrindButtonDefinition("stop", "stop"),
    SmartGrindButtonDefinition("tare", "tare", True),
    SmartGrindButtonDefinition("dismiss", "dismiss"),
)


async def async_setup_entry(hass, entry: SmartGrindConfigEntry, async_add_entities) -> None:
    """Set up supported Smart Grind buttons."""
    coordinator = entry.runtime_data
    async_add_entities(
        SmartGrindButton(coordinator, definition)
        for definition in BUTTONS
        if not definition.requires_capability or coordinator.client.supports(definition.action)
    )


class SmartGrindButton(SmartGrindEntity, ButtonEntity):
    """A safe controller-backed grinder command."""

    def __init__(
        self, coordinator: SmartGrindCoordinator, definition: SmartGrindButtonDefinition
    ) -> None:
        super().__init__(coordinator, definition.key)
        self._definition = definition
        self._attr_translation_key = definition.key

    @property
    def available(self) -> bool:
        """Only offer commands that make sense in the current phase."""
        if not super().available or self.coordinator.data is None:
            return False
        state = self.coordinator.data
        if self._definition.action in {"start", "start_manual", "tare"}:
            return state.phase == "idle"
        if self._definition.action == "stop":
            return state.active
        if self._definition.action == "dismiss":
            return state.phase in {"completed", "timeout"}
        return True

    async def async_press(self) -> None:
        """Send the command through the firmware safety controller."""
        try:
            await self.coordinator.async_command(self._definition.action)
        except SmartGrindError as exc:
            raise HomeAssistantError(str(exc)) from exc
