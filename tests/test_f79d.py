"""Regression tests for the transport-neutral F79D codec."""

from __future__ import annotations

import pytest

from .helpers import load

f79d = load("runxin.f79d")
fields = load("runxin.fields")
framing = load("runxin.framing")


def test_exact_write_encodings_match_legacy_codec() -> None:
    assert f79d.encode_field(43, 50) == [43, 50, 0]
    assert f79d.encode_field(47, 400) == [47, 0x90, 0x01]
    # WaterDevice field 7 is little-endian; field 11 is the separately reversed
    # big-endian instantaneous-flow field.
    assert f79d.encode_field(7, 200) == [7, 0xC8, 0]
    assert f79d.encode_field(10, (2, 30)) == [10, 2, 30]
    assert f79d.encode_field(15, (12, 30)) == [15, 12, 30]


def test_clock_and_duration_are_distinct() -> None:
    assert f79d.WRITE_CLOCK == {4, 5, 10}
    assert f79d.WRITE_DURATION == {15, 17, 19, 21}
    assert f79d.WRITE_TIME == {4, 5, 10, 15, 17, 19, 21}
    with pytest.raises(ValueError):
        f79d.encode_field(4, (24, 0))
    with pytest.raises(ValueError):
        f79d.encode_field(15, (12, 60))


def test_multi_field_write_frame() -> None:
    frame = f79d.build_write_fields({43: 50, 49: 1})
    framing.validate_frame(frame)
    inner = framing.inner_frame(frame)
    assert inner[3] == framing.WRITE_CODE
    assert inner[4:-2] == bytes([43, 50, 0, 49, 1, 0])


def test_field7_is_le_and_field11_is_be() -> None:
    decoded = f79d.decode_tlvs({7: (0xE8, 0x03), 11: (0x03, 0xE8)})
    assert decoded["flowRateOff"] == 1000
    assert decoded["_raw_flowRateOff"] == 1000
    assert decoded["flowRate"] == 1000
    assert decoded["_raw_flowRate"] == 1000


def test_volume_pair_requires_unit_and_continuation() -> None:
    assert f79d.decode_tlvs({35: (0, 1), 36: (59, 2)})["residualWaterProduction"] is None
    assert f79d.decode_tlvs({8: (2, 0), 35: (0, 1)})["residualWaterProduction"] is None


def test_volume_pair_unit_2_uses_base100_and_display_scale() -> None:
    decoded = f79d.decode_tlvs({8: (2, 0), 35: (0, 1), 36: (59, 2)})
    assert decoded["residualWaterProduction"] == 159.02


def test_volume_pair_units_0_and_1_use_24bit_le() -> None:
    expected = 2 | (59 << 8) | (1 << 16)
    for unit in (0, 1):
        decoded = f79d.decode_tlvs({8: (unit, 0), 35: (0, 1), 36: (59, 2)})
        assert decoded["residualWaterProduction"] == expected


def test_hardware_write_evidence_is_conservative() -> None:
    evidence = fields.Evidence
    by_id = fields.F79D_FIELDS_BY_ID
    for field_id in (4, 6, 10, 43, 47):
        assert evidence.HARDWARE_WRITE_VERIFIED in by_id[field_id].evidence
    # 7 was previously self-confirmed with the wrong endian implementation;
    # 34 and 49 are mechanical/semantic writes still pending full HW evidence.
    for field_id in (7, 34, 49):
        assert evidence.HARDWARE_WRITE_VERIFIED not in by_id[field_id].evidence


def test_bad_checksum_fails_closed() -> None:
    frame = bytearray(f79d.build_query([1, 34]))
    frame[-2] ^= 1
    with pytest.raises(f79d.F79DProtocolError):
        f79d.validate_frame(bytes(frame))
