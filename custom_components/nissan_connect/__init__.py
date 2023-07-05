"""Support for Nissan Connect Services."""
from __future__ import annotations
import asyncio
from datetime import timedelta
import functools as ft
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform, __version__
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.typing import ConfigType
from homeassistant.util.async_ import run_callback_threadsafe

from .api.auth import Auth, Token
from .api.vehicle import Vehicle
from .api.schema import LocationStatus, VehicleStatus

from .const import (
    DOMAIN,
    CONF_TOKEN,
    CONF_VIN,
)
from .coordinator import NissanDataUpdateCoordinator

DEFAULT_SCAN_INTERVAL_SECONDS = 300
SCAN_INTERVAL = timedelta(seconds=DEFAULT_SCAN_INTERVAL_SECONDS)
_LOGGER = logging.getLogger(__name__)


PLATFORMS = [
    Platform.BINARY_SENSOR,
    # Platform.BUTTON,
    Platform.SENSOR,
    Platform.LOCK,
    Platform.DEVICE_TRACKER,
]


async def async_setup(hass: HomeAssistant, _: ConfigType) -> bool:
    """Set up the Nissan component."""
    hass.data[DOMAIN] = {}
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
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

    token = Token.from_dict(entry.data[CONF_TOKEN])
    auth = Auth(token=token, token_updater=token_updater)
    vehicle = Vehicle(auth, entry.data[CONF_VIN])

    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.data[CONF_VIN])},
        manufacturer='Nissan',
        name=vehicle.vin,
        model='Rogue',
    )

    # Setup the coordinator and set up all platforms
    data = {
        Vehicle: vehicle,
        LocationStatus: NissanDataUpdateCoordinator[LocationStatus](
            hass,
            _LOGGER,
            name=f"{DOMAIN}-{entry.data[CONF_VIN]}-location",
            update_interval=SCAN_INTERVAL,
            update_method=ft.partial(
                hass.async_add_executor_job,
                vehicle.location,
            ),
            vehicle=vehicle,
        ),
        VehicleStatus: NissanDataUpdateCoordinator[VehicleStatus](
            hass,
            _LOGGER,
            name=f"{DOMAIN}-{entry.data[CONF_VIN]}-status",
            update_interval=SCAN_INTERVAL,
            update_method=ft.partial(
                hass.async_add_executor_job,
                vehicle.vehicle_status,
            ),
            vehicle=vehicle,
        ),
    }

    hass.data[DOMAIN][entry.entry_id] = data
    await asyncio.gather(
        data[LocationStatus].async_config_entry_first_refresh(),
        data[VehicleStatus].async_config_entry_first_refresh(),
    )
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, [platform for platform in PLATFORMS]
    )

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
