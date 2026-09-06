"""Diagnostics for Ypsilon Local."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

TO_REDACT = {"mac", "host", "unique_id"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return everything needed to debug a report, minus identifying data."""
    coordinator = entry.runtime_data
    client = coordinator.client

    return {
        "entry": {
            "version": entry.version,
            "options": dict(entry.options),
            "data": async_redact_data(dict(entry.data), TO_REDACT),
        },
        "connection": {
            "available": coordinator.last_update_success,
            "scan_interval": coordinator.scan_interval,
            "firmware": client.firmware,
            "transient_retries": client.transient_retries,
            "reauth_count": client.reauth_count,
        },
        "state": async_redact_data(coordinator.data, TO_REDACT)
        if coordinator.data
        else None,
    }
