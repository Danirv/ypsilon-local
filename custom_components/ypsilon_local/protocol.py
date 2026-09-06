"""Runxin F79D protocol codec."""

from __future__ import annotations

from typing import Any

QUERY_CODE = 0x09
WRITE_CODE = 0x19

STATE_FIELDS = list(range(1, 52))

FIELD_NAMES = {
    1: "deviceModel", 2: "language", 3: "deviceTimeScheme", 4: "currentTime",
    5: "washInitiationTime", 6: "continuousWaterTime", 7: "flowRateOff",
    8: "waterVolumeUnit", 9: "workPattern", 10: "regeneratingTriggerTime",
    11: "flowRate", 12: "systemCloseReason", 13: "washingIncreaseNumber",
    14: "backWashIntervalNumber", 15: "backWashTime", 16: "backWashTimeRemaining",
    17: "absorbSaltSlowWashTime", 18: "absorbSaltTimeRemaining",
    19: "saltTankRefillTime", 20: "saltTankRefillTimeRemaining",
    21: "washTime", 22: "washCountdownTime", 23: "maximumRegenerationIntervalDay",
    24: "outRelayMode", 25: "regenerationAlarmNumber", 26: "resinVolume",
    27: "clockChipFault", 28: "multiplePositionSignalFault",
    29: "noPositionSignalFault", 30: "memoryErrorFault", 31: "saltShortageAlarm",
    32: "resinReplacementReminder", 33: "reminderFlags", 34: "station",
    35: "residualWaterProduction", 36: "residualWaterProductionContinuation",
    37: "dailyWaterConsumption", 38: "dailyWaterConsumptionContinuation",
    39: "averageWeeklyWaterConsumption", 40: "averageWeeklyWaterConsumptionContinuation",
    41: "periodicWaterProduction", 42: "periodicWaterProductionContinuation",
    43: "saltAddition", 44: "operationDay", 45: "remainingDay",
    46: "regenerationPattern", 47: "rawWaterHardness", 48: "absorbSaltMode",
    49: "vacationPattern", 50: "saltDissolutionRemainingTime",
    51: "pauseRemainingTime", 52: "filterMaterialWorkingDay",
}

CLOCK_FIELDS = {4, 5, 10}
DURATION_FIELDS = set(range(15, 23))
LE16_FIELDS = {12, 25, 47, 52}
# Flow-family fields: big-endian and expressed in hundredths of the unit
# reported through waterVolumeUnit. Confirmed on hardware: writing 2 as
# little-endian made the device read 0x0200 = 512 and display 5.12 m3/h.
BE16_FIELDS = {7, 11}
HUNDREDTHS_FIELDS = {7, 11}
BOOL_FIELDS = set(range(27, 33)) | {49}
VOLUME_FIELDS = {
    35: "residualWaterProduction", 37: "dailyWaterConsumption",
    39: "averageWeeklyWaterConsumption", 41: "periodicWaterProduction",
}


class F79DProtocolError(Exception):
    """Raised when a Runxin frame is invalid.

    api.YpsilonConnectionError subclasses nothing from here, so the API layer
    re-raises this as a connection error; keeping it a plain Exception would
    let it escape every handler on the write path.
    """


def _fill_sum(frame: list[int]) -> None:
    frame[-2] = sum(frame[:-2]) & 0xFF


def build_query(fields: list[int]) -> bytes:
    if not fields or any(not 0 <= value <= 0xFF for value in fields):
        raise ValueError("fields must contain byte-sized field identifiers")

    header = [0x5A, 0x5C, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0x12, 0, 0]
    inner = [0xDF, 0xFD, 0, QUERY_CODE, *fields, 0, 0xDE]
    header[15] = len(inner)
    inner[2] = len(inner)
    _fill_sum(inner)

    frame = header + inner + [0, 0xA5]
    frame[2] = len(frame)
    _fill_sum(frame)
    return bytes(frame)


