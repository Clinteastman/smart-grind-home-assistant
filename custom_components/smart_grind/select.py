"""Profile and mode selects for Smart Grind by Weight."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.exceptions import HomeAssistantError

from . import SmartGrindConfigEntry
from .coordinator import SmartGrindCoordinator
from .entity import SmartGrindEntity
from .models import SmartGrindError


async def async_setup_entry(hass, entry: SmartGrindConfigEntry, async_add_entities) -> None:
    """Set up profile and supported mode selection."""
    coordinator = entry.runtime_data
    entities: list[SelectEntity] = [SmartGrindProfileSelect(coordinator)]
    if coordinator.client.supports("set_mode"):
        entities.append(SmartGrindModeSelect(coordinator))
    async_add_entities(entities)


class SmartGrindProfileSelect(SmartGrindEntity, SelectEntity):
    """Select the active dose profile."""

    _attr_translation_key = "profile"

    def __init__(self, coordinator: SmartGrindCoordinator) -> None:
        super().__init__(coordinator, "profile")

    @property
    def options(self) -> list[str]:
        settings = self.coordinator.client.settings
        return [profile.name for profile in settings.profiles] if settings else []

    @property
    def current_option(self) -> str | None:
        settings = self.coordinator.client.settings
        if settings is None or self.coordinator.data is None:
            return None
        profile_id = self.coordinator.data.profile
        return next(
            (profile.name for profile in settings.profiles if profile.profile_id == profile_id),
            None,
        )

    async def async_select_option(self, option: str) -> None:
        settings = self.coordinator.client.settings
        profile = (
            next((profile for profile in settings.profiles if profile.name == option), None)
            if settings
            else None
        )
        if profile is None:
            raise HomeAssistantError(f"Unknown Smart Grind profile: {option}")
        try:
            await self.coordinator.async_select_profile(profile.profile_id)
        except SmartGrindError as exc:
            raise HomeAssistantError(str(exc)) from exc


class SmartGrindModeSelect(SmartGrindEntity, SelectEntity):
    """Select weight or time dosing."""

    _attr_translation_key = "grind_mode"
    _attr_options = ["Weight", "Time"]

    def __init__(self, coordinator: SmartGrindCoordinator) -> None:
        super().__init__(coordinator, "grind_mode")

    @property
    def current_option(self) -> str | None:
        settings = self.coordinator.client.settings
        return settings.grind_mode.title() if settings else None

    async def async_select_option(self, option: str) -> None:
        mode = option.lower()
        if mode not in {"weight", "time"}:
            raise HomeAssistantError(f"Unknown grind mode: {option}")
        try:
            await self.coordinator.async_set_mode(mode)
        except SmartGrindError as exc:
            raise HomeAssistantError(str(exc)) from exc
