"""Support for Nissan Connect Services."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform, __version__
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, CONF_VIN
from .coordinator import NissanDataUpdateCoordinator

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
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    # Set up one data coordinator per account/config entry
    coordinator = NissanDataUpdateCoordinator(
        hass,
        entry=entry,
    )
    await coordinator.async_config_entry_first_refresh()

    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.data[CONF_VIN])},
        manufacturer='Nissan',
        name=entry.data[CONF_VIN],
        model='Rogue',
    )

    # Store the coordinator and set up all platforms
    hass.data[DOMAIN][entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(
        entry, [platform for platform in PLATFORMS]
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, [platform for platform in PLATFORMS]
    )

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
