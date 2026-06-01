"""Coordinator for Nissan."""
from __future__ import annotations
import functools as ft
import logging
from collections.abc import Awaitable, Callable
from datetime import timedelta
from typing import TypeVar

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api.error import TokenAuthError
from .api.vehicle import Vehicle
from .api.schema import LocationStatus, VehicleStatus

_LOGGER = logging.getLogger(__name__)
_SCAN_INTERVAL = timedelta(minutes=5)
_DataT = TypeVar("_DataT")


class NissanUpdateCoordinator(DataUpdateCoordinator[_DataT]):
    """Class to manage fetching Nissan data."""

    def __init__(
        self,
        hass: HomeAssistant,
        *,
        entry: ConfigEntry,
        vehicle: Vehicle,
        update_method: Callable[[Vehicle], _DataT],
    ) -> None:
        """Initialize Nissan data updater."""
        self.vehicle = vehicle
        self._update_method: Callable[[], Awaitable[_DataT]] = ft.partial(
            hass.async_add_executor_job, update_method, vehicle
        )
        name=f'{type(self).__name__} {vehicle.vin}'
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=name,
            update_interval=_SCAN_INTERVAL,
        )

    async def _async_update_data(self) -> _DataT:
        """Update data."""
        try:
            return await self._update_method()
        except TokenAuthError as err:
            raise ConfigEntryAuthFailed() from err
        except Exception as err:
            raise UpdateFailed() from err


class NissanLocationUpdateCoordinator(NissanUpdateCoordinator[LocationStatus]):
    """Class to manage fetching Nissan location data."""

    def __init__(
        self,
        hass: HomeAssistant,
        *,
        entry: ConfigEntry,
        vehicle: Vehicle,
    ) -> None:
        """Initialize Nissan location data updater."""
        super().__init__(
            hass,
            entry=entry,
            vehicle=vehicle,
            update_method=Vehicle.location,
        )


class NissanStatusUpdateCoordinator(NissanUpdateCoordinator[VehicleStatus]):
    """Class to manage fetching Nissan vehicle status data."""

    def __init__(
        self,
        hass: HomeAssistant,
        *,
        entry: ConfigEntry,
        vehicle: Vehicle,
    ) -> None:
        """Initialize Nissan vehicle status data updater."""
        super().__init__(
            hass,
            entry=entry,
            vehicle=vehicle,
            update_method=Vehicle.vehicle_status,
        )
