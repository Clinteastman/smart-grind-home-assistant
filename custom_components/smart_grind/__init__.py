"""Smart Grind by Weight integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .client import SmartGrindClient
from .const import DEFAULT_PORT, PLATFORMS
from .coordinator import SmartGrindCoordinator

SmartGrindConfigEntry = ConfigEntry[SmartGrindCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: SmartGrindConfigEntry) -> bool:
    """Set up Smart Grind from a config entry."""
    client = SmartGrindClient(
        entry.data[CONF_HOST],
        async_get_clientsession(hass),
        entry.data.get(CONF_PORT, DEFAULT_PORT),
    )
    coordinator = SmartGrindCoordinator(hass, client)
    await coordinator.async_start()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: SmartGrindConfigEntry) -> bool:
    """Unload a Smart Grind config entry."""
    if not await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        return False
    await entry.runtime_data.async_shutdown()
    return True
