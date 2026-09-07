"""Home Assistant/Ypsilon integration policy constants.

Protocol field definitions live in `runxin/`; BroadLink retry/session constants
live in `transport/broadlink_bl3372.py`. This module intentionally contains the
Home Assistant-facing compatibility gates, polling policy and safe-write policy.
"""

from datetime import timedelta
from typing import Final

DOMAIN: Final = "ypsilon_local"

CONF_SCAN_INTERVAL: Final = "scan_interval"
DEFAULT_SCAN_INTERVAL: Final = 60
MIN_SCAN_INTERVAL: Final = 15
MAX_SCAN_INTERVAL: Final = 3600
UPDATE_INTERVAL: Final = timedelta(seconds=DEFAULT_SCAN_INTERVAL)

# Hardware combination supported by this Home Assistant integration. The pure
# Runxin/F79D codec can be reused independently of these gates.
SUPPORTED_DEVICE_MODEL: Final = 9
EXPECTED_DEVTYPE: Final = 0x520F  # compatibility/documentation alias
MODEL_NAME: Final = "Ypsilon G6"
MANUFACTURER: Final = "ATH / BWT / Runxin"

FIELD52_REFRESH: Final = 3600
FIELD52_FAIL_BACKOFF: Final = 300
MAX_TOLERATED_FAILURES: Final = 3

# Adaptive polling. The softener is idle almost all the time, but while water
# is running or a regeneration is under way the interesting values change by
# the second, so the coordinator temporarily speeds up.
CONF_ACTIVE_SCAN_INTERVAL: Final = "active_scan_interval"
DEFAULT_ACTIVE_SCAN_INTERVAL: Final = 10
MIN_ACTIVE_SCAN_INTERVAL: Final = 5
CONF_ADAPTIVE_POLLING: Final = "adaptive_polling"
DEFAULT_ADAPTIVE_POLLING: Final = True
ACTIVE_LINGER_SECONDS: Final = 60

# Ypsilon integration write/reconciliation timing. The protocol/client layer
# does not equate an ACK with physical confirmation; HA performs read-back.
WRITE_SETTLE_DELAY: Final = 0.5
WRITE_VERIFY_TIMEOUT: Final = 5.0
WRITE_VERIFY_INTERVAL: Final = 0.5
MECHANICAL_VERIFY_TIMEOUT: Final = 15.0
MECHANICAL_VERIFY_INTERVAL: Final = 1.0

# Field 11 is a raw big-endian 16-bit counter in hundredths of the unit selected
# by waterVolumeUnit. Only cubic-metre mode (2) has been calibrated against the
# official app on real hardware; the raw value is always exposed for diagnosis.
FLOW_RATE_SCALE_BY_UNIT: Final = {
    0: 0.01,  # gallons - unverified
    1: 0.01,  # litres - unverified
    2: 0.01,  # cubic metres - confirmed
}
FLOW_RATE_SCALE_DEFAULT: Final = 0.01

# F79D field ids referenced directly by HA entities/services. Canonical field
# names/codecs are documented declaratively in runxin/fields.py.
FIELD_CURRENT_TIME: Final = 4
FIELD_WASH_INITIATION_TIME: Final = 5
FIELD_REGENERATING_TRIGGER_TIME: Final = 10
FIELD_SYSTEM_MODE: Final = 34
FIELD_SALT_ADDITION: Final = 43
FIELD_RAW_WATER_HARDNESS: Final = 47
FIELD_HOLIDAY_MODE: Final = 49

SERVICE_WRITE_FIELDS: Final = "write_fields"
SERVICE_ADVANCE_PHASE: Final = "advance_phase"

# HA's advanced raw-write service is deliberately narrower than everything the
# legacy codec knows how to serialise. Field 5 stays read-only in HA because the
# original application does not expose it as a writable setting. Unknown or
# insufficiently understood writes are refused rather than guessed.
WRITABLE_FIELDS: Final = frozenset(
    {
        FIELD_CURRENT_TIME,
        FIELD_REGENERATING_TRIGGER_TIME,
        FIELD_SYSTEM_MODE,
        FIELD_SALT_ADDITION,
        FIELD_RAW_WATER_HARDNESS,
        FIELD_HOLIDAY_MODE,
        6,  # continuousWaterTime
        7,  # flowRateOff
    }
)

# Automatic clock sync. The valve keeps its own clock and does not apply local
# daylight-saving rules, so HA can reconcile it when drift exceeds tolerance.
CONF_AUTO_SYNC_CLOCK: Final = "auto_sync_clock"
DEFAULT_AUTO_SYNC_CLOCK: Final = True
CONF_CLOCK_TOLERANCE: Final = "clock_tolerance_minutes"
DEFAULT_CLOCK_TOLERANCE: Final = 2
MIN_CLOCK_TOLERANCE: Final = 1
MAX_CLOCK_TOLERANCE: Final = 60
CLOCK_SYNC_RETRY_SECONDS: Final = 900

# User-actionable alerts. Hardware self-test faults remain diagnostics instead
# of becoming noisy notification conditions.
ALERT_FIELDS: Final = (
    ("saltShortageAlarm", "salt_shortage_alarm"),
    ("saltShortageReminder", "salt_shortage_reminder"),
    ("resinReplacementReminder", "resin_replacement"),
    ("filterMaterialReminder", "filter_reminder"),
)