def build_write(field: int, low: int, high: int = 0) -> bytes:
    if not 0 <= field <= 0xFF or not 0 <= low <= 0xFF or not 0 <= high <= 0xFF:
        raise ValueError("Valors fora de rang de byte")

    header = [0x5A, 0x5C, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0x12, 0, 0]
    inner = [0xDF, 0xFD, 0, WRITE_CODE, field, low, high, 0, 0xDE]
    header[15] = len(inner)
    inner[2] = len(inner)
    _fill_sum(inner)

    frame = header + inner + [0, 0xA5]
    frame[2] = len(frame)
    _fill_sum(frame)
    return bytes(frame)



# Encoding per field, taken from jsonToBinary() in the legacy WaterDevice APK
# (product_res/<pid>.zip -> main.*.chunk.js, webpack module 51).
#
#   "simple" -> [field, value, 0]           (addSalt, systemMode, holidayMode...)
#   "u16"    -> [field, value & 0xFF, value >> 8]
#   "u16be"  -> [field, value >> 8, value & 0xFF]   (flow-family, hundredths)
#   "time"   -> [field, hour, minute]       (NOT total minutes)
#
# Anything absent defaults to "simple", which matches the majority of fields.
WRITE_SIMPLE = {2, 6, 9, 13, 14, 23, 24, 34, 43, 46, 48, 49}
WRITE_U16 = {25, 47, 52}
WRITE_U16_BE = {7}
WRITE_TIME = {4, 5, 10, 15, 17, 19, 21}


def encode_field(field: int, value: Any) -> list[int]:
    """Serialise one field into its three payload bytes."""
    if field in WRITE_TIME:
        hour, minute = value
        if not 0 <= hour <= 23 or not 0 <= minute <= 59:
            raise ValueError(f"invalid time {hour}:{minute} for field {field}")
        return [field, hour, minute]
    if field in WRITE_U16_BE:
        value = int(value)
        if not 0 <= value <= 0xFFFF:
            raise ValueError(f"value {value} out of u16 range for field {field}")
        return [field, (value >> 8) & 0xFF, value & 0xFF]
    if field in WRITE_U16:
        value = int(value)
        if not 0 <= value <= 0xFFFF:
            raise ValueError(f"value {value} out of u16 range for field {field}")
        return [field, value & 0xFF, (value >> 8) & 0xFF]
    value = int(value)
    if not 0 <= value <= 0xFF:
        raise ValueError(f"value {value} out of byte range for field {field}")
    return [field, value, 0]


def build_control(payload: list[int]) -> bytes:
    """Wrap an already-serialised payload in a 0x19 control frame.

    The legacy codec concatenates several three-byte groups into a single
    control frame, so one write can carry multiple fields.
    """
    if not payload or len(payload) % 3:
        raise ValueError("control payload must be whole three-byte groups")

    header = [0x5A, 0x5C, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0x12, 0, 0]
    inner = [0xDF, 0xFD, 0, WRITE_CODE, *payload, 0, 0xDE]
    header[15] = len(inner)
    inner[2] = len(inner)
    _fill_sum(inner)

    frame = header + inner + [0, 0xA5]
    frame[2] = len(frame)
    _fill_sum(frame)
    return bytes(frame)


def build_write_fields(values: dict[int, Any]) -> bytes:
    """Build one 0x19 frame writing several fields at once."""
    payload: list[int] = []
    for field in sorted(values):
        payload += encode_field(field, values[field])
    return build_control(payload)


def pack_tfb(payload: bytes) -> bytes:
    return len(payload).to_bytes(2, "little") + payload


def unpack_tfb(plaintext: bytes) -> bytes:
    if len(plaintext) < 2:
        raise F79DProtocolError("missing TFB length prefix")
    declared = int.from_bytes(plaintext[:2], "little")
    if declared > len(plaintext) - 2:
        raise F79DProtocolError("declared length exceeds plaintext")
    return plaintext[2:2 + declared]


