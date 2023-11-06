from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.lock import LockEntity, LockEntityDescription

from .api.schema import LockState, VehicleStatus

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
    async_add_entities([NissanLock(data.status)])

class NissanLock(NissanCoordinatorEntity[VehicleStatus], LockEntity):
    """Nissan vehicle lock."""

    def __init__(self, coordinator: NissanDataUpdateCoordinator[VehicleStatus]) -> None:
        self.entity_description = LockEntityDescription(
            key='vehicle_lock',
            name='Lock',
            icon='mdi:car-door-lock',
        )
        super().__init__(coordinator)

    @property
    def is_locked(self) -> bool:
        return self.data.lockStatus.lockStatus == LockState.LOCKED

    @property
    def is_locking(self) -> bool:
        return self._current_command == self.vehicle.door_lock

    @property
    def is_unlocking(self) -> bool:
        return self._current_command == self.vehicle.door_unlock

    async def async_lock(self) -> None:
        self.hass.create_task(
            self._async_send_command(self.vehicle.door_lock)
        )

    async def async_unlock(self) -> None:
        self.hass.create_task(
            self._async_send_command(self.vehicle.door_unlock)
        )
