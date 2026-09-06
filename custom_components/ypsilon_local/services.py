"""Services for Ypsilon Local.

These cover the advanced corners of the protocol that don't map cleanly onto
an entity: writing several fields in one control frame, and stepping the
regeneration state machine by hand.
"""

from __future__ import annotations

import voluptuous as vol

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.service import async_register_admin_service

from .api import YpsilonConnectionError
from .const import (
    DOMAIN,
    FIELD_SYSTEM_MODE,
    SERVICE_ADVANCE_PHASE,
    SERVICE_WRITE_FIELDS,
    WRITABLE_FIELDS,
)

ATTR_CONFIG_ENTRY = "config_entry_id"
ATTR_FIELDS = "fields"
ATTR_PHASE = "phase"

WRITE_FIELDS_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_CONFIG_ENTRY): cv.string,
        vol.Required(ATTR_FIELDS): vol.All(
            {vol.Coerce(int): vol.Any(int, [int])},
            vol.Length(min=1),
        ),
    }
)

ADVANCE_PHASE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_CONFIG_ENTRY): cv.string,
        vol.Required(ATTR_PHASE): vol.All(vol.Coerce(int), vol.Range(min=0, max=4)),
    }
)


def _coordinator(hass: HomeAssistant, entry_id: str):
    entry = hass.config_entries.async_get_entry(entry_id)
    if entry is None or entry.domain != DOMAIN:
        raise ServiceValidationError(f"No Ypsilon config entry with id {entry_id}")
    # runtime_data survives an unload, so check the entry is actually loaded
    # rather than trusting the attribute to be absent.
    if entry.state is not ConfigEntryState.LOADED:
        raise ServiceValidationError("The Ypsilon entry is not loaded")
    return entry.runtime_data


@callback
def async_setup_services(hass: HomeAssistant) -> None:
    """Register the integration services once."""
    if hass.services.has_service(DOMAIN, SERVICE_WRITE_FIELDS):
        return

    async def _write_fields(call: ServiceCall) -> None:
        coordinator = _coordinator(hass, call.data[ATTR_CONFIG_ENTRY])
        raw = call.data[ATTR_FIELDS]

        unknown = sorted(set(raw) - WRITABLE_FIELDS)
        if unknown:
            raise ServiceValidationError(
                f"Fields not known to be writable: {unknown}. "
                "Refusing to guess at the protocol."
            )

        values = {
            field: tuple(value) if isinstance(value, list) else value
            for field, value in raw.items()
        }
        try:
            await coordinator.async_write_and_verify(values)
        except (YpsilonConnectionError, ValueError) as err:
            raise HomeAssistantError(f"Write failed: {err}") from err

    async def _advance_phase(call: ServiceCall) -> None:
        coordinator = _coordinator(hass, call.data[ATTR_CONFIG_ENTRY])
        try:
            await coordinator.async_write_and_verify(
                {FIELD_SYSTEM_MODE: call.data[ATTR_PHASE]}
            )
        except (YpsilonConnectionError, ValueError) as err:
            raise HomeAssistantError(f"Could not change phase: {err}") from err

    async_register_admin_service(
        hass, DOMAIN, SERVICE_WRITE_FIELDS, _write_fields, schema=WRITE_FIELDS_SCHEMA
    )
    async_register_admin_service(
        hass, DOMAIN, SERVICE_ADVANCE_PHASE, _advance_phase, schema=ADVANCE_PHASE_SCHEMA
    )


@callback
def async_unload_services(hass: HomeAssistant) -> None:
    """Remove the services when the last entry goes away."""
    for service in (SERVICE_WRITE_FIELDS, SERVICE_ADVANCE_PHASE):
        hass.services.async_remove(DOMAIN, service)
