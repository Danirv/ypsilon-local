"""Static regressions for Home Assistant entity semantics.

This file intentionally avoids importing Home Assistant so the checks can run
in the lightweight offline test job.
"""

from __future__ import annotations

from pathlib import Path
import re

SENSOR = (
    Path(__file__).resolve().parents[1]
    / "custom_components"
    / "ypsilon_local"
    / "sensor.py"
).read_text()
SWITCH = (
    Path(__file__).resolve().parents[1]
    / "custom_components"
    / "ypsilon_local"
    / "switch.py"
).read_text()


def _block(key: str) -> str:
    match = re.search(
        rf'YpsilonSensorDescription\((?:(?!YpsilonSensorDescription).)*?'
        rf'key="{re.escape(key)}"(?P<body>.*?)\n    \),',
        SENSOR,
        re.S,
    )
    assert match is not None, f"missing sensor description: {key}"
    return match.group(0)


def test_water_state_classes_match_home_assistant_semantics() -> None:
    assert "SensorStateClass.MEASUREMENT" in _block("flow_rate")
    assert "SensorStateClass.TOTAL_INCREASING" in _block("daily_water")
    assert "SensorStateClass.MEASUREMENT" in _block("residual_water")
    assert "state_class=" not in _block("weekly_average")
    assert "state_class=" not in _block("periodic_water")


def test_work_pattern_is_read_only_enum_sensor() -> None:
    block = _block("work_pattern")
    assert "SensorDeviceClass.ENUM" in block
    assert "WORK_PATTERN_KEYS" in block
    assert 'field="workPattern"' in block


def test_vacation_status_is_primary_enum_and_switch_is_not_config_entity() -> None:
    block = _block("vacation_status")
    assert "SensorDeviceClass.ENUM" in block
    assert "VACATION_STATUS_KEYS" in block
    assert "EntityCategory" not in block
    assert "_attr_entity_category" not in SWITCH


def test_phase_50_and_51_sensors_are_diagnostics_in_minutes() -> None:
    for key in ("salt_dissolution_remaining", "pause_1_remaining"):
        block = _block(key)
        assert "EntityCategory.DIAGNOSTIC" in block
        assert "UnitOfTime.MINUTES" in block


def test_legacy_flow_unit_is_liters_per_minute() -> None:
    assert "UnitOfVolumeFlowRate.LITERS_PER_MINUTE" in SENSOR
    assert "UnitOfVolumeFlowRate.LITERS_PER_HOUR" not in SENSOR
