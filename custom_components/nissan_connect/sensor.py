"""Device tracker for Nissan vehicles."""
from __future__ import annotations

from homeassistant.const import UnitOfPressure
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
