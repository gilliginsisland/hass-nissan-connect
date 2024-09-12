from typing import Any, Mapping

import voluptuous as vol

from homeassistant import config_entries, core, exceptions
from homeassistant.const import (
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_PIN,
)

from .api.auth import TokenAuth

from . import DOMAIN
from .const import CONF_VIN, CONF_TOKEN

USER_SCHEMA = vol.Schema({
    vol.Required(CONF_USERNAME): str,
    vol.Required(CONF_PASSWORD): str,
})

VEHICLE_SCHEMA = vol.Schema({
    vol.Required(CONF_VIN): str,
    vol.Required(CONF_PIN): str,
})


async def generate_token(
    hass: core.HomeAssistant, username: str, password: str
) -> dict[str, Any]:
    """Validate the user input allows us to connect."""

    auth = TokenAuth()
    try:
        await hass.async_add_executor_job(
            auth.generate, username, password
        )
    except Exception as ex:
        raise CannotConnect from ex

    return auth.token.to_dict()


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Nissan."""

    VERSION = 1

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._current: dict[str, Any] = {}
        self._entry: config_entries.ConfigEntry | None = None
        self._reason: str = "reconfigure_success"

    async def _async_create_current(self) -> config_entries.ConfigFlowResult:
        """Create or update the config_entry."""
        await self.async_set_unique_id(self._current[CONF_VIN])

        if self._entry:
            self.async_update_reload_and_abort(
                self._entry,
                data=self._entry.data | self._current,
                reason=self._reason
            )

        return self.async_create_entry(
            title=self._current[CONF_VIN],
            data=self._current,
        )

    def async_show_form(
        self, *,
        data_schema: vol.Schema | None = None,
        **kwargs,
    ) -> config_entries.ConfigFlowResult:
        if data_schema:
            data_schema = self.add_suggested_values_to_schema(data_schema, self._current)
        return super().async_show_form(data_schema=data_schema, **kwargs)

    async def async_step_vehicle_data(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            self._current[CONF_VIN] = user_input[CONF_VIN]
            self._current[CONF_PIN] = user_input[CONF_PIN]

            if not errors:
                return await self._async_create_current()

        return self.async_show_form(
            step_id="vehicle_data",
            data_schema=VEHICLE_SCHEMA,
            errors=errors,
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            self._current[CONF_USERNAME] = user_input[CONF_USERNAME]

            try:
                self._current[CONF_TOKEN] = await generate_token(
                    self.hass, user_input[CONF_USERNAME], user_input[CONF_PASSWORD]
                )
            except CannotConnect:
                errors["base"] = "cannot_connect"

            if not errors:
                return await self.async_step_vehicle_data()

        return self.async_show_form(
            step_id="user",
            data_schema=USER_SCHEMA,
            errors=errors,
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> config_entries.ConfigFlowResult:
        """Handle configuration by re-auth."""
        self._async_reconfigure(entry_data)
        return await self.async_step_user()

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle a reconfiguration flow initialized by the user."""
        self._async_reconfigure(user_input)
        return await self.async_step_vehicle_data()

    def _async_reconfigure(
        self, entry_data: Mapping[str, Any] | None = None, reason: str | None = None
    ):
        if entry_id := self.context.get("entry_id"):
            self._entry = self.hass.config_entries.async_get_entry(entry_id)
        if self._entry:
            self._current.update(**self._entry.data)
        if entry_data:
            self._current.update(**entry_data)
        if reason:
            self._reason = reason


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""
