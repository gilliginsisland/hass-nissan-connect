from typing import Any, Mapping

import voluptuous as vol

from homeassistant import config_entries, core, exceptions
from homeassistant.const import (
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_PIN,
)

from .api.auth import TokenAuth

from .const import (
    CONFIG_ENTRY_VERSION,
    CONF_TOKEN,
    CONF_VIN,
    DOMAIN,
    SUBENTRY_TYPE_VEHICLE,
)

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

    VERSION = CONFIG_ENTRY_VERSION

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._current: dict[str, Any] = {}
        self._entry: config_entries.ConfigEntry | None = None
        self._reason: str = "reconfigure"

    @classmethod
    @core.callback
    def async_get_supported_subentry_types(
        cls, config_entry: config_entries.ConfigEntry
    ) -> dict[str, type[config_entries.ConfigSubentryFlow]]:
        """Return subentries supported by this integration."""
        return {SUBENTRY_TYPE_VEHICLE: VehicleSubentryFlowHandler}

    async def async_on_create_entry(
        self, result: config_entries.ConfigFlowResult
    ) -> config_entries.ConfigFlowResult:
        """Create a vehicle subentry flow after creating the account entry."""
        subentry_result = await self.hass.config_entries.subentries.async_init(
            (result["result"].entry_id, SUBENTRY_TYPE_VEHICLE),
            context=config_entries.SubentryFlowContext(
                source=config_entries.SOURCE_USER,
            ),
        )
        result["next_flow"] = (
            config_entries.FlowType.CONFIG_SUBENTRIES_FLOW,
            subentry_result["flow_id"],
        )
        return result

    def async_show_form(
        self, *,
        data_schema: vol.Schema | None = None,
        **kwargs,
    ) -> config_entries.ConfigFlowResult:
        if data_schema:
            data_schema = self.add_suggested_values_to_schema(data_schema, self._current)
        return super().async_show_form(data_schema=data_schema, **kwargs)

    def _existing_entry_for_username(
        self, username: str
    ) -> config_entries.ConfigEntry | None:
        return self.hass.config_entries.async_entry_for_domain_unique_id(
            DOMAIN, username
        )

    async def _async_create_or_update_account(
        self, username: str, password: str
    ) -> config_entries.ConfigFlowResult:
        """Create or update the account config entry."""
        username = username.strip()
        await self.async_set_unique_id(username)

        if self._entry:
            existing_entry = self._existing_entry_for_username(username)
            if existing_entry and existing_entry.entry_id != self._entry.entry_id:
                raise AlreadyConfigured
        else:
            self._abort_if_unique_id_configured()

        token = await generate_token(self.hass, username, password)
        self._current[CONF_USERNAME] = username
        self._current[CONF_TOKEN] = token
        data: dict[str, Any] = {
            CONF_USERNAME: username,
            CONF_TOKEN: token,
        }

        if not self._entry:
            return self.async_create_entry(
                title=username,
                data=data,
            )

        return self.async_update_and_abort(
            self._entry,
            unique_id=username,
            title=username,
            data=data,
            reason=f"{self._reason}_successful",
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                return await self._async_create_or_update_account(
                    user_input[CONF_USERNAME], user_input[CONF_PASSWORD]
                )
            except AlreadyConfigured:
                errors["base"] = "already_configured"
            except CannotConnect:
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=USER_SCHEMA,
            errors=errors,
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> config_entries.ConfigFlowResult:
        """Handle configuration by re-auth."""
        self._async_reconfigure(entry_data, reason="reauth")
        return await self.async_step_user()

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle a reconfiguration flow initialized by the user."""
        self._async_reconfigure(reason="reconfigure")
        return await self.async_step_user(user_input)

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


class VehicleSubentryFlowHandler(config_entries.ConfigSubentryFlow):
    """Handle a subentry flow for Nissan vehicles."""

    def _show_vehicle_form(
        self,
        *,
        step_id: str,
        current: Mapping[str, Any] | None = None,
        errors: dict[str, str] | None = None,
    ) -> config_entries.SubentryFlowResult:
        data_schema = VEHICLE_SCHEMA
        if current:
            data_schema = self.add_suggested_values_to_schema(data_schema, current)
        return self.async_show_form(
            step_id=step_id,
            data_schema=data_schema,
            errors=errors or {},
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.SubentryFlowResult:
        """User flow to add a vehicle."""
        if user_input is not None:
            data: dict[str, str] = {
                CONF_VIN: user_input[CONF_VIN].strip().upper(),
                CONF_PIN: user_input[CONF_PIN],
            }
            return self.async_create_entry(
                title=data[CONF_VIN],
                data=data,
                unique_id=data[CONF_VIN],
            )

        return self._show_vehicle_form(step_id="user")

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.SubentryFlowResult:
        """User flow to modify an existing vehicle."""
        entry = self._get_entry()
        subentry = self._get_reconfigure_subentry()

        if user_input is not None:
            data: dict[str, str] = {
                CONF_VIN: user_input[CONF_VIN].strip().upper(),
                CONF_PIN: user_input[CONF_PIN],
            }
            return self.async_update_and_abort(
                entry,
                subentry,
                title=data[CONF_VIN],
                data=data,
                unique_id=data[CONF_VIN],
            )

        return self._show_vehicle_form(
            step_id="reconfigure",
            current=subentry.data,
        )


class AlreadyConfigured(exceptions.HomeAssistantError):
    """Error to indicate the account is already configured."""


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""
