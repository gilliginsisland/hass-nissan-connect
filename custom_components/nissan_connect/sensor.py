"""Device tracker for Nissan vehicles."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfPressure
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
    SensorDeviceClass,
)

from .api.schema import VehicleStatus

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
    async_add_entities([NissanTirePressureSensor(data.status, sensor) for sensor in TIRE_SENSOR_TYPES])


TIRE_TYPES = {
    'flPressure': 'Front Left Tire Pressure',
    'frPressure': 'Front Right Tire Pressure',
    'rlPressure': 'Rear Left Tire Pressure',
    'rrPressure': 'Rear Right Tire Pressure',
}

TIRE_SENSOR_TYPES = {
    SensorEntityDescription(
        key=key, name=value, icon='mdi:tire',
        device_class=SensorDeviceClass.PRESSURE,
        native_unit_of_measurement=UnitOfPressure.PSI,
        state_class=SensorStateClass.MEASUREMENT,
    ) for key, value in TIRE_TYPES.items()
}


class NissanTirePressureSensor(NissanCoordinatorEntity[SensorEntityDescription, VehicleStatus], SensorEntity):
    """Nissan tire pressure sensor."""

    @property
    def native_value(self) -> int:
        return self.data.pressure[self.entity_description.key].value
