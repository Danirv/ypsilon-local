"""Stable semantic mappings for enum-like Runxin F79D fields."""

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

SYSTEM_CLOSE_REASON_KEYS: dict[int, str] = {
    257: "manual_close",
    513: "leak_detected",
    769: "continuous_flow_timeout",
    1025: "flow_rate_exceeded",
}

VACATION_STATUS_KEYS = ("off", "preparing", "active")


def vacation_status(vacation_enabled: bool | None, station: int | None) -> str | None:
    """Return the semantic vacation state without hiding the raw valve phase."""
    if vacation_enabled is None:
        return None
    if not vacation_enabled:
        return "off"
    return "active" if station == 8 else "preparing"
