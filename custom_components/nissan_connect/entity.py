"""Coordinator for Nissan."""
from __future__ import annotations
from typing import Callable, TypeVar
import asyncio

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity, EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api.vehicle import RequestStatusTracker, Vehicle
from .api.schema import (
    RequestState,
    RequestStatus,
)

from .const import DOMAIN, ATTRIBUTION
from .coordinator import NissanDataUpdateCoordinator

_T = TypeVar("_T")
_RemoteCallable = Callable[[], RequestStatusTracker]


class NissanEntity(Entity):
    """Common base for all Nissan entities."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION

    def __init__(
        self,
        vehicle: Vehicle,
        entity_description: EntityDescription,
        *args,
        **kwargs
    ) -> None:
        """Initialize entity."""

        self._vehicle = vehicle
        self._current_command: _RemoteCallable | None = None

        self._attr_extra_state_attributes = {
            "vin": vehicle.vin,
        }
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, vehicle.vin)},
        )
        self._attr_unique_id = f'{vehicle.vin}_{entity_description.key}'

        self.entity_description = entity_description

        super().__init__(*args, **kwargs)

    async def _async_follow_request(
        self, status_tracker: RequestStatusTracker, delay: int = 2
    ) -> RequestStatus:
        while True:
            await asyncio.sleep(delay)
            r = await self.hass.async_add_executor_job(status_tracker)
            if r.status != RequestState.INITIATED:
                return r

    async def _async_send_command(self, command: _RemoteCallable) -> RequestStatus:
        await self._async_pre_send_command(command)
        try:
            return await self._async_follow_request(
                await self.hass.async_add_executor_job(command)
            )
        finally:
            await self._async_post_send_command(command)

    async def _async_pre_send_command(self, command: _RemoteCallable) -> None:
        self._current_command = command
        self.async_write_ha_state()

    async def _async_post_send_command(self, command: _RemoteCallable) -> None:
        if self._current_command == command:
            self._current_command = None
        self.async_write_ha_state()


class NissanCoordinatorEntity(NissanEntity, CoordinatorEntity[NissanDataUpdateCoordinator[_T]]):
    """Common base for Nissan coordinator entities."""

    def __init__(
        self,
        coordinator: NissanDataUpdateCoordinator[_T],
        entity_description: EntityDescription,
    ) -> None:
        """Initialize entity."""
        super().__init__(coordinator.vehicle, entity_description, coordinator)

    async def _async_post_send_command(self, command: _RemoteCallable) -> None:
        await self.coordinator.async_request_refresh()
        return await super()._async_post_send_command(command)

    @property
    def data(self) -> _T:
        return self.coordinator.data
