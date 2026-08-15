"""Privacy-safe diagnostics for Smart Grind by Weight."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant

from . import SmartGrindConfigEntry
from .const import CONF_DEVICE_ID

TO_REDACT = {CONF_HOST, CONF_DEVICE_ID, "device_id", "ip_address"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: SmartGrindConfigEntry
) -> dict[str, Any]:
    """Return useful protocol state without local network identifiers."""
    coordinator = entry.runtime_data
    status = coordinator.client.status
    settings = coordinator.client.settings

    status_data = None
    if status is not None:
        status_data = asdict(status)
        status_data["commands"] = sorted(status.commands)
        status_data = async_redact_data(status_data, TO_REDACT)

    settings_data = asdict(settings) if settings is not None else None
    state_data = asdict(coordinator.data) if coordinator.data is not None else None
    return {
        "config_entry": async_redact_data(dict(entry.data), TO_REDACT),
        "status": status_data,
        "settings": settings_data,
        "state": state_data,
        "last_update_success": coordinator.last_update_success,
    }
