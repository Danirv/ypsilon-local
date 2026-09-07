"""Tests for transport/client contracts and bounded delivery behavior."""

from __future__ import annotations

import pytest

from .helpers import load

client_mod = load("runxin.client")
framing = load("runxin.framing")
transport_mod = load("transport.broadlink_bl3372")


def _empty_write_response() -> bytes:
    header = [0x5A, 0x5C, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0x12, 0, 0]
    inner = [0xDF, 0xFD, 0, framing.WRITE_RESPONSE_CODE, 0, 0xDE]
    header[15] = len(inner)
    inner[2] = len(inner)
    inner[-2] = sum(inner[:-2]) & 0xFF
    frame = header + inner + [0, 0xA5]
    frame[2] = len(frame)
    frame[-2] = sum(frame[:-2]) & 0xFF
    return bytes(frame)


def test_client_prefers_write_specific_hook() -> None:
    class Fake:
        def __init__(self) -> None:
            self.reads = 0
            self.writes = 0

        def transact(self, frame: bytes) -> bytes:
            self.reads += 1
            return _empty_write_response()

        def transact_write(self, frame: bytes) -> bytes:
            self.writes += 1
            return _empty_write_response()

    fake = Fake()
    client = client_mod.F79DClient(fake)
    client.write_fields({43: 50})
    assert fake.writes == 1
    assert fake.reads == 0


def test_write_path_never_retries_ambiguous_error(monkeypatch) -> None:
    transport = transport_mod.BroadlinkBL3372Transport("192.0.2.1")
    calls = 0

    def fail_once(frame: bytes) -> bytes:
        nonlocal calls
        calls += 1
        raise transport_mod.BroadlinkOuterError(-5)

    monkeypatch.setattr(transport, "_transact_once", fail_once)
    with pytest.raises(transport_mod.BroadlinkOuterError):
        transport.transact_write(b"frame")
    assert calls == 1


def test_read_transient_retries_are_bounded(monkeypatch) -> None:
    transport = transport_mod.BroadlinkBL3372Transport(
        "192.0.2.1", transient_delays=(0.0, 0.0)
    )
    calls = 0

    def eventually_ok(frame: bytes) -> bytes:
        nonlocal calls
        calls += 1
        if calls < 3:
            raise transport_mod.BroadlinkOuterError(-5)
        return b"ok"

    monkeypatch.setattr(transport, "_transact_once", eventually_ok)
    monkeypatch.setattr(transport_mod.time, "sleep", lambda _: None)
    monkeypatch.setattr(transport_mod.random, "uniform", lambda _a, _b: 0.0)
    assert transport.transact(b"frame") == b"ok"
    assert calls == 3
    assert transport.transient_retries == 2


def test_reauth_budget_does_not_consume_transient_budget(monkeypatch) -> None:
    transport = transport_mod.BroadlinkBL3372Transport(
        "192.0.2.1", transient_delays=(0.0, 0.0)
    )
    sequence = [-1, -5, -5, 0]

    def sequence_reply(frame: bytes) -> bytes:
        code = sequence.pop(0)
        if code:
            raise transport_mod.BroadlinkOuterError(code)
        return b"ok"

    monkeypatch.setattr(transport, "_transact_once", sequence_reply)
    monkeypatch.setattr(transport, "_drop_session", lambda: None)
    monkeypatch.setattr(transport_mod.time, "sleep", lambda _: None)
    monkeypatch.setattr(transport_mod.random, "uniform", lambda _a, _b: 0.0)
    assert transport.transact(b"frame") == b"ok"
    assert transport.reauth_count == 1
    assert transport.transient_retries == 2
