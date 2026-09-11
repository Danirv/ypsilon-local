"""Regressions for water-counter semantics recovered from codec and hardware.

No private device history is stored here. The small synthetic sequences mirror
the observed shape: field 37 rises within a day and resets at the day boundary.
"""

from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "ypsilon_local"
SENSOR = (INTEGRATION / "sensor.py").read_text()
FIELDS = (INTEGRATION / "runxin" / "fields.py").read_text()


def _block(key: str) -> str:
    match = re.search(
        rf'YpsilonSensorDescription\((?:(?!YpsilonSensorDescription).)*?'
        rf'key="{re.escape(key)}"(?P<body>.*?)\n    \),',
        SENSOR,
        re.S,
    )
    assert match is not None, f"missing sensor description: {key}"
    return match.group(0)


def _positive_meter_delta(samples: list[float]) -> float:
    """Model TOTAL_INCREASING semantics: a decrease starts a new meter cycle."""
    total = 0.0
    previous = samples[0]
    for value in samples[1:]:
        if value >= previous:
            total += value - previous
        else:
            total += value
        previous = value
    return round(total, 3)


def test_daily_counter_reset_does_not_create_negative_consumption() -> None:
    # End of day 0.44 -> next day reset -> next draws to 0.35.
    samples = [0.40, 0.44, 0.00, 0.03, 0.12, 0.35]
    assert _positive_meter_delta(samples) == 0.39
    assert "SensorStateClass.TOTAL_INCREASING" in _block("daily_water")


def test_weekly_average_is_controller_aggregate_not_week_total() -> None:
    block = _block("weekly_average")
    assert "state_class=" not in block
    assert "controller-reported weekly average" in FIELDS
    assert "week-history total" in FIELDS


def test_periodic_capacity_is_not_a_cumulative_meter() -> None:
    block = _block("periodic_water")
    assert "state_class=" not in block
    assert "water-treatment/cycle capacity" in FIELDS


def test_salt_addition_is_bookkeeping_not_level_sensor() -> None:
    assert "not a measured remaining salt level" in FIELDS
    assert 'FieldSpec(43, "saltAddition"' in FIELDS
