"""Device tracker for Nissan vehicles."""
from __future__ import annotations

from homeassistant.components.device_tracker import SourceType, TrackerEntity
from homeassistant.helpers.entity import EntityDescription

from .api.schema import LocationStatus

from . import VehicleRuntimeData
from .entity import NissanCoordinatorEntity, async_vehicle_entry_setup


@async_vehicle_entry_setup
def async_setup_entry(runtime_data: VehicleRuntimeData):
    """Set up the Nissan tracker from config entry."""
    return [
        NissanDeviceTracker(runtime_data.location_coordinator, tracker)
        for tracker in TRACKER_TYPES
    ]


TRACKER_TYPES: tuple[EntityDescription, ...] = (
    EntityDescription(
        key='vehicle_location',
        name='Location',
        icon='mdi:car',
    )
)


class NissanDeviceTracker(NissanCoordinatorEntity[LocationStatus], TrackerEntity):
    """Nissan device tracker."""

    @property
    def latitude(self) -> float:
        """Return latitude value of the device."""
        return self.data.location.latitude

    @property
    def longitude(self) -> float:
        """Return longitude value of the device."""
        return self.data.location.longitude

    @property
    def source_type(self) -> SourceType:
        """Return the source type, eg gps or router, of the device."""
        return SourceType.GPS