def _inner_frame(frame: bytes) -> bytes:
    start = frame.find(b"\xdf\xfd", 17)
    if start < 0 or start + 3 > len(frame):
        raise F79DProtocolError("missing DF FD")
    length = frame[start + 2]
    inner = frame[start:start + length]
    if len(inner) != length:
        raise F79DProtocolError("truncated inner frame")
    return inner


def validate_frame(frame: bytes) -> None:
    if len(frame) < 25:
        raise F79DProtocolError("frame too short")
    if frame[:2] != b"\x5a\x5c":
        raise F79DProtocolError("missing magic")
    if frame[2] != len(frame):
        raise F79DProtocolError("outer length mismatch")
    if frame[-1] != 0xA5:
        raise F79DProtocolError("missing A5")
    if frame[-2] != sum(frame[:-2]) & 0xFF:
        raise F79DProtocolError("outer checksum mismatch")

    inner = _inner_frame(frame)
    if inner[2] != len(inner):
        raise F79DProtocolError("inner length mismatch")
    if inner[-1] != 0xDE:
        raise F79DProtocolError("missing DE")
    if inner[-2] != sum(inner[:-2]) & 0xFF:
        raise F79DProtocolError("inner checksum mismatch")


def extract_tlvs(frame: bytes) -> dict[int, tuple[int, int]]:
    validate_frame(frame)
    inner = _inner_frame(frame)
    if inner[3] not in (0xC9, 0xD9):
        raise F79DProtocolError(f"unexpected response opcode 0x{inner[3]:02x}")
    data = inner[4:-2]
    if len(data) % 3:
        # A 0x19 acknowledgement is not a TLV list; the frame is already
        # checksum-validated, so report success with no fields rather than
        # raising on a perfectly good reply.
        if inner[3] == 0xD9:
            return {}
        raise F79DProtocolError("TLV data not divisible by three")
    return {
        data[offset]: (data[offset + 1], data[offset + 2])
        for offset in range(0, len(data), 3)
    }


def _clock(low: int, high: int) -> str | None:
    """Format a time-of-day field, or None if the valve reported nonsense.

    Publishing "25:70:00" would propagate a bad reading into the clock-drift
    calculation and into any automation comparing times.
    """
    if not (0 <= low <= 23 and 0 <= high <= 59):
        return None
    return f"{low:02d}:{high:02d}:00"


def _duration(low: int, high: int) -> str:
    total = low * 60 + high
    hours, remainder = divmod(total, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def decode_tlvs(tlvs: dict[int, tuple[int, int]]) -> dict[str, Any]:
    decoded: dict[str, Any] = {}
    for field, (low, high) in tlvs.items():
        if field in (36, 38, 40, 42):
            continue
        name = FIELD_NAMES.get(field, f"field_{field}")
        if field in CLOCK_FIELDS:
            value: Any = _clock(low, high)
        elif field in DURATION_FIELDS:
            value = _duration(low, high)
        elif field in LE16_FIELDS:
            value = low | high << 8
        elif field in BE16_FIELDS:
            value = low << 8 | high
            if field in HUNDREDTHS_FIELDS:
                # Scaling depends on waterVolumeUnit, which the entity layer
                # knows about; keep the raw counter here and convert there.
                decoded[f"_raw_{name}"] = value
        elif field in BOOL_FIELDS:
            value = bool(low)
        elif field in VOLUME_FIELDS:
            # Volumes span two consecutive fields. Without the second half the
            # value is unknowable, and reporting 0 would look like an empty
            # tank rather than a missing reading.
            if field + 1 not in tlvs:
                decoded[name] = None
                continue
            next_low, next_high = tlvs[field + 1]
            packed = next_high + next_low * 100 + high * 10_000
            value = packed / 100
        elif field == 33:
            decoded["saltShortageReminder"] = bool(low)
            decoded["filterMaterialReminder"] = bool(high)
            continue
        else:
            value = low
        decoded[name] = value

    return decoded


def decode_reply(plaintext: bytes) -> dict[str, Any]:
    return decode_tlvs(extract_tlvs(unpack_tfb(plaintext)))