"""Stable semantic mappings for enum-like Runxin F79D fields.

These mappings are deliberately read-only protocol knowledge. They translate
raw controller codes into stable machine-readable states for consumers such as
Home Assistant and diagnostics; they do not make the corresponding fields safe
to write.

The work-pattern labels were recovered directly from the legacy WaterDevice
application. Codes 0..6 also align with Runxin's published down-flow,
up-flow and filter mode families. We intentionally keep neutral state keys
instead of embedding vendor menu numbers in the protocol contract.
"""

from __future__ import annotations

STATION_KEYS: dict[int, str] = {
    0: "in_service",
    1: "backwash",
    2: "brine_draw",
    3: "brine_refill",
    4: "fast_rinse",
    5: "closed",
    6: "salt_dissolving",
    7: "pause_1",
    8: "pause_2",
}

VOLUME_UNIT_KEYS: dict[int, str] = {
    0: "gallons",
    1: "liters",
    2: "cubic_meters",
}

REGENERATION_PATTERN_KEYS: dict[int, str] = {
    0: "flow",
    1: "time",
}

WORK_PATTERN_KEYS: dict[int, str] = {
    0: "downflow_meter_delayed",
    1: "downflow_meter_immediate",
    2: "downflow_intelligent_meter_delayed",
    3: "upflow_meter_delayed",
    4: "upflow_meter_immediate",
    5: "upflow_intelligent_meter_delayed",
    6: "filter_type",
    7: "meter_delayed",
    8: "meter_immediate",
    9: "intelligent_meter_delayed",
}
