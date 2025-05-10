"""Config flow to configure the integration."""

from __future__ import annotations

import asyncio
from types import MappingProxyType
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
    DEFAULT_DISCOVERY_UNIQUE_ID,
)
from homeassistant.const import (
    CONF_NAME,
)
from homeassistant.components import usb
from homeassistant.core import HomeAssistant, callback

import co2meter as co2
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.service_info.usb import UsbServiceInfo

from .const import DOMAIN, LOGGER


@callback
def async_get_schema(
    defaults: dict[str, Any] | MappingProxyType[str, Any],
) -> vol.Schema:
    """Return the schema."""
    schema = {
        vol.Optional(
            CONF_NAME,
            description={"suggested_value": defaults.get(CONF_NAME)},
        ): str,
    }

    return vol.Schema(schema)


async def async_validate_input(
    hass: HomeAssistant, user_input: dict[str, Any]
) -> tuple[dict[str, str], str]:
    """Manage options."""
    errors = {}
    field = "base"

    dev = co2.CO2monitor(bypass_decrypt=True)
    if not dev:
        errors[field] = "cannot_connect"
        return errors, ''

    return errors, f'{dev.info["product_name"]}_{dev.info["serial_no"].replace(".", "_")}'


class USBCo2FlowHandler(ConfigFlow, domain=DOMAIN):
    """Config flow for USB Co2."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> OptionsFlow:
        """Get the options flow for this handler."""
        return UsbCo2OptionsFlowHandler()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initialized by the user."""
        errors: dict[str, str] = {}

        # if not usb.async_is_plugged_in(
        #     self.hass, {"vid": "04D9", "pid": "A052"}
        # ):
        #     raise ConfigEntryNotReady("The USB device is missing")

        if user_input is not None:
            errors, dev_id = await async_validate_input(self.hass, user_input)
            if not errors:

                # Storing data in option, to allow for changing them later
                # using an options flow.
                await self.async_set_unique_id(dev_id, raise_on_progress=False)
                return self.async_create_entry(
                    title=user_input.get(CONF_NAME) or dev_id,
                    data={},
                    options={
                        CONF_NAME: user_input.get(CONF_NAME),
                    },
                )
        else:
            user_input = {
            }

        return self.async_show_form(
            step_id="user",
            data_schema=async_get_schema(user_input),
            errors=errors,
        )

    async def async_step_usb(self, discovery_info: UsbServiceInfo) -> ConfigFlowResult:
        """Handle USB discovery."""
        self._device_path = discovery_info.device
        self._device_name = usb.human_readable_device_name(
            discovery_info.device,
            discovery_info.serial_number,
            discovery_info.manufacturer,
            discovery_info.description,
            discovery_info.vid,
            discovery_info.pid,
        )
        self._set_confirm_only()
        self.context["title_placeholders"] = {
            CONF_NAME: f"USB CO2 {self._device_name}"
        }
        await self.async_set_unique_id(DEFAULT_DISCOVERY_UNIQUE_ID)
        return self.async_show_form(
            step_id="usb_config",
            data_schema=async_get_schema(self.config_entry.options),
        )

        return self.async_show_form(
            step_id="usb_config",
            data_schema=vol.Schema(
                {vol.Optional(CONF_NAME): vol.In(ports_as_string)}
            ),
        )


class UsbCo2OptionsFlowHandler(OptionsFlow):
    """Handle options."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            errors, dev_id = await async_validate_input(self.hass, user_input)
            if not errors:
                for entry in self.hass.config_entries.async_entries(DOMAIN):
                    if (
                        entry.entry_id != self.config_entry.entry_id
                        and entry.options[CONF_NAME] == user_input[CONF_NAME]
                    ):
                        errors = {CONF_NAME: "already_configured"}

                if not errors:
                    return self.async_create_entry(
                        title=user_input.get(CONF_NAME),
                        data={},
                        options={
                            CONF_NAME: user_input.get(CONF_NAME),
                        },
                    )
        else:
            user_input = {}

        return self.async_show_form(
            step_id="init",
            data_schema=async_get_schema(user_input or self.config_entry.options),
            errors=errors,
        )
