"""Coordinator for Nissan."""
from __future__ import annotations
from typing import Any, Callable, TypeVar
import logging
import functools as ft
from datetime import timedelta
import asyncio

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo, Entity
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    CoordinatorEntity,
    UpdateFailed,
)

from .api.vehicle import RequestStatusTracker, Vehicle
from .api.schema import (
    RequestState,
    RequestStatus,
)

from .const import DOMAIN, ATTRIBUTION

_LOGGER = logging.getLogger(__name__)
_SCAN_INTERVAL = timedelta(minutes=5)

_T = TypeVar("_T")


class NissanDataUpdateCoordinator(DataUpdateCoordinator[_T]):
    """Class to manage fetching Nissan data."""
    def __init__(
        self,
        hass: HomeAssistant,
        *,
        vehicle: Vehicle,
        method: Callable[[Vehicle], _T],
    ) -> None:
        """Initialize vehicle-wide Nissan data updater."""
        self._method = ft.partial(hass.async_add_executor_job, method)
        self.vehicle = vehicle
        name=f'{type(self).__name__} {vehicle.vin}'
        super().__init__(hass, _LOGGER, name=name, update_interval=_SCAN_INTERVAL)

    async def _async_update_data(self) -> _T:
        """Update data."""
        try:
            return await self._method(self.vehicle)
        except Exception as err:
            raise UpdateFailed() from err


class NissanEntityMixin(Entity):
    """Common base for all Nissan entities."""

    def __init__(self, vehicle: Vehicle, *args, **kwargs) -> None:
        """Initialize entity."""
        self._vehicle = vehicle
        self._current_command: Callable[[], RequestStatusTracker] | None = None
        super().__init__(*args, **kwargs)

    @property
    def has_entity_name(self) -> bool:
        return True

    @property
    def attribution(self) -> str:
        return ATTRIBUTION

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "vin": self.vehicle.vin,
        }

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.vehicle.vin)},
        )

    @property
    def unique_id(self) -> str:
        return f'{self.vehicle.vin}_{self.entity_description.key}'

    @property
    def vehicle(self) -> Vehicle:
        return self._vehicle

    async def _async_follow_request(
        self, status_tracker: RequestStatusTracker, delay: int = 2
    ) -> RequestStatus:
        while True:
            await asyncio.sleep(delay)
            r = await self.hass.async_add_executor_job(status_tracker)
            if r.status != RequestState.INITIATED:
                return r

    async def _async_send_command(
        self, command: Callable[[], RequestStatusTracker]
    ) -> RequestStatus:
        try:
            self._current_command = command
            self.async_write_ha_state()
            return await self._async_follow_request(
                await self.hass.async_add_executor_job(command)
            )
        finally:
            if isinstance(self, CoordinatorEntity):
                await self.coordinator.async_request_refresh()
            self._current_command = None
            self.async_write_ha_state()


class NissanCoordinatorEntity(NissanEntityMixin, CoordinatorEntity[NissanDataUpdateCoordinator[_T]]):
    """Common base for Nissan coordinator entities."""

    def __init__(self, coordinator: NissanDataUpdateCoordinator[_T]) -> None:
        """Initialize entity."""
        super().__init__(coordinator.vehicle, coordinator)

    @property
    def data(self) -> _T:
        return self.coordinator.data
