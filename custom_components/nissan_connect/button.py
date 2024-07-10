import functools as ft

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.button import ButtonEntity, ButtonEntityDescription

from .api.schema import RemoteCommand

from . import RuntimeData
from .entity import NissanEntity


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry[RuntimeData],
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the BMW buttons from config entry."""
    async_add_entities([NissanButton(config_entry.runtime_data.vehicle, button) for button in BUTTON_TYPES])


BUTTON_TYPES: list[ButtonEntityDescription] = [
    ButtonEntityDescription(
        key=RemoteCommand.LOCK.name,
        name='Remote Lock',
    ),
    ButtonEntityDescription(
        key=RemoteCommand.UNLOCK.name,
        name='Remote Unlock',
    ),
    ButtonEntityDescription(
        key=RemoteCommand.START.name,
        name='Remote Start',
    ),
    ButtonEntityDescription(
        key=RemoteCommand.STOP.name,
        name='Remote Stop',
    ),
    ButtonEntityDescription(
        key=RemoteCommand.DOUBLE_START.name,
        name='Remote Double Start',
    ),
    ButtonEntityDescription(
        key=RemoteCommand.HORN_ONLY.name,
        name='Remote Horn',
    ),
    ButtonEntityDescription(
        key=RemoteCommand.LIGHT_ONLY.name,
        name='Remote Lights',
    ),
    ButtonEntityDescription(
        key=RemoteCommand.HORN_LIGHT.name,
        name='Remote Horn Lights',
    ),
]


class NissanButton(NissanEntity, ButtonEntity):
    """Representation of a NissanConnect button."""

    async def async_press(self) -> None:
        """Press the button."""
        await self._async_send_command(
            ft.partial(
                self._vehicle.send_command,
                RemoteCommand[self.entity_description.key],
            ),
        )
