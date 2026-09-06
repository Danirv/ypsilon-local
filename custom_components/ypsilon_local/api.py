"""Blocking local API for the Ypsilon G6."""

from __future__ import annotations

import logging
import random
import threading
import time
from typing import Any

import broadlink
import broadlink.exceptions

from .const import (
    AUTH_ERROR_CODES,
    EXPECTED_DEVTYPE,
    FIELD52_FAIL_BACKOFF,
    FIELD52_REFRESH,
    MCU_BUSY_CODE,
    MCU_BUSY_DELAYS,
    SOCKET_TIMEOUT,
    WRITE_SETTLE_DELAY,
)
from .protocol import (
    STATE_FIELDS,
    F79DProtocolError,
    build_query,
    build_write_fields,
    decode_reply,
    pack_tfb,
)

_LOGGER = logging.getLogger(__name__)

TRANSPORT_ERRORS = (broadlink.exceptions.BroadlinkException, OSError, TimeoutError)


class YpsilonConnectionError(Exception):
    """Raised when the local BroadLink transport fails."""


class YpsilonWriteNotConfirmed(YpsilonConnectionError):
    """The control frame was accepted but read-back did not confirm it."""


class YpsilonOuterError(YpsilonConnectionError):
    """BroadLink outer response error (offset 0x22)."""

    def __init__(self, code: int) -> None:
        self.code = code
        super().__init__(f"BroadLink outer error {code}")


class YpsilonLocalClient:
    """Authenticated client for one BL3372/F79D."""

    def __init__(self, host: str) -> None:
        self.host = host
        self._device: Any = None
        self._lock = threading.Lock()
        # Diagnostics, read by the coordinator and never reset here.
        self.transient_retries = 0
        self.reauth_count = 0
        self._firmware: int | None = None

    @property
    def mac(self) -> str | None:
        """Return the device MAC as a plain 12-char hex string, or None.

        python-broadlink stores this as bytes, but some forks hand back a
        string; normalising here keeps every caller from having to guess.
        """
        raw = getattr(self._device, "mac", None) if self._device else None
        if raw is None:
            return None
        if isinstance(raw, (bytes, bytearray)):
            return raw.hex()
        return str(raw).replace(":", "").replace("-", "").lower()

    @property
    def firmware(self) -> int | None:
        """Firmware version of the BL3372 module, if already read."""
        return self._firmware

    def close(self) -> None:
        """Drop the session so the next call authenticates from scratch."""
        device = self._device
        self._device = None
        socket = getattr(device, "sock", None) if device else None
        if socket is not None:
            try:
                socket.close()
            except OSError:
                pass

    # -- transport ---------------------------------------------------------

    def _connect(self) -> Any:
        device = broadlink.hello(self.host, timeout=SOCKET_TIMEOUT)
        if device is None:
            raise YpsilonConnectionError("No device found")
        if int(device.devtype) != EXPECTED_DEVTYPE:
            raise YpsilonConnectionError(
                f"Unexpected devtype 0x{int(device.devtype):04x}"
            )
        device.timeout = SOCKET_TIMEOUT
        if device.auth() is False:
            raise YpsilonConnectionError("Auth failed")
        self._device = device
        if self._firmware is None:
            # Cheap, module-level call; surfaces as sw_version in the UI.
            try:
                self._firmware = int(device.get_fwversion())
            except Exception:  # noqa: BLE001 - purely cosmetic metadata
                self._firmware = None
        return device

    def _query_once(self, payload: bytes) -> dict[str, Any]:
        device = self._device or self._connect()
        response = bytes(device.send_packet(0x6A, pack_tfb(payload)))
        if len(response) < 0x38:
            raise YpsilonConnectionError("Short response")
        error = int.from_bytes(response[0x22:0x24], "little", signed=True)
        if error:
            raise YpsilonOuterError(error)
        encrypted = response[0x38:]
        if not encrypted or len(encrypted) % 16:
            raise YpsilonConnectionError("Invalid encrypted length")
        return decode_reply(device.decrypt(encrypted))

    def _execute_resilient(self, payload: bytes) -> dict[str, Any]:
        """Retry policy that distinguishes a busy MCU from a stale session.

        -5 means the valve micro is servicing its own cloud-report loop over
        the shared UART: reconnecting would only add contention, so we wait a
        short jittered moment and retry on the same session. -1/-7 mean the
        control key expired, which does need a fresh auth.
        """
        reauthed = False
        for attempt in range(len(MCU_BUSY_DELAYS) + 1):
            try:
                return self._query_once(payload)
            except YpsilonOuterError as err:
                if err.code in AUTH_ERROR_CODES and not reauthed:
                    reauthed = True
                    self.reauth_count += 1
                    self._device = None
                    continue
                if err.code == MCU_BUSY_CODE and attempt < len(MCU_BUSY_DELAYS):
                    self.transient_retries += 1
                    base = MCU_BUSY_DELAYS[attempt]
                    time.sleep(base + random.uniform(0, base / 2))
                    continue
                raise
        raise AssertionError("unreachable")

    def _guarded(self, payload: bytes) -> dict[str, Any]:
        """Run one transaction, normalising every failure mode."""
        try:
            return self._execute_resilient(payload)
        except YpsilonConnectionError:
            self._device = None
            raise
        except F79DProtocolError as err:
            # A malformed reply usually means we lost frame sync; drop the
            # session so the next poll starts clean.
            self._device = None
            raise YpsilonConnectionError(f"Protocol error: {err}") from err
        except TRANSPORT_ERRORS as err:
            self._device = None
            raise YpsilonConnectionError(str(err)) from err

    # -- public surface ----------------------------------------------------

    def read_identity(self) -> dict[str, Any]:
        with self._lock:
            data = self._guarded(build_query([1, 34]))
            data["mac"] = self.mac
            return data

    def read_state(self, field52_cache: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            state = self._guarded(build_query(STATE_FIELDS))

            # Field 52 is a static filter setting; refreshing it hourly keeps
            # the per-poll product command count at one.
            now = time.monotonic()
            if now >= field52_cache.get("next_refresh", 0.0):
                try:
                    extra = self._guarded(build_query([52]))
                except YpsilonConnectionError:
                    field52_cache["next_refresh"] = now + FIELD52_FAIL_BACKOFF
                else:
                    field52_cache["value"] = extra.get("filterMaterialWorkingDay")
                    field52_cache["next_refresh"] = now + FIELD52_REFRESH

            state["filterMaterialWorkingDay"] = field52_cache.get("value")
            state["_transientRetries"] = self.transient_retries
            state["_reauthCount"] = self.reauth_count
            return state

    def write_fields(self, values: dict[int, Any]) -> None:
        """Send one 0x19 control frame for one or more fields.

        The reply is only checked for framing and outer error: the caller is
        expected to confirm the change with a subsequent read rather than
        trusting an optimistic local state.
        """
        with self._lock:
            self._guarded(build_write_fields(values))
            # Give the MCU a moment to apply the change before the verifying
            # read the caller will issue.
            time.sleep(WRITE_SETTLE_DELAY)
