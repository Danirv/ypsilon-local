"""Number entities for Ypsilon Local."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.number import NumberEntity, NumberEntityDescription, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfMass, UnitOfTime, UnitOfVolumeFlowRate
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError

from .const import DOMAIN
from .entity import YpsilonEntity
from .api import YpsilonConnectionError

@dataclass(frozen=True, kw_only=True)
class YpsilonNumberDescription(NumberEntityDescription):
    field_id: int
    field_name: str
    # Flow-family fields are stored as hundredths on the wire; the entity
    # works in the human unit and converts on the way in and out.
    hundredths: bool = False

NUMBERS = (
    YpsilonNumberDescription(
        key="salt_addition", translation_key="salt_addition", field_id=43, field_name="saltAddition",
        native_min_value=0, native_max_value=100, native_step=1,
        native_unit_of_measurement=UnitOfMass.KILOGRAMS, entity_category=EntityCategory.CONFIG, icon="mdi:shaker-outline",
    ),
    YpsilonNumberDescription(
        key="raw_water_hardness", translation_key="raw_water_hardness", field_id=47, field_name="rawWaterHardness",
        native_min_value=50, native_max_value=1500, native_step=10,
        native_unit_of_measurement="mg/L", entity_category=EntityCategory.CONFIG, icon="mdi:water-opacity",
    ),
    YpsilonNumberDescription(
        key="continuous_water_time", translation_key="continuous_water_time", field_id=6, field_name="continuousWaterTime",
        native_min_value=0, native_max_value=255, native_step=1,
        native_unit_of_measurement=UnitOfTime.MINUTES, entity_category=EntityCategory.CONFIG, icon="mdi:pipe-leak",
    ),
    YpsilonNumberDescription(
        key="flow_rate_off", translation_key="flow_rate_off", field_id=7, field_name="flowRateOff",
        hundredths=True,
        native_min_value=0, native_max_value=655.35, native_step=0.01,
        native_unit_of_measurement=UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR, entity_category=EntityCategory.CONFIG, icon="mdi:valve-closed",
    ),
)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = entry.runtime_data
    async_add_entities(YpsilonNumber(coordinator, entry, desc) for desc in NUMBERS)

class YpsilonNumber(YpsilonEntity, NumberEntity):
    entity_description: YpsilonNumberDescription

    def __init__(self, coordinator, entry, description) -> None:
        super().__init__(coordinator, entry)
        self.entity_description = description
        base_id = entry.unique_id or entry.entry_id
        self._attr_unique_id = f"{base_id}_{description.key}"
        self._attr_mode = NumberMode.BOX

    @property
    def native_value(self) -> float | None:
        if not self.coordinator.data:
            return None
        if self._pending_value is not None:
            return self._pending_value
        value = self.coordinator.data.get(self.entity_description.field_name)
        if value is None:
            return None
        if self.entity_description.hundredths:
            return round(value / 100, 2)
        return value

    async def async_set_native_value(self, value: float) -> None:
        # encode_field() picks the right serialisation for this field, so a
        # one-byte setting is never split into low/high by mistake.
        desc = self.entity_description
        # Defensive range check: a service call or script can pass anything,
        # and the valve has no way to reject a syntactically valid frame.
        if desc.native_min_value is not None and value < desc.native_min_value:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="below_minimum",
                translation_placeholders={
                    "value": str(value),
                    "minimum": str(desc.native_min_value),
                },
            )
        if desc.native_max_value is not None and value > desc.native_max_value:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="above_maximum",
                translation_placeholders={
                    "value": str(value),
                    "maximum": str(desc.native_max_value),
                },
            )

        raw = round(value * 100) if desc.hundredths else int(value)
        try:
            await self._async_write({desc.field_id: raw}, value)
        except (YpsilonConnectionError, ValueError) as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="write_failed",
                translation_placeholders={
                    "name": desc.field_name,
                    "error": str(err),
                },
            ) from err