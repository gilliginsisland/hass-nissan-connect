from typing import Any, Mapping

import voluptuous as vol

from homeassistant import config_entries, core, exceptions
from homeassistant.const import (
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_PIN,
)
from homeassistant.data_entry_flow import (
    FlowHandler,
    FlowResult,
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


class FlowMixin(FlowHandler):
    """Represent the base config flow for NissanConnect."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._current: dict[str, Any] = {}
        self._entry: config_entries.ConfigEntry | None = None

    async def async_step_vehicle_data(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            self._current[CONF_VIN] = user_input[CONF_VIN]
            self._current[CONF_PIN] = user_input[CONF_PIN]

            if not errors:
                return self._async_create_current()

        return self.async_show_form(
            step_id="vehicle_data",
            data_schema=VEHICLE_SCHEMA,
            errors=errors,
        )

    def _async_create_current(self) -> FlowResult:
        """Create or update the config_entry."""
        if self._entry:
            self.hass.config_entries.async_update_entry(
                self._entry, data=self._entry.data | self._current
            )
            self.hass.async_create_task(
                self.hass.config_entries.async_reload(self._entry.entry_id)
            )
            return self.async_abort(reason="reauth_successful")

        return self.async_create_entry(
            title=self._current[CONF_VIN],
            data=self._current,
        )

    def async_show_form(
        self, *,
        data_schema: vol.Schema | None = None,
        **kwargs,
    ) -> FlowResult:
        if data_schema:
            data_schema = self.add_suggested_values_to_schema(data_schema, self._current)
        return super().async_show_form(data_schema=data_schema, **kwargs)


class ConfigFlow(FlowMixin, config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Nissan."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
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

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> FlowResult:
        """Handle configuration by re-auth."""
        self._entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        self._current.update(entry_data)
        return await self.async_step_user()

    @staticmethod
    @core.callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlow(config_entry)


class OptionsFlow(FlowMixin, config_entries.OptionsFlowWithConfigEntry):
    """Handle an options flow for Nissan."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        self._entry = self.config_entry
        self._current.update(self.config_entry.data)
        return await self.async_step_vehicle_data(user_input)


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""
