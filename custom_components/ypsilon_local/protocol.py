"""Compatibility facade for the pre-v2.4 single-file F79D codec.

New code should import from `ypsilon_local.runxin` / `ypsilon_local.runxin.f79d`.
The reusable implementation there has no BroadLink or Home Assistant imports.
This module intentionally keeps the old symbol names so upgrades do not break
internal callers or third-party research scripts that imported `protocol.py`.
"""

from __future__ import annotations

from .runxin.f79d import (
    BE16_FIELDS,
    BOOL_FIELDS,
    CLOCK_FIELDS,
    DURATION_FIELDS,
    FIELD_NAMES,
    HUNDREDTHS_FIELDS,
    LE16_FIELDS,
    QUERY_CODE,
    STATE_FIELDS,
    VOLUME_FIELDS,
    WRITE_CODE,
    WRITE_SIMPLE,
    WRITE_TIME,
    WRITE_U16,
    WRITE_U16_BE,
    F79DProtocolError,
    _inner_frame,
    build_control,
    build_query,
    build_write,
    build_write_fields,
    decode_frame,
    decode_tlvs,
    encode_field,
    extract_tlvs,
    validate_frame,
)


def pack_tfb(payload: bytes) -> bytes:
    """Legacy BL3372 envelope helper retained for import compatibility."""
    return len(payload).to_bytes(2, "little") + payload


def unpack_tfb(plaintext: bytes) -> bytes:
    """Legacy BL3372 envelope helper retained for import compatibility."""
    if len(plaintext) < 2:
        raise F79DProtocolError("missing TFB length prefix")
    declared = int.from_bytes(plaintext[:2], "little")
    if declared > len(plaintext) - 2:
        raise F79DProtocolError("declared length exceeds plaintext")
    return plaintext[2:2 + declared]


def decode_reply(plaintext: bytes):
    """Decode the old BL3372 plaintext shape used by v2.3 and earlier."""
    return decode_frame(unpack_tfb(plaintext))


__all__ = [
    "STATE_FIELDS",
    "FIELD_NAMES",
    "CLOCK_FIELDS",
    "DURATION_FIELDS",
    "LE16_FIELDS",
    "BE16_FIELDS",
    "HUNDREDTHS_FIELDS",
    "BOOL_FIELDS",
    "VOLUME_FIELDS",
    "WRITE_SIMPLE",
    "WRITE_U16",
    "WRITE_U16_BE",
    "WRITE_TIME",
    "QUERY_CODE",
    "WRITE_CODE",
    "F79DProtocolError",
    "build_query",
    "build_write",
    "encode_field",
    "build_control",
    "build_write_fields",
    "pack_tfb",
    "unpack_tfb",
    "validate_frame",
    "extract_tlvs",
    "decode_tlvs",
    "decode_reply",
    "_inner_frame",
]
