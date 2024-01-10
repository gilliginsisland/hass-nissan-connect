"""Support for Nissan Connect Services."""
from __future__ import annotations
import asyncio
import functools as ft
from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PIN, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.typing import ConfigType
from homeassistant.util.async_ import run_callback_threadsafe

from .api.auth import TokenAuth, Token
from .api.vehicle import Vehicle
from .api.schema import LocationStatus, VehicleStatus

from .const import (
    DOMAIN,
    CONF_TOKEN,
    CONF_VIN,
)
from .coordinator import NissanDataUpdateCoordinator

PLATFORMS = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.SENSOR,
    Platform.LOCK,
    Platform.DEVICE_TRACKER,
]


@dataclass
class DomainData():
    vehicle: Vehicle
    status: NissanDataUpdateCoordinator[VehicleStatus]
    location: NissanDataUpdateCoordinator[LocationStatus]


async def async_setup(hass: HomeAssistant, _: ConfigType) -> bool:
    """Set up the Nissan component."""
    hass.data[DOMAIN] = {}
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    auth = TokenAuth(token_storage=TokenStorage(hass, entry))
    vehicle = Vehicle(auth, entry.data[CONF_VIN], pin=entry.data[CONF_PIN])

    # Setup the coordinator and set up all platforms
    data = DomainData(
        vehicle=vehicle,
        location=NissanDataUpdateCoordinator(
            hass, vehicle=vehicle, method=Vehicle.location,
        ),
        status=NissanDataUpdateCoordinator(
            hass, vehicle=vehicle, method=Vehicle.vehicle_status,
        ),
    )

    hass.data[DOMAIN][entry.entry_id] = data

    await asyncio.gather(
        data.location.async_config_entry_first_refresh(),
        data.status.async_config_entry_first_refresh(),
    )

    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.data[CONF_VIN])},
        manufacturer='Nissan',
        name=vehicle.vin,
        model='Rogue',
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


class TokenStorage():
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry

    def get(self) -> Token:
        return Token.from_dict(self.entry.data[CONF_TOKEN])

    def set(self, token: Token):
        """Handle from sync context when token is updated."""
        run_callback_threadsafe(
            self.hass.loop,
            ft.partial(
                self.hass.config_entries.async_update_entry,
                self.entry,
                data={**self.entry.data, CONF_TOKEN: token.to_dict()},
            ),
        ).result()
