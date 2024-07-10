from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.lock import LockEntity, LockEntityDescription

from .api.schema import LockState, VehicleStatus

from . import RuntimeData
from .entity import NissanCoordinatorEntity


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry[RuntimeData],
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Nissan tracker from config entry."""
    async_add_entities([NissanLock(config_entry.runtime_data.status, lock) for lock in LOCK_TYPES])


LOCK_TYPES = [
    LockEntityDescription(
        key='vehicle_lock',
        name='Lock',
        icon='mdi:car-door-lock',
    ),
]


class NissanLock(NissanCoordinatorEntity[VehicleStatus], LockEntity):
    """Nissan vehicle lock."""

    @property
    def is_locked(self) -> bool:
        return self.data.lockStatus.lockStatus == LockState.LOCKED

    @property
    def is_locking(self) -> bool:
        return self._current_command == self._vehicle.door_lock

    @property
    def is_unlocking(self) -> bool:
        return self._current_command == self._vehicle.door_unlock

    async def async_lock(self, **kwargs) -> None:
        self.hass.create_task(
            self._async_send_command(self._vehicle.door_lock)
        )

    async def async_unlock(self, **kwargs) -> None:
        self.hass.create_task(
            self._async_send_command(self._vehicle.door_unlock)
        )
