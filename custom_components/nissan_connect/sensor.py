"""Device tracker for Nissan vehicles."""
from __future__ import annotations

from datetime import datetime

from homeassistant.const import EntityCategory, UnitOfLength, UnitOfPressure
from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass, # pyright: ignore[reportPrivateImportUsage]
    SensorDeviceClass, # pyright: ignore[reportPrivateImportUsage]
)

from .api.schema import VehicleStatus

from . import VehicleRuntimeData
from .entity import NissanCoordinatorEntity, async_vehicle_entry_setup


@async_vehicle_entry_setup
def async_setup_entry(runtime_data: VehicleRuntimeData):
    """Set up the Nissan tracker from config entry."""
    return [
        NissanTirePressureSensor(runtime_data.status_coordinator, sensor)
        for sensor in TIRE_SENSOR_TYPES
    ] + [
        NissanCockpitSensor(runtime_data.status_coordinator, sensor)
        for sensor in COCKPIT_SENSOR_TYPES
    ] + [
        NissanLastUpdateSensor(runtime_data.status_coordinator, LAST_UPDATE_SENSOR_TYPE),
    ]


TIRE_TYPES: tuple[tuple[str, str], ...] = (
    ('flPressure', 'Front Left Tire Pressure'),
    ('frPressure', 'Front Right Tire Pressure'),
    ('rlPressure', 'Rear Left Tire Pressure'),
    ('rrPressure', 'Rear Right Tire Pressure'),
)

TIRE_SENSOR_TYPES: tuple[SensorEntityDescription, ...] = tuple(
    SensorEntityDescription(
        key=key, name=value, icon='mdi:tire',
        device_class=SensorDeviceClass.PRESSURE,
        native_unit_of_measurement=UnitOfPressure.PSI,
        state_class=SensorStateClass.MEASUREMENT,
    ) for key, value in TIRE_TYPES
)


class NissanTirePressureSensor(NissanCoordinatorEntity[VehicleStatus], SensorEntity):
    """Nissan tire pressure sensor."""

    @property
    def native_value(self) -> int:
        return self.data.pressure[self.entity_description.key].value


COCKPIT_SENSOR_TYPES: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key='totalMileage', name='Odometer', icon='mdi:counter',
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=0,
    ),
    SensorEntityDescription(
        key='fuelAutonomy', name='Range', icon='mdi:gas-station',
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
    ),
)

# The API reports its own unit per value; US vehicles still report 'KM'.
_LENGTH_UNITS: dict[str, UnitOfLength] = {
    'KM': UnitOfLength.KILOMETERS,
    'MI': UnitOfLength.MILES,
}


class NissanCockpitSensor(NissanCoordinatorEntity[VehicleStatus], SensorEntity):
    """Nissan odometer and range sensor."""

    @property
    def native_value(self) -> int:
        return self.data.cockpit[self.entity_description.key].value

    @property
    def native_unit_of_measurement(self) -> str | None:
        # Read at entity registration too, before the first successful poll.
        if self.data is None:
            return UnitOfLength.KILOMETERS
        unit = self.data.cockpit[self.entity_description.key].unit
        return _LENGTH_UNITS.get(unit.upper(), unit)


LAST_UPDATE_SENSOR_TYPE = SensorEntityDescription(
    key='lastUpdateTime', name='Last Update', icon='mdi:clock-outline',
    device_class=SensorDeviceClass.TIMESTAMP,
    entity_category=EntityCategory.DIAGNOSTIC,
)


class NissanLastUpdateSensor(NissanCoordinatorEntity[VehicleStatus], SensorEntity):
    """When the vehicle last reported its status to Nissan."""

    @property
    def native_value(self) -> datetime:
        return self.data.lastUpdateTime
