import functools as ft

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription

from .api.schema import RemoteCommand, VehicleStatus

from . import VehicleRuntimeData
from .entity import NissanCoordinatorEntity, async_vehicle_entry_setup


@async_vehicle_entry_setup
def async_setup_entry(runtime_data: VehicleRuntimeData):
    """Set up the BMW buttons from config entry."""
    return [
        NissanButton(runtime_data.status_coordinator, button)
        for button in BUTTON_TYPES
    ]


BUTTON_TYPES: tuple[ButtonEntityDescription, ...] = (
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
)


class NissanButton(NissanCoordinatorEntity[VehicleStatus], ButtonEntity):
    """Representation of a NissanConnect button."""

    async def async_press(self) -> None:
        """Press the button."""
        await self._async_send_command(
            ft.partial(
                self._vehicle.send_command,
                RemoteCommand[self.entity_description.key],
            ),
        )
