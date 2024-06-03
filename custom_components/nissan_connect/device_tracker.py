"""Device tracker for Nissan vehicles."""
from __future__ import annotations

from homeassistant.components.device_tracker import SourceType, TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api.schema import LocationStatus

from . import RuntimeData
from .coordinator import NissanCoordinatorEntity


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry[RuntimeData],
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Nissan tracker from config entry."""
    async_add_entities([NissanDeviceTracker(config_entry.runtime_data.location, tracker) for tracker in TRACKER_TYPES])


TRACKER_TYPES = [
    EntityDescription(
        key='vehicle_location',
        name='Location',
        icon='mdi:car',
    )
]


class NissanDeviceTracker(NissanCoordinatorEntity[LocationStatus], TrackerEntity):
    """Nissan device tracker."""

    @property
    def latitude(self) -> float | None:
        """Return latitude value of the device."""
        return self.data.location.latitude

    @property
    def longitude(self) -> float | None:
        """Return longitude value of the device."""
        return self.data.location.longitude

    @property
    def source_type(self) -> SourceType:
        """Return the source type, eg gps or router, of the device."""
        return SourceType.GPS
