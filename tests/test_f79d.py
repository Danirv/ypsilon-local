"""Regression tests for the transport-neutral F79D codec."""

from __future__ import annotations

import pytest

from .helpers import load

f79d = load("runxin.f79d")
fields = load("runxin.fields")
framing = load("runxin.framing")


def test_exact_write_encodings_match_verified_device_behavior() -> None:
    assert f79d.encode_field(43, 50) == [43, 50, 0]
    assert f79d.encode_field(47, 400) == [47, 0x90, 0x01]
    assert f79d.encode_field(7, 200) == [7, 0x00, 0xC8]
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


def test_field7_and_field11_are_big_endian() -> None:
    decoded = f79d.decode_tlvs({7: (0x03, 0xE8), 11: (0x03, 0xE8)})
    assert decoded["flowRateOff"] == 1000
    assert decoded["_raw_flowRateOff"] == 1000
    assert decoded["flowRate"] == 1000
    assert decoded["_raw_flowRate"] == 1000


def test_field7_real_device_bytes_decode_to_10_m3h_raw() -> None:
    first, second = (0x03, 0xE8)
    assert first | (second << 8) == 59395
    assert (first << 8) | second == 1000
    assert f79d.decode_tlvs({7: (first, second)})["flowRateOff"] == 1000


def test_field7_write_2_m3h_uses_be_00_c8() -> None:
    assert f79d.encode_field(7, 200) == [7, 0x00, 0xC8]


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
    for field_id in (4, 6, 7, 10, 43, 47):
        assert evidence.HARDWARE_WRITE_VERIFIED in by_id[field_id].evidence
    for field_id in (34, 49):
        assert evidence.HARDWARE_WRITE_VERIFIED not in by_id[field_id].evidence


def test_field7_codec_sets_are_consistent() -> None:
    assert 7 in f79d.BE16_FIELDS
    assert 7 not in f79d.LE16_FIELDS
    assert 7 in f79d.WRITE_U16_BE
    assert 7 not in f79d.WRITE_U16


def test_state_block_keeps_field52_on_slow_refresh_policy() -> None:
    assert f79d.STATE_FIELDS == list(range(1, 52))
    assert 52 not in f79d.STATE_FIELDS


def test_bad_checksum_fails_closed() -> None:
    frame = bytearray(f79d.build_query([1, 34]))
    frame[-2] ^= 1
    with pytest.raises(f79d.F79DProtocolError):
        f79d.validate_frame(bytes(frame))
