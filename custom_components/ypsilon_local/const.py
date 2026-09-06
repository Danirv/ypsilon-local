"""Constants for Ypsilon Local."""

from datetime import timedelta
from typing import Final

DOMAIN: Final = "ypsilon_local"

CONF_SCAN_INTERVAL: Final = "scan_interval"
DEFAULT_SCAN_INTERVAL: Final = 60
MIN_SCAN_INTERVAL: Final = 15
MAX_SCAN_INTERVAL: Final = 3600
UPDATE_INTERVAL: Final = timedelta(seconds=DEFAULT_SCAN_INTERVAL)

SUPPORTED_DEVICE_MODEL: Final = 9  # F79D, per the Runxin codec
EXPECTED_DEVTYPE: Final = 0x520F
MODEL_NAME: Final = "Ypsilon G6"
MANUFACTURER: Final = "ATH / BWT / Runxin"

SOCKET_TIMEOUT: Final = 5
MCU_BUSY_CODE: Final = -5
AUTH_ERROR_CODES: Final = frozenset({-1, -7})
MCU_BUSY_DELAYS: Final = (0.4, 0.8)

FIELD52_REFRESH: Final = 3600
FIELD52_FAIL_BACKOFF: Final = 300
MAX_TOLERATED_FAILURES: Final = 3

# Adaptive polling. The softener is idle almost all the time, but while water
# is running or a regeneration is under way the interesting values change by
# the second, so the coordinator temporarily speeds up - the same behaviour the
# official app shows while you are watching it.
CONF_ACTIVE_SCAN_INTERVAL: Final = "active_scan_interval"
DEFAULT_ACTIVE_SCAN_INTERVAL: Final = 10
MIN_ACTIVE_SCAN_INTERVAL: Final = 5
CONF_ADAPTIVE_POLLING: Final = "adaptive_polling"
DEFAULT_ADAPTIVE_POLLING: Final = True
# Keep polling fast for a moment after flow stops, so the tail of a draw-off is
# captured instead of being cut at the next slow tick.
ACTIVE_LINGER_SECONDS: Final = 60

# Pause after a 0x19 control frame so the MCU applies the change before the
# verifying read.
WRITE_SETTLE_DELAY: Final = 0.5

# A write ACK only proves that the BL3372 accepted the F79D control frame.
# Confirmation comes from a strict read-back that must match the requested
# value. Normal settings get a short window; mechanical state changes can
# legitimately take longer while the valve motor moves.
WRITE_VERIFY_TIMEOUT: Final = 5.0
WRITE_VERIFY_INTERVAL: Final = 0.5
MECHANICAL_VERIFY_TIMEOUT: Final = 15.0
MECHANICAL_VERIFY_INTERVAL: Final = 1.0

# Field 11 (flowRate) is a raw big-endian 16-bit counter in hundredths of the
# unit the device reports through waterVolumeUnit. Calibrated against the
# official app: raw 14 is shown there as 0.14 m3/h, i.e. one count = 0.01 m3/h
# (10 L/h).
#
# Only the cubic-metre mode (code 2) is confirmed on real hardware. The other
# two modes fall back to the same hundredths assumption, which is the most
# likely behaviour but has not been observed; the flow sensor always exposes
# the untouched counter as its "raw_value" attribute so this can be checked.
FLOW_RATE_SCALE_BY_UNIT: Final = {
    0: 0.01,  # gallons - unverified
    1: 0.01,  # litres - unverified
    2: 0.01,  # cubic metres - confirmed
}
FLOW_RATE_SCALE_DEFAULT: Final = 0.01

# Field ids used by the write platforms, named after the legacy APK codec.
FIELD_CURRENT_TIME: Final = 4
FIELD_WASH_INITIATION_TIME: Final = 5
FIELD_REGENERATING_TRIGGER_TIME: Final = 10
FIELD_SYSTEM_MODE: Final = 34
FIELD_SALT_ADDITION: Final = 43
FIELD_RAW_WATER_HARDNESS: Final = 47
FIELD_HOLIDAY_MODE: Final = 49


SERVICE_WRITE_FIELDS: Final = "write_fields"
SERVICE_ADVANCE_PHASE: Final = "advance_phase"

# Only fields whose encoding is confirmed from the legacy WaterDevice codec
# may be written. Anything else is refused rather than guessed at.
WRITABLE_FIELDS: Final = frozenset(
    {
        FIELD_CURRENT_TIME,
        FIELD_WASH_INITIATION_TIME,
        FIELD_REGENERATING_TRIGGER_TIME,
        FIELD_SYSTEM_MODE,
        FIELD_SALT_ADDITION,
        FIELD_RAW_WATER_HARDNESS,
        FIELD_HOLIDAY_MODE,
        6,   # continuousWaterTime
        7,   # flowRateOff
    }
)


# Automatic clock sync. The valve keeps its own clock, drifts, and knows
# nothing about daylight saving, so twice a year it silently ends up an hour
# off and every scheduled regeneration moves with it.
CONF_AUTO_SYNC_CLOCK: Final = "auto_sync_clock"
DEFAULT_AUTO_SYNC_CLOCK: Final = True
CONF_CLOCK_TOLERANCE: Final = "clock_tolerance_minutes"
DEFAULT_CLOCK_TOLERANCE: Final = 2
MIN_CLOCK_TOLERANCE: Final = 1
MAX_CLOCK_TOLERANCE: Final = 60
# The device only stores hours and minutes, so a correction can never be more
# precise than a minute; retrying sooner would just write on every poll if the
# valve ever refuses the command.
CLOCK_SYNC_RETRY_SECONDS: Final = 900


# Fields that represent something the user should act on, in the order they
# are reported. Hardware self-tests are deliberately excluded: they belong in
# diagnostics, not in a notification at three in the morning.
ALERT_FIELDS: Final = (
    ("saltShortageAlarm", "salt_shortage_alarm"),
    ("saltShortageReminder", "salt_shortage_reminder"),
    ("resinReplacementReminder", "resin_replacement"),
    ("filterMaterialReminder", "filter_reminder"),
)
