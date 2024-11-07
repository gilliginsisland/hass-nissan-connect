"""Coordinator for Nissan."""
from __future__ import annotations
from typing import Callable, TypeVar
import logging
import functools as ft
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api.error import TokenAuthError
from .api.vehicle import Vehicle

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
        self._update_method = ft.partial(hass.async_add_executor_job, method)
        self.vehicle = vehicle
        name=f'{type(self).__name__} {vehicle.vin}'
        super().__init__(hass, _LOGGER, name=name, update_interval=_SCAN_INTERVAL)

    async def _async_update_data(self) -> _T:
        """Update data."""
        try:
            return await self._update_method(self.vehicle)
        except TokenAuthError as err:
            raise ConfigEntryAuthFailed() from err
        except Exception as err:
            raise UpdateFailed() from err
