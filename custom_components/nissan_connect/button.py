from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.button import ButtonEntity, ButtonEntityDescription

from .api.vehicle import Vehicle
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


@dataclass
class NissanRequiredKeysMixin:
    """Mixin for required keys."""

    remote_service: RemoteCommand


@dataclass
class NissanButtonEntityDescription(ButtonEntityDescription, NissanRequiredKeysMixin):
    """Class describing Nissan button entities."""


BUTTON_TYPES: list[NissanButtonEntityDescription] = [
    NissanButtonEntityDescription(
        key=RemoteCommand.LOCK.name,
        name='Lock',
        remote_service=RemoteCommand.LOCK,
    ),
    NissanButtonEntityDescription(
        key=RemoteCommand.UNLOCK.name,
        name='Unlock',
        remote_service=RemoteCommand.UNLOCK,
    ),
    NissanButtonEntityDescription(
        key=RemoteCommand.START.name,
        name='Start',
        remote_service=RemoteCommand.START,
    ),
    NissanButtonEntityDescription(
        key=RemoteCommand.STOP.name,
        name='Stop',
        remote_service=RemoteCommand.STOP,
    ),
    NissanButtonEntityDescription(
        key=RemoteCommand.DOUBLE_START.name,
        name='DoubleStart',
        remote_service=RemoteCommand.DOUBLE_START,
    ),
    NissanButtonEntityDescription(
        key=RemoteCommand.HORN_ONLY.name,
        name='Horn',
        remote_service=RemoteCommand.HORN_ONLY,
    ),
    NissanButtonEntityDescription(
        key=RemoteCommand.LIGHT_ONLY.name,
        name='Lights',
        remote_service=RemoteCommand.LIGHT_ONLY,
    ),
    NissanButtonEntityDescription(
        key=RemoteCommand.HORN_LIGHT.name,
        name='HornLights',
        remote_service=RemoteCommand.HORN_LIGHT,
    ),
]


class NissanButton(NissanEntityMixin, ButtonEntity):
    """Representation of a MyBMW button."""

    entity_description: NissanButtonEntityDescription

    def __init__(
        self,
        vehicle: Vehicle,
        description: NissanButtonEntityDescription,
    ) -> None:
        """Initialize Nissan vehicle button."""
        self.entity_description = description
        super().__init__(vehicle)

    async def async_press(self) -> None:
        """Press the button."""
        await self._async_follow_request(
            self.vehicle.send_command(
                self.entity_description.remote_service,
                pin='',
            )
        )
