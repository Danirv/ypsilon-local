"""Static regressions for vacation and advanced-write policy.

These checks deliberately avoid importing Home Assistant so they remain part of
the lightweight offline test job.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "ypsilon_local"
COORDINATOR = (INTEGRATION / "coordinator.py").read_text()
CONST = (INTEGRATION / "const.py").read_text()
SERVICES = (INTEGRATION / "services.py").read_text()


def test_stable_vacation_does_not_force_fast_polling() -> None:
    assert 'data.get("vacationPattern") and station == 8' in COORDINATOR
    assert "return False" in COORDINATOR


def test_vacation_entry_and_exit_have_explicit_station_guards() -> None:
    assert "async_set_vacation_mode" in COORDINATOR
    assert "if station != 0:" in COORDINATOR
    assert "vacation_enable_invalid_state" in COORDINATOR
    assert "if station != 8:" in COORDINATOR
    assert "vacation_disable_invalid_state" in COORDINATOR


def test_generic_write_service_cannot_bypass_mechanical_controls() -> None:
    writable_block = CONST.split("WRITABLE_FIELDS", 1)[1].split(")\n", 1)[0]
    assert "FIELD_SYSTEM_MODE" not in writable_block
    assert "FIELD_HOLIDAY_MODE" not in writable_block
    assert "_validate_raw_fields" in SERVICES
    assert "FIELD_FLOW_RATE_OFF" in SERVICES
