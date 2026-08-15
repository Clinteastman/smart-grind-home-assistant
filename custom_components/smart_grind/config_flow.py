"""Config flow for Smart Grind by Weight."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import format_mac
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from .client import SmartGrindClient
from .const import CONF_DEVICE_ID, DEFAULT_NAME, DEFAULT_PORT, DOMAIN
from .models import SmartGrindConnectionError, SmartGrindProtocolError

_LOGGER = logging.getLogger(__name__)


class SmartGrindConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle UI and mDNS setup."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the flow."""
        self._discovered_host: str | None = None
        self._discovered_port = DEFAULT_PORT

    async def _async_probe(self, host: str, port: int) -> tuple[str, str]:
        client = SmartGrindClient(host, async_get_clientsession(self.hass), port)
        status = await client.async_get_status()
        return format_mac(status.device_id), status.model

    async def async_step_zeroconf(self, discovery_info: ZeroconfServiceInfo) -> ConfigFlowResult:
        """Handle a discovered grinder."""
        host = discovery_info.host
        port = discovery_info.port or DEFAULT_PORT
        try:
            device_id, model = await self._async_probe(host, port)
        except SmartGrindConnectionError, SmartGrindProtocolError:
            return self.async_abort(reason="cannot_connect")

        await self.async_set_unique_id(device_id)
        self._abort_if_unique_id_configured(updates={CONF_HOST: host, CONF_PORT: port})
        self._discovered_host = host
        self._discovered_port = port
        self.context["title_placeholders"] = {"name": f"{DEFAULT_NAME} {device_id[-5:]}"}
        return await self.async_step_confirm(
            description_placeholders={"model": model, "host": host}
        )

    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm a discovered grinder."""
        if user_input is not None:
            return self.async_create_entry(
                title=DEFAULT_NAME,
                data={
                    CONF_HOST: self._discovered_host,
                    CONF_PORT: self._discovered_port,
                    CONF_DEVICE_ID: self.unique_id,
                },
            )
        return self.async_show_form(step_id="confirm")

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle manual setup by hostname or IP address."""
        errors: dict[str, str] = {}
        if user_input is not None:
            host = str(user_input[CONF_HOST]).strip().rstrip(".")
            try:
                device_id, _ = await self._async_probe(host, DEFAULT_PORT)
            except SmartGrindConnectionError:
                errors["base"] = "cannot_connect"
            except SmartGrindProtocolError:
                errors["base"] = "invalid_device"
            except Exception:  # Home Assistant displays a safe generic error.
                _LOGGER.exception("Unexpected error validating Smart Grind at %s", host)
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(device_id)
                self._abort_if_unique_id_configured(
                    updates={CONF_HOST: host, CONF_PORT: DEFAULT_PORT}
                )
                return self.async_create_entry(
                    title=DEFAULT_NAME,
                    data={
                        CONF_HOST: host,
                        CONF_PORT: DEFAULT_PORT,
                        CONF_DEVICE_ID: device_id,
                    },
                )

        schema = vol.Schema({vol.Required(CONF_HOST): str})
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Update the network address while preserving device identity."""
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            host = str(user_input[CONF_HOST]).strip().rstrip(".")
            try:
                device_id, _ = await self._async_probe(host, DEFAULT_PORT)
            except SmartGrindConnectionError:
                errors["base"] = "cannot_connect"
            except SmartGrindProtocolError:
                errors["base"] = "invalid_device"
            except Exception:
                _LOGGER.exception("Unexpected error reconfiguring Smart Grind at %s", host)
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(device_id)
                self._abort_if_unique_id_mismatch()
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates={
                        CONF_HOST: host,
                        CONF_PORT: DEFAULT_PORT,
                        CONF_DEVICE_ID: device_id,
                    },
                )

        schema = vol.Schema({vol.Required(CONF_HOST, default=entry.data[CONF_HOST]): str})
        return self.async_show_form(step_id="reconfigure", data_schema=schema, errors=errors)
