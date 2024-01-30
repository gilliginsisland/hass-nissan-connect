from dataclasses import dataclass
import functools as ft

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.button import ButtonEntity, ButtonEntityDescription

from .api.schema import RemoteCommand

from . import DomainData
from .const import DOMAIN
from .coordinator import NissanEntityMixin


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the BMW buttons from config entry."""
    data: DomainData = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([NissanButton(data.vehicle, button) for button in BUTTON_TYPES])


@dataclass(frozen=True, kw_only=True)
class NissanButtonEntityDescription(ButtonEntityDescription):
    """Class describing Nissan button entities."""

    remote_service: RemoteCommand


BUTTON_TYPES: list[NissanButtonEntityDescription] = [
    NissanButtonEntityDescription(
        key=RemoteCommand.LOCK.name,
        name='Remote Lock',
        remote_service=RemoteCommand.LOCK,
    ),
    NissanButtonEntityDescription(
        key=RemoteCommand.UNLOCK.name,
        name='Remote Unlock',
        remote_service=RemoteCommand.UNLOCK,
    ),
    NissanButtonEntityDescription(
        key=RemoteCommand.START.name,
        name='Remote Start',
        remote_service=RemoteCommand.START,
    ),
    NissanButtonEntityDescription(
        key=RemoteCommand.STOP.name,
        name='Remote Stop',
        remote_service=RemoteCommand.STOP,
    ),
    NissanButtonEntityDescription(
        key=RemoteCommand.DOUBLE_START.name,
        name='Remote Double Start',
        remote_service=RemoteCommand.DOUBLE_START,
    ),
    NissanButtonEntityDescription(
        key=RemoteCommand.HORN_ONLY.name,
        name='Remote Horn',
        remote_service=RemoteCommand.HORN_ONLY,
    ),
    NissanButtonEntityDescription(
        key=RemoteCommand.LIGHT_ONLY.name,
        name='Remote Lights',
        remote_service=RemoteCommand.LIGHT_ONLY,
    ),
    NissanButtonEntityDescription(
        key=RemoteCommand.HORN_LIGHT.name,
        name='Remote Horn Lights',
        remote_service=RemoteCommand.HORN_LIGHT,
    ),
]


class NissanButton(NissanEntityMixin[NissanButtonEntityDescription], ButtonEntity):
    """Representation of a NissanConnect button."""

    async def async_press(self) -> None:
        """Press the button."""
        await self._async_send_command(
            ft.partial(
                self._vehicle.send_command,
                self.entity_description.remote_service,
            ),
        )
