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
from .coordinator import NissanCoordinatorEntity


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Nissan tracker from config entry."""
    data: DomainData = hass.data[DOMAIN][config_entry.entry_id]

    sensor_types = (
        (NissanLockSensor, LOCK_SENSORS),
        (NissanMalfunctionIndicatorLamp, MALFUNCTION_SENSORS),
    )

    async_add_entities(
        [cls(data.status, sensor) for (cls, sensors) in sensor_types for sensor in sensors]
    )


LOCK_SENSORS: tuple[BinarySensorEntityDescription, ...] = (
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
)

MALFUNCTION_SENSORS: tuple[BinarySensorEntityDescription, ...] = (
    BinarySensorEntityDescription(
        key='absWarning',
        name='ABS Warning',
        icon='mdi:car-brake-abs',
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    BinarySensorEntityDescription(
        key='airbagWarning',
        name='AirBag Warning',
        icon='mdi:airbag',
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    BinarySensorEntityDescription(
        key='brakeFluidWarning',
        name='Break Fluid Warning',
        icon='mdi:car-brake-fluid-level',
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    BinarySensorEntityDescription(
        key='oilPressureWarning',
        name='Oil Pressure Warning',
        icon='mdi:car-brake-low-pressure',
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    BinarySensorEntityDescription(
        key='tyrePressureWarning',
        name='Tire Pressure Warning',
        icon='mdi:car-tire-alert',
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    BinarySensorEntityDescription(
        key='oilPressureSwitch',
        name='Oil Pressure Switch',
        icon='mdi:oil',
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    BinarySensorEntityDescription(
        key='lampRequest',
        name='Lamp Request',
        icon='mdi:oil-lamp',
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
)


class NissanLockSensor(
    NissanCoordinatorEntity[BinarySensorEntityDescription, VehicleStatus],
    BinarySensorEntity
):
    """Nissan door sensor."""

    @property
    def is_on(self) -> bool:
        return self.data.lockStatus[self.entity_description.key] == DoorState.OPEN


class NissanMalfunctionIndicatorLamp(
    NissanCoordinatorEntity[BinarySensorEntityDescription, VehicleStatus],
    BinarySensorEntity
):
    """Nissan malfunction indicator lamp sensor."""

    @property
    def is_on(self) -> bool:
        return self.data.healthStatus.malfunctionIndicatorLamps[self.entity_description.key]
