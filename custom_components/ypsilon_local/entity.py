"""Base entity for Ypsilon Local."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, MODEL_NAME
from .coordinator import YpsilonDataUpdateCoordinator


class YpsilonEntity(CoordinatorEntity[YpsilonDataUpdateCoordinator]):
    """Shared device wiring for every Ypsilon entity."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: YpsilonDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._pending_value: Any | None = None
        self._writes_in_flight = 0
        self._write_target: tuple[dict[int, Any], Any] | None = None

    # -- provisional value after a write ----------------------------------
    #
    # Writes are still verified by a read: this only bridges the second or so
    # between pressing a control and the confirming poll landing, so the UI
    # does not appear to ignore the user. The moment fresh device data
    # arrives the provisional value is dropped, so a rejected write snaps
    # back to reality instead of lingering as a phantom state.

    def _set_pending(self, value: Any) -> None:
        self._pending_value = value
        self.async_write_ha_state()

    @callback
    def _handle_coordinator_update(self) -> None:
        # Only drop the provisional value once nothing is being written. While
        # a write is in flight the incoming reading still describes the old
        # state, and clearing here would make the control jump back to the
        # previous value until the next poll - very visible when stepping a
        # number up one click at a time.
        if not self._writes_in_flight:
            self._pending_value = None
        super()._handle_coordinator_update()

    async def _async_write(self, fields: dict[int, Any], display: Any) -> None:
        """Write fields, showing `display` until the device confirms it.

        Repeated edits are coalesced. Stepping a number up ten times would
        otherwise send ten frames down a slow serial link to a valve that only
        cares about the final value, so a change arriving while a write is
        already running just replaces the target: the running writer picks it
        up when it finishes. The first call still awaits its own write, which
        is what surfaces a failure to the user.
        """
        self._set_pending(display)
        self._write_target = (fields, display)

        if self._writes_in_flight:
            # A writer is already draining; it will send this value too.
            return

        self._writes_in_flight += 1
        try:
            while self._write_target is not None:
                target_fields, _ = self._write_target
                self._write_target = None
                await self.coordinator.async_write_and_verify(target_fields)
        except Exception:
            self._write_target = None
            self._pending_value = None
            raise
        finally:
            self._writes_in_flight -= 1
            if not self._writes_in_flight:
                # The last strict read-back has already reconciled the device
                # state. Drop the provisional value now instead of waiting for
                # a later scheduled poll to clear it.
                self._pending_value = None
            self.async_write_ha_state()

    @property
    def device_info(self) -> DeviceInfo:
        unique_id = self._entry.unique_id
        connections = set()
        if unique_id and unique_id.count(":") == 5:
            connections.add((CONNECTION_NETWORK_MAC, unique_id))

        firmware = self.coordinator.client.firmware
        return DeviceInfo(
            identifiers={(DOMAIN, unique_id or self._entry.entry_id)},
            connections=connections,
            manufacturer=MANUFACTURER,
            model=MODEL_NAME,
            # The user can rename the device freely; take the entry title so a
            # renamed entry stays consistent instead of a hardcoded string.
            name=self._entry.title,
            sw_version=str(firmware) if firmware is not None else None,
            # No configuration_url: the BroadLink module serves no web page, so
            # the "visit device" link would only lead to a connection error.
        )
