from __future__ import annotations
from typing import Callable

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.lock import LockEntity, LockEntityDescription

from .api.vehicle import Vehicle
from .api.schema import LockState, RequestStatus, VehicleStatus

from .const import DOMAIN
from .coordinator import NissanBaseEntity, NissanDataUpdateCoordinator

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Nissan tracker from config entry."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    coordinator: NissanDataUpdateCoordinator[VehicleStatus] = data[VehicleStatus]
    async_add_entities([NissanLock(coordinator)])

class NissanLock(NissanBaseEntity[VehicleStatus], LockEntity):
    """Nissan vehicle lock."""

    def __init__(self, coordinator: NissanDataUpdateCoordinator[VehicleStatus]) -> None:
        super().__init__(coordinator)

        self.entity_description = LockEntityDescription(
            key='vehicle_lock',
            name='Lock',
            icon='mdi:car-door-lock',
        )

    @property
    def is_locked(self) -> bool:
        return self.data.lockStatus.lockStatus == LockState.LOCKED

    async def async_lock(self) -> None:
        self._attr_is_locking = True
        self.async_write_ha_state()
        self.hass.create_task(
            self._async_send_command(self.vehicle.door_lock)
        )

    async def async_unlock(self) -> None:
        self._attr_is_unlocking = True
        self.async_write_ha_state()
        self.hass.create_task(
            self._async_send_command(self.vehicle.door_unlock)
        )

    async def _async_send_command(
        self, command: Callable[[], Callable[[], RequestStatus]]
    ) -> RequestStatus:
        try:
            return await self._async_follow_request(
                await self.hass.async_add_executor_job(command)
            )
        finally:
            await self.coordinator.async_request_refresh()
            self._attr_is_unlocking = False
            self._attr_is_locking = False
            self.async_write_ha_state()
