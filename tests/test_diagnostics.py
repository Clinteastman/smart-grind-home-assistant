"""Tests for Smart Grind diagnostics."""

from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.smart_grind.const import CONF_DEVICE_ID, DOMAIN
from custom_components.smart_grind.diagnostics import async_get_config_entry_diagnostics


async def test_diagnostics_redact_network_identity(
    hass: HomeAssistant, mock_coordinator_start
) -> None:
    """Diagnostics retain useful state but redact local identifiers."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Smart Grind by Weight",
        unique_id="68:4a:8d:85:84:28",
        data={
            CONF_HOST: "192.0.2.10",
            CONF_PORT: 80,
            CONF_DEVICE_ID: "68:4a:8d:85:84:28",
        },
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)

    assert diagnostics["config_entry"][CONF_HOST] != "192.0.2.10"
    assert diagnostics["config_entry"][CONF_DEVICE_ID] != "68:4a:8d:85:84:28"
    assert diagnostics["status"]["device_id"] != "684a8d858428"
    assert diagnostics["status"]["ip_address"] != "192.0.2.10"
    assert diagnostics["status"]["firmware_version"] == "1.5.3"
    assert diagnostics["status"]["commands"] == [
        "dismiss",
        "select_profile",
        "set_mode",
        "start",
        "start_manual",
        "stop",
        "tare",
    ]
    assert diagnostics["state"]["phase"] == "idle"
