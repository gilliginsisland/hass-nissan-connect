"""Support for Nissan Connect Services."""
from __future__ import annotations
import asyncio
import functools as ft
from collections.abc import Callable
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

from homeassistant.config_entries import ConfigEntry, ConfigSubentry
from homeassistant.const import CONF_PIN, CONF_USERNAME, Platform
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.util.async_ import run_callback_threadsafe

from .api.auth import TokenAuth, Token
from .api.error import TokenAuthError
from .api.vehicle import Vehicle

from .const import (
    CONFIG_ENTRY_VERSION,
    DOMAIN,
    CONF_MIGRATED_TO,
    CONF_TOKEN,
    CONF_VIN,
    SUBENTRY_TYPE_VEHICLE,
)
from .coordinator import (
    NissanLocationUpdateCoordinator,
    NissanStatusUpdateCoordinator,
)

PLATFORMS = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.SENSOR,
    Platform.LOCK,
    Platform.DEVICE_TRACKER,
]


@dataclass
class VehicleRuntimeData():
    subentry_id: str
    vehicle: Vehicle
    location_coordinator: NissanLocationUpdateCoordinator
    status_coordinator: NissanStatusUpdateCoordinator


@dataclass
class RuntimeData():
    auth: TokenAuth
    vehicles: dict[str, VehicleRuntimeData]
    _vehicle_listeners: list[Callable[[VehicleRuntimeData], None]]

    @callback
    def async_add_vehicle_listener(self, listener: Callable[[VehicleRuntimeData], None]) -> CALLBACK_TYPE:
        """Listen for newly added vehicles."""
        self._vehicle_listeners.append(listener)
        return lambda: self._vehicle_listeners.remove(listener)

    @callback
    def async_call_vehicle_listeners(self, vehicle_data: VehicleRuntimeData) -> None:
        """Notify listeners that a vehicle was added."""
        for listener in self._vehicle_listeners:
            listener(vehicle_data)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry[RuntimeData]) -> bool:
    if CONF_MIGRATED_TO in entry.data:
        return True

    auth = TokenAuth(token_storage=TokenStorage(hass, entry))
    try:
        await hass.async_add_executor_job(auth.refresh)
    except TokenAuthError as err:
        raise ConfigEntryAuthFailed() from err
    except Exception as err:
        raise ConfigEntryNotReady() from err

    entry.runtime_data = RuntimeData(
        auth=auth,
        vehicles={},
        _vehicle_listeners=[],
    )

    async def _async_sync_vehicle_subentries(
        hass: HomeAssistant,
        updated_entry: ConfigEntry[RuntimeData],
    ) -> None:
        """Add or remove vehicles to match configured vehicle subentries."""
        data = updated_entry.runtime_data
        subentries_by_vin: dict[str, ConfigSubentry] = {
            subentry.data[CONF_VIN]: subentry
            for subentry in updated_entry.subentries.values()
            if subentry.subentry_type == SUBENTRY_TYPE_VEHICLE
        }
        updated_vins = subentries_by_vin.keys()
        device_registry = dr.async_get(hass)
        entity_registry = er.async_get(hass)

        for vin in data.vehicles.keys() - updated_vins:
            vehicle_data = data.vehicles.pop(vin)
            device_registry.async_clear_config_subentry(
                updated_entry.entry_id, vehicle_data.subentry_id
            )
            entity_registry.async_clear_config_subentry(
                updated_entry.entry_id, vehicle_data.subentry_id
            )

        for vin in updated_vins:
            subentry = subentries_by_vin[vin]
            vehicle_data = data.vehicles.get(vin)
            if vehicle_data and vehicle_data.subentry_id == subentry.subentry_id:
                vehicle_data.vehicle.pin = subentry.data[CONF_PIN]
                continue
            if vehicle_data:
                data.vehicles.pop(vin)
                device_registry.async_clear_config_subentry(
                    updated_entry.entry_id, vehicle_data.subentry_id
                )
                entity_registry.async_clear_config_subentry(
                    updated_entry.entry_id, vehicle_data.subentry_id
                )

            vehicle = Vehicle(data.auth, vin, pin=subentry.data[CONF_PIN])
            vehicle_data = VehicleRuntimeData(
                subentry_id=subentry.subentry_id,
                vehicle=vehicle,
                location_coordinator=NissanLocationUpdateCoordinator(
                    hass, entry=updated_entry, vehicle=vehicle,
                ),
                status_coordinator=NissanStatusUpdateCoordinator(
                    hass, entry=updated_entry, vehicle=vehicle,
                ),
            )
            data.vehicles[vin] = vehicle_data
            await asyncio.gather(
                vehicle_data.location_coordinator.async_refresh(),
                vehicle_data.status_coordinator.async_refresh(),
            )
            data.async_call_vehicle_listeners(vehicle_data)

    await _async_sync_vehicle_subentries(hass, entry)

    entry.async_on_unload(entry.add_update_listener(_async_sync_vehicle_subentries))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate old config entries to account entries with vehicle subentries."""
    if entry.version > CONFIG_ENTRY_VERSION:
        return False

    if CONF_MIGRATED_TO in entry.data:
        hass.config_entries.async_update_entry(
            entry,
            version=CONFIG_ENTRY_VERSION,
        )
        hass.async_create_task(
            hass.config_entries.async_remove(entry.entry_id),
            f"remove migrated {DOMAIN} config entry {entry.entry_id}",
        )
        return True

    device_registry = dr.async_get(hass)

    if entry.version < 2:
        stored_data: dict[str, Any] = dict(entry.data)
        username: str = stored_data[CONF_USERNAME]
        vin: str = stored_data.pop(CONF_VIN)
        pin: str = stored_data.pop(CONF_PIN)

        if (
            (existing_entry := hass.config_entries.async_entry_for_domain_unique_id(
                DOMAIN, username
            ))
            and existing_entry.entry_id != entry.entry_id
            and 2 <= existing_entry.version <= CONFIG_ENTRY_VERSION
        ):
            hass.config_entries.async_update_entry(
                entry,
                data={CONF_MIGRATED_TO: existing_entry.entry_id},
                title=username,
                version=CONFIG_ENTRY_VERSION,
            )
            hass.async_create_task(
                hass.config_entries.async_remove(entry.entry_id),
                f"remove migrated {DOMAIN} config entry {entry.entry_id}",
            )
            entry = existing_entry
        else:
            hass.config_entries.async_update_entry(
                entry,
                data={
                    CONF_USERNAME: username,
                    CONF_TOKEN: stored_data[CONF_TOKEN],
                },
                title=username,
                unique_id=username,
            )

        normalized_vin = vin.strip().upper()
        if not any(
            subentry.unique_id == normalized_vin
            for subentry in entry.get_subentries_of_type(SUBENTRY_TYPE_VEHICLE)
        ):
            subentry_data: dict[str, str] = {
                CONF_VIN: normalized_vin,
                CONF_PIN: pin,
            }
            vehicle_subentry = ConfigSubentry(
                data=MappingProxyType(subentry_data),
                subentry_type=SUBENTRY_TYPE_VEHICLE,
                title=normalized_vin,
                unique_id=normalized_vin,
            )
            hass.config_entries.async_add_subentry(
                entry,
                vehicle_subentry,
            )

            device = device_registry.async_get_device(
                identifiers={(DOMAIN, normalized_vin)}
            )
            if device:
                device_registry.async_update_device(
                    device.id,
                    add_config_entry_id=entry.entry_id,
                    add_config_subentry_id=vehicle_subentry.subentry_id,
                )

    if entry.version < CONFIG_ENTRY_VERSION:
        for device in dr.async_entries_for_config_entry(device_registry, entry.entry_id):
            device_registry.async_update_device(
                device.id,
                remove_config_entry_id=entry.entry_id,
                remove_config_subentry_id=None,
            )
        hass.config_entries.async_update_entry(
            entry,
            version=CONFIG_ENTRY_VERSION,
        )

    return True


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
