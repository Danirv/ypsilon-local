"""BroadLink BL3372 transport for raw Runxin transactions.

This module owns every BroadLink-specific concern: discovery/authentication,
0x6A packet transport, encryption, the two-byte TFB length envelope, outer
response errors, session refresh and the observed transient -5 retry policy.
The Runxin codec never imports this module or the `broadlink` package.
"""

from __future__ import annotations

import random
import threading
import time
from typing import Any

import broadlink
import broadlink.exceptions

from ..runxin.errors import RunxinTransportError
from .base import RunxinTransport

DEFAULT_DEVTYPE = 0x520F
DEFAULT_SOCKET_TIMEOUT = 5
DEFAULT_TRANSIENT_ERROR_CODE = -5
DEFAULT_AUTH_ERROR_CODES = frozenset({-1, -7})
DEFAULT_TRANSIENT_DELAYS = (0.4, 0.8)

BROADLINK_EXCEPTIONS = (
    broadlink.exceptions.BroadlinkException,
    OSError,
    TimeoutError,
)


class BroadlinkOuterError(RunxinTransportError):
    """BroadLink outer response error read from packet offset 0x22."""

    def __init__(self, code: int) -> None:
        self.code = code
        super().__init__(f"BroadLink outer error {code}")


def pack_tfb(frame: bytes) -> bytes:
    """Wrap a raw Runxin frame in the BL3372 two-byte little-endian length."""
    return len(frame).to_bytes(2, "little") + frame


def unpack_tfb(plaintext: bytes) -> bytes:
    """Remove the BL3372 length prefix and ignore decrypted block padding."""
    if len(plaintext) < 2:
        raise RunxinTransportError("missing BL3372 TFB length prefix")
    declared = int.from_bytes(plaintext[:2], "little")
    if declared > len(plaintext) - 2:
        raise RunxinTransportError("BL3372 declared length exceeds plaintext")
    return plaintext[2:2 + declared]


class BroadlinkBL3372Transport(RunxinTransport):
    """Authenticated BroadLink transport carrying Runxin frames over 0x6A."""

    def __init__(
        self,
        host: str,
        *,
        expected_devtype: int | None = DEFAULT_DEVTYPE,
        timeout: float = DEFAULT_SOCKET_TIMEOUT,
        transient_error_code: int = DEFAULT_TRANSIENT_ERROR_CODE,
        auth_error_codes: frozenset[int] = DEFAULT_AUTH_ERROR_CODES,
        transient_delays: tuple[float, ...] = DEFAULT_TRANSIENT_DELAYS,
    ) -> None:
        self.host = host
        self.expected_devtype = expected_devtype
        self.timeout = timeout
        self.transient_error_code = transient_error_code
        self.auth_error_codes = auth_error_codes
        self.transient_delays = transient_delays

        self._device: Any = None
        self._firmware: int | None = None
        self._lock = threading.Lock()
        self.transient_retries = 0
        self.reauth_count = 0

    @property
    def identifier(self) -> str | None:
        """Return the BroadLink MAC as a plain 12-character hex string."""
        raw = getattr(self._device, "mac", None) if self._device else None
        if raw is None:
            return None
        if isinstance(raw, (bytes, bytearray)):
            return raw.hex()
        return str(raw).replace(":", "").replace("-", "").lower()

    @property
    def mac(self) -> str | None:
        """Compatibility alias for `identifier`."""
        return self.identifier

    @property
    def firmware(self) -> int | None:
        return self._firmware

    @property
    def diagnostics(self) -> dict[str, int]:
        return {
            "transient_retries": self.transient_retries,
            "reauth_count": self.reauth_count,
        }

    def _drop_session(self) -> None:
        device = self._device
        self._device = None
        sock = getattr(device, "sock", None) if device else None
        if sock is not None:
            try:
                sock.close()
            except OSError:
                pass

    def invalidate(self) -> None:
        """Drop the current authenticated BroadLink session."""
        self._drop_session()

    def close(self) -> None:
        """Close the BroadLink socket and discard the session."""
        with self._lock:
            self._drop_session()

    def _connect(self) -> Any:
        device = broadlink.hello(self.host, timeout=self.timeout)
        if device is None:
            raise RunxinTransportError("No BroadLink device found")
        if (
            self.expected_devtype is not None
            and int(device.devtype) != self.expected_devtype
        ):
            raise RunxinTransportError(
                f"Unexpected devtype 0x{int(device.devtype):04x}"
            )
        device.timeout = self.timeout
        if device.auth() is False:
            raise RunxinTransportError("BroadLink auth failed")
        self._device = device

        if self._firmware is None:
            # Cosmetic transport metadata only; a missing firmware value must
            # never make an otherwise healthy Runxin transaction fail.
            try:
                self._firmware = int(device.get_fwversion())
            except Exception:  # noqa: BLE001
                self._firmware = None
        return device

    def _transact_once(self, frame: bytes) -> bytes:
        device = self._device or self._connect()
        response = bytes(device.send_packet(0x6A, pack_tfb(frame)))
        if len(response) < 0x38:
            raise RunxinTransportError("Short BroadLink response")

        error = int.from_bytes(response[0x22:0x24], "little", signed=True)
        if error:
            raise BroadlinkOuterError(error)

        encrypted = response[0x38:]
        if not encrypted or len(encrypted) % 16:
            raise RunxinTransportError("Invalid BroadLink encrypted length")
        return unpack_tfb(device.decrypt(encrypted))

    def _transact_resilient(self, frame: bytes) -> bytes:
        """Retry the two observed recoverable BroadLink failure classes.

        On the tested BL3372/F79D, outer error -5 is transient and often clears
        after a short retry on the same session. Captures prove the behavior,
        but not the vendor's exact internal cause, so we deliberately avoid
        labelling it as a specific MCU/UART state. Outer -1/-7 behave like stale
        authentication/session failures and get one fresh auth attempt.
        """
        reauthed = False
        for attempt in range(len(self.transient_delays) + 1):
            try:
                return self._transact_once(frame)
            except BroadlinkOuterError as err:
                if err.code in self.auth_error_codes and not reauthed:
                    reauthed = True
                    self.reauth_count += 1
                    self._drop_session()
                    continue
                if (
                    err.code == self.transient_error_code
                    and attempt < len(self.transient_delays)
                ):
                    self.transient_retries += 1
                    base = self.transient_delays[attempt]
                    time.sleep(base + random.uniform(0, base / 2))
                    continue
                raise
        raise AssertionError("unreachable")

    def transact(self, frame: bytes) -> bytes:
        """Carry one raw Runxin request through the BroadLink 0x6A channel."""
        with self._lock:
            try:
                return self._transact_resilient(frame)
            except RunxinTransportError:
                self._drop_session()
                raise
            except BROADLINK_EXCEPTIONS as err:
                self._drop_session()
                raise RunxinTransportError(str(err)) from err
