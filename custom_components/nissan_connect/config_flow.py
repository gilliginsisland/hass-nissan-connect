from typing import Any
from abc import ABC, abstractmethod

import voluptuous as vol

from homeassistant import config_entries, core, exceptions
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD
from homeassistant.data_entry_flow import (
    FlowHandler,
    FlowResult,
)

from .api.auth import Auth

from . import DOMAIN
from .const import CONF_VIN, CONF_TOKEN

DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_USERNAME): str,
    vol.Required(CONF_PASSWORD): str,
    vol.Required(CONF_VIN): str,
})


async def generate_token(
    hass: core.HomeAssistant, username: str, password: str
) -> dict[str, Any]:
    """Validate the user input allows us to connect."""

    auth = Auth()
    try:
        await hass.async_add_executor_job(
            auth.fetch_token, username, password
        )
    except Exception as ex:
        raise CannotConnect from ex

    return auth.token_storage.get().to_dict()


class BaseFlow(FlowHandler, ABC):
    """Represent the base config flow for NissanConnect."""

    @abstractmethod
    async def async_save_entry(self, data: dict[str, Any]) -> FlowResult:
        """Create or update the config_entry."""
        pass

    async def async_step_sign_in(
        self, user_input: dict[str, Any] | None
    ) -> FlowResult:
        """Update the config_entry."""

        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                token = await generate_token(
                    self.hass, user_input[CONF_USERNAME], user_input[CONF_PASSWORD]
                )
            except CannotConnect:
                errors["base"] = "cannot_connect"
            else:
                return await self.async_save_entry(
                    data={
                        CONF_VIN: user_input[CONF_VIN],
                        CONF_TOKEN: token,
                    },
                )
        return self.async_show_form(
            step_id="sign_in", data_schema=DATA_SCHEMA, errors=errors
        )


class ConfigFlow(BaseFlow, config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Nissan."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        return await self.async_step_sign_in(user_input)

    async def async_save_entry(
        self, data: dict[str, Any]
    ) -> FlowResult:
        """Create the config_entry."""
        await self.async_set_unique_id(data[CONF_VIN])
        self._abort_if_unique_id_configured()
        return self.async_create_entry(title=data[CONF_VIN], data=data)

    @staticmethod
    @core.callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlow(config_entry)


class OptionsFlow(BaseFlow, config_entries.OptionsFlowWithConfigEntry):
    """Handle an options flow for Nissan."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        return await self.async_step_sign_in(user_input)

    async def async_save_entry(
        self, data: dict[str, Any]
    ) -> FlowResult:
        """Update the config_entry."""
        self.hass.config_entries.async_update_entry(
            self.config_entry, data=data,
        )
        return self.async_create_entry(title="", data={})


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""
