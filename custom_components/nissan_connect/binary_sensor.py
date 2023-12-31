"""Device tracker for Nissan vehicles."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
    BinarySensorDeviceClass,
)

from .api.schema import DoorState, VehicleStatus

from . import DomainData
from .const import DOMAIN
from .coordinator import NissanCoordinatorEntity, NissanDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Nissan tracker from config entry."""
    data: DomainData = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([NissanBinarySensor(data.status, sensor) for sensor in BINARY_SENSORS])


BINARY_SENSORS: list[BinarySensorEntityDescription] = [
    BinarySensorEntityDescription(
        key='doorStatusFrontLeft',
        name='Front Left Door',
        icon='mdi:car-door',
        device_class=BinarySensorDeviceClass.DOOR,
    ),
    BinarySensorEntityDescription(
        key='doorStatusFrontRight',
        name='Front Right Door',
        icon='mdi:car-door',
        device_class=BinarySensorDeviceClass.DOOR,
    ),
    BinarySensorEntityDescription(
        key='doorStatusRearLeft',
        name='Rear Left Door',
        icon='mdi:car-door',
        device_class=BinarySensorDeviceClass.DOOR,
    ),
    BinarySensorEntityDescription(
        key='doorStatusRearRight',
        name='Rear Right Door',
        icon='mdi:car-door',
        device_class=BinarySensorDeviceClass.DOOR,
    ),
    BinarySensorEntityDescription(
        key='engineHoodStatus',
        name='Engine Hood',
        icon='mdi:car',
        device_class=BinarySensorDeviceClass.OPENING,
    ),
    BinarySensorEntityDescription(
        key='hatchStatus',
        name='Hatch',
        icon='mdi:car-back',
        device_class=BinarySensorDeviceClass.OPENING,
    ),
]

class NissanBinarySensor(NissanCoordinatorEntity[VehicleStatus], BinarySensorEntity):
    """Nissan door sensor."""

    def __init__(
        self,
        coordinator: NissanDataUpdateCoordinator[VehicleStatus],
        description: BinarySensorEntityDescription,
    ) -> None:
        """Initialize the Tracker."""
        super().__init__(coordinator)

        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        state: DoorState = self.data.lockStatus[self.entity_description.key]
        return state == DoorState.OPEN
