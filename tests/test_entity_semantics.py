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
