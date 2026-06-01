from __future__ import annotations

from homeassistant.components.lock import LockEntity, LockEntityDescription

from .api.schema import LockState, VehicleStatus

from . import VehicleRuntimeData
from .entity import NissanCoordinatorEntity, async_vehicle_entry_setup


@async_vehicle_entry_setup
def async_setup_entry(runtime_data: VehicleRuntimeData):
    """Set up the Nissan tracker from config entry."""
    return [
        NissanLock(runtime_data.status_coordinator, lock)
        for lock in LOCK_TYPES
    ]


LOCK_TYPES: tuple[LockEntityDescription, ...] = (
    LockEntityDescription(
        key='vehicle_lock',
        name='Lock',
        icon='mdi:car-door-lock',
    ),
)


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
