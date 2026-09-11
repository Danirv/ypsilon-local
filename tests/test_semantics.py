"""Regression tests for F79D semantic mappings."""

from __future__ import annotations

from .helpers import load

semantics = load("runxin.semantics")


def test_work_pattern_mapping_matches_legacy_app() -> None:
    assert semantics.WORK_PATTERN_KEYS == {
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


def test_regeneration_pattern_stable_states_are_backwards_compatible() -> None:
    assert semantics.REGENERATION_PATTERN_KEYS == {0: "flow", 1: "time"}


def test_known_volume_unit_mapping_is_stable() -> None:
    assert semantics.VOLUME_UNIT_KEYS == {0: "gallons", 1: "liters", 2: "cubic_meters"}


def test_system_close_reason_mapping_matches_legacy_ui() -> None:
    assert semantics.SYSTEM_CLOSE_REASON_KEYS == {
        257: "manual_close",
        513: "leak_detected",
        769: "continuous_flow_timeout",
        1025: "flow_rate_exceeded",
    }


def test_vacation_semantics_preserve_raw_station_context() -> None:
    assert semantics.vacation_status(False, 0) == "off"
    assert semantics.vacation_status(True, 3) == "preparing"
    assert semantics.vacation_status(True, 8) == "active"
    assert semantics.vacation_status(None, 8) is None
