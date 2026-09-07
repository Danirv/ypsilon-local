# Protocol layering and evidence

This document describes what the project has observed for interoperability. It
is not vendor documentation and should not be read as a claim that every Runxin
controller uses the same protocol.

## Layers on the tested device

A normal local transaction contains two independent protocols:

1. a raw Runxin/F79D product frame;
2. a BroadLink BL3372 transport envelope carrying that frame.

The v2.4 refactor keeps those layers separate.

### Raw Runxin frame

The tested F79D uses an outer frame beginning `5A 5C` and ending `A5`, with an
inner frame beginning `DF FD` and ending `DE`. Both layers contain an additive
8-bit checksum. The request opcode is `0x09` for field queries and `0x19` for
control writes. Observed replies use `0xC9` and `0xD9` respectively.

Field data is represented as three-byte groups:

```text
[field_id, byte_1, byte_2]
```

The meaning of the two data bytes depends on the field. The F79D catalogue in
`runxin/fields.py` records the known read and write codecs instead of scattering
that knowledge through conditionals.

### BL3372 transport envelope

The BL3372 prepends a two-byte little-endian length to the raw Runxin frame
before sending it through BroadLink command `0x6A`. Authentication, encryption,
outer response errors and this length prefix are transport concerns and live in
`transport/broadlink_bl3372.py`, not in the Runxin codec.

`protocol.py` still exposes legacy `pack_tfb()` / `unpack_tfb()` helpers only to
avoid breaking old research imports. New code must not use those helpers as
part of the Runxin layer.

## F79D field codecs

The codecs currently needed by the observed profile are:

- `u8`: value in byte 1, byte 2 zero for known writes;
- `u16_le`: little-endian unsigned 16-bit;
- `u16_be`: big-endian unsigned 16-bit;
- `time_hm`: hour/minute;
- `duration_min_sec`: the legacy display pair decoded as minutes/seconds;
- `bool`: boolean from byte 1;
- `volume_pair`: value reconstructed from a base field plus its continuation;
- `reminder_flags`: field 33 split into two boolean flags.

Four water-volume values use two consecutive field ids. A base field without
its continuation is returned as `None` rather than zero because zero would be a
plausible but incorrect physical state.

## Evidence levels

`runxin/fields.py` uses conservative provenance labels:

- `legacy_app_codec`: recovered from the old WaterDevice product codec;
- `device_state_observed`: seen in real Ypsilon/F79D state/captures;
- `hardware_write_verified`: locally exercised against physical hardware;
- `cloud_write_observed`: change observed through the old cloud application;
- `inferred`: interpretation not yet directly confirmed.

A field being present in the old application does not prove it is implemented
identically by every Runxin model or firmware. Write capability in the codec is
also different from the **safe write whitelist** exposed by Home Assistant.

## Compatibility boundary

The project has strong evidence for the F79D profile and the tested Ypsilon G6.
The legacy applications clearly contain model-dependent behavior, which is a
reason to make reuse easier, not a reason to label the F79D map as a universal
Runxin API.

For another controller, first establish:

- whether the `5A 5C` / `DF FD` framing is the same;
- its device-model value;
- which field ids exist;
- read byte order/scaling;
- write encoding and safe ranges;
- phase/state-machine semantics.

See `adding-a-device-profile.md`.

## Safety and research hygiene

Only interoperability facts and independently written code belong in this
repository. Do not commit vendor APKs, firmware, proprietary binaries, pairing
keys, credentials, private tokens or unredacted captures containing secrets.
