"""Tests for loading Smart Grind in Home Assistant."""

from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.smart_grind.const import CONF_DEVICE_ID, DOMAIN


async def test_setup_creates_device_entities(hass: HomeAssistant, mock_coordinator_start) -> None:
    """A config entry creates the complete initial entity set."""
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
    await hass.async_block_till_done()

    registry = er.async_get(hass)
    entries = [
        item for item in registry.entities.values() if item.config_entry_id == entry.entry_id
    ]
    assert len(entries) == 16
    assert {item.unique_id for item in entries} >= {
        "684a8d858428_weight",
        "684a8d858428_phase",
        "684a8d858428_grinding",
        "684a8d858428_start",
        "684a8d858428_start_manual",
        "684a8d858428_profile",
        "684a8d858428_grind_mode",
    }
