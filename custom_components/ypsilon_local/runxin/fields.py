"""Declarative field catalogue for the Runxin F79D profile.

The catalogue is intentionally data-first. Field meaning, wire encoding and
research evidence live together so future device profiles can reuse the frame
codec without copying a pile of field-id conditionals.

`LEGACY_APP_CODEC` means the field/encoding was recovered from the legacy
WaterDevice product codec. It does *not* mean every field has been exercised
on every valve firmware.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class FieldCodec(str, Enum):
    U8 = "u8"
    U16_LE = "u16_le"
    U16_BE = "u16_be"
    TIME_HM = "time_hm"
    DURATION_MIN_SEC = "duration_min_sec"
    BOOL = "bool"
    VOLUME_PAIR = "volume_pair"
    CONTINUATION = "continuation"
    REMINDER_FLAGS = "reminder_flags"


class Evidence(str, Enum):
    LEGACY_APP_CODEC = "legacy_app_codec"
    DEVICE_STATE_OBSERVED = "device_state_observed"
    HARDWARE_WRITE_VERIFIED = "hardware_write_verified"
    CLOUD_WRITE_OBSERVED = "cloud_write_observed"
    INFERRED = "inferred"


@dataclass(frozen=True, slots=True)
class FieldSpec:
    id: int
    name: str
    read_codec: FieldCodec = FieldCodec.U8
    write_codec: FieldCodec | None = None
    evidence: tuple[Evidence, ...] = (Evidence.LEGACY_APP_CODEC,)
    unit_hint: str | None = None
    notes: str | None = None


APP = (Evidence.LEGACY_APP_CODEC,)
OBSERVED = (Evidence.LEGACY_APP_CODEC, Evidence.DEVICE_STATE_OBSERVED)
HW_WRITE = (
    Evidence.LEGACY_APP_CODEC,
    Evidence.DEVICE_STATE_OBSERVED,
    Evidence.HARDWARE_WRITE_VERIFIED,
)
SALT_HW_CLOUD_WRITE = (
    Evidence.LEGACY_APP_CODEC,
    Evidence.DEVICE_STATE_OBSERVED,
    Evidence.HARDWARE_WRITE_VERIFIED,
    Evidence.CLOUD_WRITE_OBSERVED,
)


F79D_FIELD_SPECS: tuple[FieldSpec, ...] = (
    FieldSpec(1, "deviceModel", evidence=OBSERVED),
    FieldSpec(2, "language", write_codec=FieldCodec.U8),
    FieldSpec(3, "deviceTimeScheme"),
    FieldSpec(4, "currentTime", FieldCodec.TIME_HM, FieldCodec.TIME_HM, evidence=HW_WRITE),
    FieldSpec(5, "washInitiationTime", FieldCodec.TIME_HM, FieldCodec.TIME_HM),
    FieldSpec(6, "continuousWaterTime", write_codec=FieldCodec.U8, evidence=HW_WRITE, unit_hint="min"),
    FieldSpec(7, "flowRateOff", FieldCodec.U16_BE, FieldCodec.U16_BE, evidence=HW_WRITE,
              notes="Hundredths of the selected flow unit."),
    FieldSpec(8, "waterVolumeUnit", evidence=OBSERVED),
    FieldSpec(9, "workPattern", write_codec=FieldCodec.U8, evidence=OBSERVED,
              notes="Legacy WaterDevice enum codes 0..9; exposed read-only by HA."),
    FieldSpec(10, "regeneratingTriggerTime", FieldCodec.TIME_HM, FieldCodec.TIME_HM, evidence=HW_WRITE),
    FieldSpec(11, "flowRate", FieldCodec.U16_BE, evidence=OBSERVED,
              notes="Hundredths of the selected flow unit; raw counter is preserved."),
    FieldSpec(12, "systemCloseReason", FieldCodec.U16_LE),
    FieldSpec(13, "washingIncreaseNumber", write_codec=FieldCodec.U8),
    FieldSpec(14, "backWashIntervalNumber", write_codec=FieldCodec.U8),
    FieldSpec(15, "backWashTime", FieldCodec.DURATION_MIN_SEC, FieldCodec.DURATION_MIN_SEC),
    FieldSpec(16, "backWashTimeRemaining", FieldCodec.DURATION_MIN_SEC),
    FieldSpec(17, "absorbSaltSlowWashTime", FieldCodec.DURATION_MIN_SEC, FieldCodec.DURATION_MIN_SEC),
    FieldSpec(18, "absorbSaltTimeRemaining", FieldCodec.DURATION_MIN_SEC),
    FieldSpec(19, "saltTankRefillTime", FieldCodec.DURATION_MIN_SEC, FieldCodec.DURATION_MIN_SEC),
    FieldSpec(20, "saltTankRefillTimeRemaining", FieldCodec.DURATION_MIN_SEC),
    FieldSpec(21, "washTime", FieldCodec.DURATION_MIN_SEC, FieldCodec.DURATION_MIN_SEC),
    FieldSpec(22, "washCountdownTime", FieldCodec.DURATION_MIN_SEC),
    FieldSpec(23, "maximumRegenerationIntervalDay", write_codec=FieldCodec.U8, unit_hint="day"),
    FieldSpec(24, "outRelayMode", write_codec=FieldCodec.U8),
    FieldSpec(25, "regenerationAlarmNumber", FieldCodec.U16_LE, FieldCodec.U16_LE),
    FieldSpec(26, "resinVolume", unit_hint="L", evidence=OBSERVED),
    FieldSpec(27, "clockChipFault", FieldCodec.BOOL),
    FieldSpec(28, "multiplePositionSignalFault", FieldCodec.BOOL),
    FieldSpec(29, "noPositionSignalFault", FieldCodec.BOOL),
    FieldSpec(30, "memoryErrorFault", FieldCodec.BOOL),
    FieldSpec(31, "saltShortageAlarm", FieldCodec.BOOL),
    FieldSpec(32, "resinReplacementReminder", FieldCodec.BOOL),
    FieldSpec(33, "reminderFlags", FieldCodec.REMINDER_FLAGS),
    FieldSpec(34, "station", write_codec=FieldCodec.U8, evidence=OBSERVED),
    FieldSpec(35, "residualWaterProduction", FieldCodec.VOLUME_PAIR, evidence=OBSERVED,
              notes="Uses field 36 as its continuation."),
    FieldSpec(36, "residualWaterProductionContinuation", FieldCodec.CONTINUATION),
    FieldSpec(37, "dailyWaterConsumption", FieldCodec.VOLUME_PAIR, evidence=OBSERVED,
              notes="Uses field 38 as its continuation."),
    FieldSpec(38, "dailyWaterConsumptionContinuation", FieldCodec.CONTINUATION),
    FieldSpec(39, "averageWeeklyWaterConsumption", FieldCodec.VOLUME_PAIR, evidence=OBSERVED,
              notes="Uses field 40 as its continuation."),
    FieldSpec(40, "averageWeeklyWaterConsumptionContinuation", FieldCodec.CONTINUATION),
    FieldSpec(41, "periodicWaterProduction", FieldCodec.VOLUME_PAIR, evidence=OBSERVED,
              notes="Uses field 42 as its continuation."),
    FieldSpec(42, "periodicWaterProductionContinuation", FieldCodec.CONTINUATION),
    FieldSpec(43, "saltAddition", write_codec=FieldCodec.U8, evidence=SALT_HW_CLOUD_WRITE, unit_hint="kg"),
    FieldSpec(44, "operationDay", evidence=OBSERVED, unit_hint="day"),
    FieldSpec(45, "remainingDay", evidence=OBSERVED, unit_hint="day"),
    FieldSpec(46, "regenerationPattern", write_codec=FieldCodec.U8, evidence=OBSERVED),
    FieldSpec(47, "rawWaterHardness", FieldCodec.U16_LE, FieldCodec.U16_LE, evidence=HW_WRITE, unit_hint="mg/L"),
    FieldSpec(48, "absorbSaltMode", write_codec=FieldCodec.U8),
    FieldSpec(49, "vacationPattern", FieldCodec.BOOL, FieldCodec.U8),
    FieldSpec(50, "saltDissolutionRemainingTime", evidence=OBSERVED),
    FieldSpec(51, "pauseRemainingTime", evidence=OBSERVED),
    FieldSpec(52, "filterMaterialWorkingDay", FieldCodec.U16_LE, FieldCodec.U16_LE, evidence=OBSERVED, unit_hint="day"),
)

F79D_FIELDS_BY_ID = {spec.id: spec for spec in F79D_FIELD_SPECS}
F79D_FIELDS_BY_NAME = {spec.name: spec for spec in F79D_FIELD_SPECS}

if len(F79D_FIELDS_BY_ID) != len(F79D_FIELD_SPECS):
    raise RuntimeError("duplicate F79D field id")
if len(F79D_FIELDS_BY_NAME) != len(F79D_FIELD_SPECS):
    raise RuntimeError("duplicate F79D field name")
