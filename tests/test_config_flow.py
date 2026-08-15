"""Tests for Smart Grind UI setup."""

from unittest.mock import AsyncMock, patch

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.smart_grind.config_flow import SmartGrindConfigFlow
from custom_components.smart_grind.const import CONF_DEVICE_ID, DOMAIN


async def test_user_flow(hass: HomeAssistant, mock_coordinator_start) -> None:
    """Manual setup probes the device and stores its stable hardware ID."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM

    with patch.object(
        SmartGrindConfigFlow,
        "_async_probe",
        AsyncMock(return_value=("68:4a:8d:85:84:28", "ESP32-S3-Touch-AMOLED-1.64")),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_HOST: "192.0.2.10"}
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        CONF_HOST: "192.0.2.10",
        CONF_PORT: 80,
        CONF_DEVICE_ID: "68:4a:8d:85:84:28",
    }
    assert result["result"].unique_id == "68:4a:8d:85:84:28"
