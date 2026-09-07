"""Runxin F79D field codec built on the transport-neutral frame layer."""

from __future__ import annotations

from typing import Any

from .errors import F79DProtocolError
from .fields import F79D_FIELDS_BY_ID, F79D_FIELD_SPECS, FieldCodec
from .framing import (
    QUERY_CODE,
    WRITE_CODE,
    build_control_frame,
    build_query_frame,
    extract_tlvs,
    inner_frame,
    validate_frame,
)

DEVICE_MODEL = 9
STATE_FIELDS = list(range(1, 52))

FIELD_NAMES = {spec.id: spec.name for spec in F79D_FIELD_SPECS}
CLOCK_FIELDS = {
    spec.id for spec in F79D_FIELD_SPECS if spec.read_codec is FieldCodec.TIME_HM
}
DURATION_FIELDS = {
    spec.id for spec in F79D_FIELD_SPECS if spec.read_codec is FieldCodec.DURATION_MIN_SEC
}
LE16_FIELDS = {
    spec.id for spec in F79D_FIELD_SPECS if spec.read_codec is FieldCodec.U16_LE
}
BE16_FIELDS = {
    spec.id for spec in F79D_FIELD_SPECS if spec.read_codec is FieldCodec.U16_BE
}
HUNDREDTHS_FIELDS = {7, 11}
BOOL_FIELDS = {
    spec.id for spec in F79D_FIELD_SPECS if spec.read_codec is FieldCodec.BOOL
}
VOLUME_FIELDS = {
    spec.id: spec.name
    for spec in F79D_FIELD_SPECS
    if spec.read_codec is FieldCodec.VOLUME_PAIR
}

WRITE_SIMPLE = {
    spec.id
    for spec in F79D_FIELD_SPECS
    if spec.write_codec is FieldCodec.U8
}
WRITE_U16 = {
    spec.id
    for spec in F79D_FIELD_SPECS
    if spec.write_codec is FieldCodec.U16_LE
}
WRITE_U16_BE = {
    spec.id
    for spec in F79D_FIELD_SPECS
    if spec.write_codec is FieldCodec.U16_BE
}
WRITE_TIME = {
    spec.id
    for spec in F79D_FIELD_SPECS
    if spec.write_codec is FieldCodec.TIME_HM
}


def build_query(fields: list[int]) -> bytes:
    """Build an F79D 0x09 field query."""
    return build_query_frame(fields)


def build_write(field: int, low: int, high: int = 0) -> bytes:
    """Build one raw three-byte F79D control group.

    This helper preserves the original research API. New code should normally
    use `build_write_fields()` so the field catalogue chooses the encoding.
    """
    if not 0 <= field <= 0xFF or not 0 <= low <= 0xFF or not 0 <= high <= 0xFF:
        raise ValueError("values must fit in one byte")
    return build_control_frame([field, low, high])


def encode_field(field: int, value: Any) -> list[int]:
    """Serialise one field into the legacy three-byte payload group."""
    spec = F79D_FIELDS_BY_ID.get(field)
    codec = spec.write_codec if spec is not None else None

    # Compatibility fallback used by research tooling. Home Assistant applies
    # a separate safe-write whitelist before calling the codec.
    if codec is None:
        codec = FieldCodec.U8

    if codec is FieldCodec.TIME_HM:
        try:
            hour, minute = value
        except (TypeError, ValueError) as err:
            raise ValueError(f"field {field} requires (hour, minute)") from err
        if not 0 <= int(hour) <= 23 or not 0 <= int(minute) <= 59:
            raise ValueError(f"invalid time {hour}:{minute} for field {field}")
        return [field, int(hour), int(minute)]

    number = int(value)
    if codec is FieldCodec.U16_BE:
        if not 0 <= number <= 0xFFFF:
            raise ValueError(f"value {number} out of u16 range for field {field}")
        return [field, (number >> 8) & 0xFF, number & 0xFF]
    if codec is FieldCodec.U16_LE:
        if not 0 <= number <= 0xFFFF:
            raise ValueError(f"value {number} out of u16 range for field {field}")
        return [field, number & 0xFF, (number >> 8) & 0xFF]
    if codec is FieldCodec.U8:
        if not 0 <= number <= 0xFF:
            raise ValueError(f"value {number} out of byte range for field {field}")
        return [field, number, 0]

    raise ValueError(f"field {field} has unsupported write codec {codec.value}")


def build_control(payload: list[int]) -> bytes:
    """Wrap serialised F79D field groups in a 0x19 control frame."""
    return build_control_frame(payload)


def build_write_fields(values: dict[int, Any]) -> bytes:
    """Build one 0x19 frame writing one or more fields."""
    payload: list[int] = []
    for field in sorted(values):
        payload += encode_field(field, values[field])
    return build_control(payload)


def _clock(low: int, high: int) -> str | None:
    """Format a time-of-day field, rejecting impossible controller values."""
    if not (0 <= low <= 23 and 0 <= high <= 59):
        return None
    return f"{low:02d}:{high:02d}:00"


def _duration(low: int, high: int) -> str:
    """Decode the legacy minutes/seconds duration pair as HH:MM:SS."""
    total = low * 60 + high
    hours, remainder = divmod(total, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def decode_tlvs(tlvs: dict[int, tuple[int, int]]) -> dict[str, Any]:
    """Decode F79D field groups into stable legacy field names."""
    decoded: dict[str, Any] = {}
    for field, (low, high) in tlvs.items():
        spec = F79D_FIELDS_BY_ID.get(field)
        name = spec.name if spec is not None else f"field_{field}"
        codec = spec.read_codec if spec is not None else FieldCodec.U8

        if codec is FieldCodec.CONTINUATION:
            continue
        if codec is FieldCodec.TIME_HM:
            value: Any = _clock(low, high)
        elif codec is FieldCodec.DURATION_MIN_SEC:
            value = _duration(low, high)
        elif codec is FieldCodec.U16_LE:
            value = low | high << 8
        elif codec is FieldCodec.U16_BE:
            value = low << 8 | high
            if field in HUNDREDTHS_FIELDS:
                # Keep the untouched counter for calibration/debugging. The HA
                # entity layer applies the selected water-unit scale.
                decoded[f"_raw_{name}"] = value
        elif codec is FieldCodec.BOOL:
            value = bool(low)
        elif codec is FieldCodec.VOLUME_PAIR:
            # The four water-volume values each span a base field plus the next
            # continuation field. Without the continuation the value is unknown.
            if field + 1 not in tlvs:
                decoded[name] = None
                continue
            next_low, next_high = tlvs[field + 1]
            packed = next_high + next_low * 100 + high * 10_000
            value = packed / 100
        elif codec is FieldCodec.REMINDER_FLAGS:
            decoded["saltShortageReminder"] = bool(low)
            decoded["filterMaterialReminder"] = bool(high)
            continue
        else:
            value = low
        decoded[name] = value

    return decoded


def decode_frame(frame: bytes) -> dict[str, Any]:
    """Validate and decode one raw Runxin/F79D response frame."""
    return decode_tlvs(extract_tlvs(frame))


# Original private helper name kept for protocol-regression compatibility.
_inner_frame = inner_frame

__all__ = [
    "DEVICE_MODEL",
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
    "validate_frame",
    "extract_tlvs",
    "decode_tlvs",
    "decode_frame",
    "_inner_frame",
]
