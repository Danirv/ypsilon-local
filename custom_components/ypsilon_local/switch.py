"""Switch entities for Ypsilon Local."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import YpsilonConnectionError
from .const import DOMAIN
from .coordinator import YpsilonDataUpdateCoordinator
from .entity import YpsilonEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    async_add_entities([YpsilonVacationSwitch(coordinator, entry)])


class YpsilonVacationSwitch(YpsilonEntity, SwitchEntity):
    """Vacation-mode flag with the legacy application's state-machine guards."""

    _attr_translation_key = "vacation_mode"
    _attr_icon = "mdi:beach"

    def __init__(
        self, coordinator: YpsilonDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator, entry)
        base_id = entry.unique_id or entry.entry_id
        self._attr_unique_id = f"{base_id}_vacation_mode"

    @property
    def is_on(self) -> bool | None:
        if not self.coordinator.data:
            return None
        if self._pending_value is not None:
            return bool(self._pending_value)
        value = self.coordinator.data.get("vacationPattern")
        return None if value is None else bool(value)

    async def _set(self, enabled: bool) -> None:
        self._set_pending(enabled)
        try:
            await self.coordinator.async_set_vacation_mode(enabled)
        except YpsilonConnectionError as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="write_failed",
                translation_placeholders={"name": "vacation mode", "error": str(err)},
            ) from err
        finally:
            self._pending_value = None
            self.async_write_ha_state()

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._set(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._set(False)
