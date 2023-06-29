from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.lock import LockEntity, LockEntityDescription

from .api.schema import LockState

from .const import DOMAIN
from .coordinator import NissanBaseEntity, NissanDataUpdateCoordinator

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Nissan tracker from config entry."""
    coordinator: NissanDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([NissanLock(coordinator)])

class NissanLock(NissanBaseEntity, LockEntity):
    """Nissan vehicle lock."""

    def __init__(self, coordinator: NissanDataUpdateCoordinator) -> None:
        super().__init__(coordinator)

        self.entity_description = LockEntityDescription(
            key='vehicle_lock',
            name='Lock',
            icon='mdi:car-door-lock',
        )

    @property
    def is_locked(self) -> bool:
        return self.data.lock.lockStatus == LockState.LOCKED

    async def async_lock(self) -> None:
        self._attr_is_locking = True
        try:
            await self._async_follow_request(
                await self.hass.async_add_executor_job(
                    self.vehicle.door_lock
                )
            )
        finally:
            self._attr_is_locking = False
            await self.async_update()

    async def async_unlock(self) -> None:
        self._attr_is_unlocking = True
        try:
            await self._async_follow_request(
                await self.hass.async_add_executor_job(
                    self.vehicle.door_unlock
                )
            )
        finally:
            self._attr_is_unlocking = False
            await self.async_update()
