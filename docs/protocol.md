[English](protocol.md) | [Español](protocol.es.md) | [Català](protocol.ca.md)

# Protocol layering and evidence

This document describes what the project has observed for interoperability. It
is not vendor documentation and should not be read as a claim that every Runxin
controller uses the same protocol.

## Layers on the tested device

A normal local transaction contains two independent protocols:

1. a raw Runxin/F79D product frame;
2. a BroadLink BL3372 transport envelope carrying that frame.

The 2.4.x architecture keeps those layers separate.

### Raw Runxin frame

The tested F79D uses an outer frame beginning `5A 5C` and ending `A5`, with an
inner frame beginning `DF FD` and ending `DE`. Both layers contain an additive
8-bit checksum. The request opcode is `0x09` for field queries and `0x19` for
control writes. Observed replies use `0xC9` and `0xD9` respectively.

Field data is represented as three-byte groups:

```text
[field_id, byte_1, byte_2]
```

The meaning of the data bytes depends on the field. `runxin/fields.py` records
the known read/write codecs and evidence explicitly.

### BL3372 transport envelope

The BL3372 prepends a two-byte little-endian length to the raw Runxin frame
before sending it through BroadLink command `0x6A`. Authentication, encryption,
outer errors, retry policy and this length prefix are transport concerns.

`protocol.py` still exposes legacy `pack_tfb()` / `unpack_tfb()` helpers only for
backwards compatibility with research scripts. New protocol code belongs under
`runxin/`.

## F79D field codecs

Observed codecs include:

- `u8`;
- `u16_le`;
- `u16_be`;
- `time_hm` — time of day, hour/minute;
- `duration_min_sec` — duration tuple, minute/second;
- `bool`;
- `volume_pair` — a base field plus its continuation;
- `reminder_flags` — field 33 split into two boolean flags.

Clock-time and duration writes deliberately use distinct semantic codecs even
when both occupy two payload bytes. This prevents future users from treating a
duration as a time of day merely because the wire shape is similar.

Four water-volume values use two consecutive field ids. A base field without
its continuation is returned as `None`, never a plausible false zero.

## Evidence levels

`runxin/fields.py` uses conservative provenance labels:

- `legacy_app_codec`: recovered from the old WaterDevice product codec;
- `device_state_observed`: seen in real Ypsilon/F79D state/captures;
- `hardware_write_verified`: local SET exercised end-to-end and confirmed by an
  independent physical read-back;
- `cloud_write_observed`: change observed through the old cloud application;
- `inferred`: interpretation not yet directly confirmed.

A protocol ACK is not enough for `hardware_write_verified`. See
[`hardware-verification.md`](hardware-verification.md).

A field being present in the old application does not prove it is implemented
identically by every Runxin model or firmware. Codec write support is also
separate from the narrower **safe write whitelist** exposed by Home Assistant.

## Read and write delivery semantics

Reads are idempotent and a transport may use bounded retries when appropriate.
Writes are not assumed idempotent. If delivery becomes ambiguous after a SET is
sent, the transport must not blindly duplicate it; physical state should be
queried and reconciled first.

## Compatibility boundary

The project has strong evidence for the F79D profile and the tested Ypsilon G6.
The legacy applications contain model-dependent behavior, which is a reason to
make reuse easier, not a reason to call the current 52-field map a universal
Runxin API.

For another controller, first establish:

- whether the `5A 5C` / `DF FD` framing is actually shared;
- its device-model value;
- which field ids exist;
- read byte order/scaling;
- write encoding and safe ranges;
- phase/state-machine semantics.

See [`adding-a-device-profile.md`](adding-a-device-profile.md).

## Safety and research hygiene

Only interoperability facts and independently written code belong here. Do not
commit vendor APKs, firmware, proprietary binaries, pairing keys, credentials,
private tokens or unredacted captures containing secrets.
