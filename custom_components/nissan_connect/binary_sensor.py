"""Device tracker for Nissan vehicles."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
    BinarySensorDeviceClass,
)

from .api.schema import DoorState, VehicleStatus

from . import VehicleRuntimeData
from .entity import NissanCoordinatorEntity, async_vehicle_entry_setup


@async_vehicle_entry_setup
def async_setup_entry(runtime_data: VehicleRuntimeData):
    """Set up the Nissan tracker from config entry."""
    return [
        cls(runtime_data.status_coordinator, sensor)
        for (cls, sensors) in SENSOR_TYPES for sensor in sensors
    ]


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
        key='emergencyBrakingWarning',
        name='Emergency Braking Warning',
        icon='mdi:car-brake-alert',
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


class NissanLockSensor(NissanCoordinatorEntity[VehicleStatus], BinarySensorEntity):
    """Nissan door sensor."""

    @property
    def is_on(self) -> bool | None:
        state = self.data.lockStatus[self.entity_description.key]
        if state is None:
            return None
        return state == DoorState.OPEN


class NissanMalfunctionIndicatorLamp(NissanCoordinatorEntity[VehicleStatus], BinarySensorEntity):
    """Nissan malfunction indicator lamp sensor."""

    @property
    def is_on(self) -> bool | None:
        return self.data.healthStatus.malfunctionIndicatorLamps[self.entity_description.key]


TIRE_STATUS_SENSORS: tuple[BinarySensorEntityDescription, ...] = tuple(
    BinarySensorEntityDescription(
        key=key,
        name=name,
        icon='mdi:car-tire-alert',
        device_class=BinarySensorDeviceClass.PROBLEM,
    ) for key, name in (
        ('flStatus', 'Front Left Tire Status'),
        ('frStatus', 'Front Right Tire Status'),
        ('rlStatus', 'Rear Left Tire Status'),
        ('rrStatus', 'Rear Right Tire Status'),
    )
)


class NissanTireStatusSensor(NissanCoordinatorEntity[VehicleStatus], BinarySensorEntity):
    """Nissan per-tire pressure status sensor."""

    @property
    def is_on(self) -> bool:
        return self.data.pressure[self.entity_description.key]


SENSOR_TYPES = (
    (NissanLockSensor, LOCK_SENSORS),
    (NissanMalfunctionIndicatorLamp, MALFUNCTION_SENSORS),
    (NissanTireStatusSensor, TIRE_STATUS_SENSORS),
)
