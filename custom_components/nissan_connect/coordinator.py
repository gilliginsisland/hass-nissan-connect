"""Coordinator for Nissan."""
from __future__ import annotations
from typing import Any, Callable
from dataclasses import dataclass
from datetime import timedelta
import functools as ft
import asyncio
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    CoordinatorEntity,
    UpdateFailed,
)
from homeassistant.util.async_ import run_callback_threadsafe

from .api.auth import Auth, Token
from .api.vehicle import Vehicle
from .api.schema import (
    GeoPoint,
    LockStatus,
    PressureStatus,
    RequestState,
    RequestStatus,
)

from .const import CONF_TOKEN, CONF_VIN, DOMAIN, ATTRIBUTION

DEFAULT_SCAN_INTERVAL_SECONDS = 300
SCAN_INTERVAL = timedelta(seconds=DEFAULT_SCAN_INTERVAL_SECONDS)
_LOGGER = logging.getLogger(__name__)


@dataclass
class VehicleData():
    location: GeoPoint
    pressure: PressureStatus
    lock: LockStatus


class NissanDataUpdateCoordinator(DataUpdateCoordinator[VehicleData]):
    """Class to manage fetching Nissan data."""
    def __init__(self, hass: HomeAssistant, *, entry: ConfigEntry) -> None:
        """Initialize vehicle-wide Nissan data updater."""
        token = Token.from_dict(entry.data[CONF_TOKEN])
        def token_updater(token: Token):
            """Handle from sync context when token is updated."""
            run_callback_threadsafe(
                hass.loop,
                ft.partial(
                    hass.config_entries.async_update_entry,
                    entry,
                    data={**entry.data, CONF_TOKEN: token.to_dict()},
                ),
            ).result()

        self.auth = Auth(token=token, token_updater=token_updater)
        self.vehicle = Vehicle(self.auth, entry.data[CONF_VIN])
        self._entry = entry

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}-{entry.data['vin']}",
            update_interval=SCAN_INTERVAL,
            update_method=self._async_update_data
        )

    async def _async_update_data(self) -> VehicleData:
        """Fetch data from Nissan."""
        try:
            location, vehicle = await asyncio.gather(
                self.hass.async_add_executor_job(self.vehicle.location),
                self.hass.async_add_executor_job(self.vehicle.vehicle_status),
            )
        except Exception as err:
            raise UpdateFailed(f"Error communicating with Nissan API: {err}") from err

        return VehicleData(
            location=location.location,
            pressure=vehicle.pressure,
            lock=vehicle.lockStatus,
        )


class NissanBaseEntity(CoordinatorEntity[NissanDataUpdateCoordinator]):
    """Common base for Nissan entities."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(self, coordinator: NissanDataUpdateCoordinator) -> None:
        """Initialize entity."""
        super().__init__(coordinator)

        self.vehicle = self.coordinator.vehicle
        self._attrs: dict[str, Any] = {
            "vin": self.vehicle.vin,
        }
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self.vehicle.vin)},
        )

    @property
    def data(self):
        return self.coordinator.data

    @property
    def unique_id(self) -> str:
        return f'{self.vehicle.vin}_{self.entity_description.key}'

    async def _async_follow_request(
        self,
        status_func: Callable[[], RequestStatus],
        delay: int = 1
    ) -> RequestStatus:
        while True:
            await asyncio.sleep(delay)
            r = await self.hass.async_add_executor_job(status_func)
            if r.status != RequestState.INITIATED:
                return r
            delay += 1
