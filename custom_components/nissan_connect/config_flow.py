from typing import Any

import voluptuous as vol

from homeassistant import config_entries, core, exceptions
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD
from homeassistant.data_entry_flow import FlowResult

from .api.auth import Auth

from . import DOMAIN
from .const import CONF_VIN, CONF_TOKEN

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Required(CONF_VIN): str,
    }
)


async def validate_input(
    hass: core.HomeAssistant, data: dict[str, Any]
) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from DATA_SCHEMA with values provided by the user.
    """
    auth = Auth()
    try:
        await hass.async_add_executor_job(
            auth.fetch_tokens,
            data[CONF_USERNAME],
            data[CONF_PASSWORD],
        )
    except Exception as ex:
        raise CannotConnect from ex

    return auth.token.to_dict()


class NissanConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Nissan."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            unique_id = user_input[CONF_VIN]

            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            token = None
            try:
                token = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"

            if token:
                return self.async_create_entry(
                    title=user_input[CONF_VIN],
                    data={
                        CONF_VIN: user_input[CONF_VIN],
                        CONF_TOKEN: token,
                    },
                )

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""
