"""Small transport-neutral client for a Runxin F79D controller.

Only a synchronous `transact(frame) -> frame` transport is required. The
transport may be BroadLink, serial, TCP, ESPHome-backed, or a test double.
"""

from __future__ import annotations

import threading
from typing import Any, Protocol

from .errors import RunxinProtocolError
from .f79d import STATE_FIELDS, build_query, build_write_fields, decode_frame


class TransactionTransport(Protocol):
    """Minimal structural contract consumed by `F79DClient`."""

    def transact(self, frame: bytes) -> bytes:
        """Send one raw Runxin request and return one raw Runxin response."""
        ...


class F79DClient:
    """Read/write F79D fields through an arbitrary transaction transport."""

    def __init__(self, transport: TransactionTransport) -> None:
        self.transport = transport
        self._lock = threading.Lock()

    def close(self) -> None:
        """Close the transport when it provides a close hook."""
        close = getattr(self.transport, "close", None)
        if callable(close):
            close()

    def _invalidate_transport(self) -> None:
        invalidate = getattr(self.transport, "invalidate", None)
        if callable(invalidate):
            invalidate()

    def _transaction(self, request: bytes) -> dict[str, Any]:
        response = self.transport.transact(request)
        try:
            return decode_frame(response)
        except RunxinProtocolError:
            # A malformed product frame can mean stale framing/session state.
            # Stateful transports may reset themselves; stateless transports
            # simply inherit the no-op behavior.
            self._invalidate_transport()
            raise

    def read_fields(self, fields: list[int]) -> dict[str, Any]:
        """Read an explicit set of F79D field ids."""
        with self._lock:
            return self._transaction(build_query(fields))

    def read_identity(self) -> dict[str, Any]:
        """Read the small identity/status set used during discovery."""
        return self.read_fields([1, 34])

    def read_state(self) -> dict[str, Any]:
        """Read the normal 1..51 F79D state block."""
        return self.read_fields(STATE_FIELDS)

    def write_fields(self, values: dict[int, Any]) -> None:
        """Write one or more F79D fields in a single 0x19 transaction."""
        with self._lock:
            self._transaction(build_write_fields(values))
