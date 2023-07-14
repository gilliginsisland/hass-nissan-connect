"""Coordinator for Nissan."""
from __future__ import annotations
from typing import Any, Callable, TypeVar
import logging
import functools as ft
from datetime import timedelta
import asyncio

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    CoordinatorEntity,
    UpdateFailed,
)

from .api.vehicle import Vehicle
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


class NissanBaseEntity(CoordinatorEntity[NissanDataUpdateCoordinator[_T]]):
    """Common base for Nissan entities."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(self, coordinator: NissanDataUpdateCoordinator[_T]) -> None:
        """Initialize entity."""
        super().__init__(coordinator)

        self._attrs: dict[str, Any] = {
            "vin": self.vehicle.vin,
        }
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self.vehicle.vin)},
        )

    @property
    def vehicle(self) -> Vehicle:
        return self.coordinator.vehicle

    @property
    def data(self) -> _T:
        return self.coordinator.data

    @property
    def unique_id(self) -> str:
        return f'{self.vehicle.vin}_{self.entity_description.key}'

    async def _async_follow_request(
        self, status_tracker: Callable[[], RequestStatus], delay: int = 2
    ) -> RequestStatus:
        while True:
            await asyncio.sleep(delay)
            r = await self.hass.async_add_executor_job(status_tracker)
            if r.status != RequestState.INITIATED:
                return r
