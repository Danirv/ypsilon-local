"""Regressions for vacation-state evidence and Home Assistant policy.

The recovered WaterDevice codec can encode field 49, but the tested Ypsilon G6
ACKed a direct local write without changing read-back state. Home Assistant must
therefore keep vacation status read-only until a current-firmware local action is
physically verified.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "ypsilon_local"
COORDINATOR = (INTEGRATION / "coordinator.py").read_text()
CONST = (INTEGRATION / "const.py").read_text()
INIT = (INTEGRATION / "__init__.py").read_text()
SERVICES = (INTEGRATION / "services.py").read_text()
FIELDS = (INTEGRATION / "runxin" / "fields.py").read_text()


def test_stable_observed_vacation_does_not_force_fast_polling() -> None:
    assert 'data.get("vacationPattern") and station == 8' in COORDINATOR
    assert "return False" in COORDINATOR


def test_vacation_is_read_only_in_home_assistant() -> None:
    assert "Platform.SWITCH" not in INIT
    assert not (INTEGRATION / "switch.py").exists()
    assert "async_set_vacation_mode" not in COORDINATOR
    assert "FIELD_HOLIDAY_MODE" not in COORDINATOR


def test_codec_keeps_field49_research_semantics_without_hw_claim() -> None:
    assert 'FieldSpec(49, "vacationPattern", FieldCodec.BOOL, FieldCodec.U8' in FIELDS
    assert "direct local writes are not hardware-verified" in FIELDS


def test_generic_write_service_cannot_write_vacation_or_mechanical_fields() -> None:
    writable_block = CONST.split("WRITABLE_FIELDS", 1)[1].split(")\n", 1)[0]
    assert "FIELD_SYSTEM_MODE" not in writable_block
    assert "FIELD_HOLIDAY_MODE" not in writable_block
    assert "_validate_raw_fields" in SERVICES
    assert "FIELD_FLOW_RATE_OFF" in SERVICES
