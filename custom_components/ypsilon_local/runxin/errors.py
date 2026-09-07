"""Transport-agnostic Runxin protocol exceptions.

This module deliberately has no Home Assistant or transport dependency so the
Runxin codec can be vendored or extracted into another Python project.
"""

from __future__ import annotations


class RunxinError(Exception):
    """Base error for reusable Runxin protocol/client code."""


class RunxinTransportError(RunxinError):
    """Raised when the transport cannot complete a Runxin transaction."""


class RunxinProtocolError(RunxinError):
    """Raised when a Runxin frame is malformed or semantically unexpected."""


# Backwards-compatible name used by the original single-file F79D codec.
F79DProtocolError = RunxinProtocolError
