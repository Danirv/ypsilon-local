[English](protocol.md) | [Español](protocol.es.md) | [Català](protocol.ca.md)

# Protocol layering and evidence

Ypsilon keeps the protocol stack split into independent layers:

```text
Home Assistant policy -> F79D client/codec -> raw Runxin frame
                                          -> transport -> device
```

The reusable `runxin/` package contains no Home Assistant or BroadLink dependencies. `transport/broadlink_bl3372.py` owns BroadLink authentication/session/encryption/retry behavior.

## Raw F79D frame

The tested controller uses an outer frame starting `5A 5C` and ending `A5`, containing an inner frame starting `DF FD` and ending `DE`. Both layers carry additive 8-bit checksums.

Observed request opcodes:

- `0x09` — field query;
- `0x19` — control/write.

Observed replies use `0xC9` and `0xD9` respectively.

Field data is transported in three-byte groups:

```text
[field_id, byte_1, byte_2]
```

Those two bytes do **not** have one global endianness. The field catalogue is authoritative for each field.

## Field codecs

Known codecs include:

- `u8`;
- `u16_le`;
- `u16_be`;
- `time_hm`;
- `duration_min_sec`;
- `bool`;
- `volume_pair`;
- `reminder_flags`.

Version 2.6.0 explicitly records the legacy WaterDevice asymmetry:

- field 7 (`flowRateOff`) is `u16_le`;
- field 11 (`flowRate`) is `u16_be` because WaterDevice reverses that field before its generic integer decoder.

Volume-pair fields are also unit dependent. See [`f79d.md`](f79d.md); a single universal formula is incorrect.

## Evidence model

`runxin/fields.py` records conservative provenance:

- `legacy_app_codec` — recovered from the legacy WaterDevice product codec;
- `device_state_observed` — seen in real Ypsilon/F79D state/captures;
- `hardware_write_verified` — local SET exercised end-to-end and confirmed by an independent fresh physical read;
- `cloud_write_observed` — a change observed through the old cloud application;
- `inferred` — interpretation not directly confirmed.

A protocol ACK alone is never hardware-write evidence.

The 2.6 correction deliberately removes `hardware_write_verified` from field 7. The prior implementation encoded and decoded that field with the same wrong byte order, so it could self-confirm. The field can regain `HW` only after the corrected LE implementation is tested against the physical controller.

## Read and write delivery semantics

Reads are idempotent and transports may retry them within bounded policy.

Writes are treated differently:

1. send the SET once;
2. do not blindly resend after an ambiguous timeout;
3. perform a strict fresh GET;
4. reconcile the physical result;
5. report success only when the requested state is confirmed.

This is especially important for mechanical operations.

## Home Assistant policy versus codec capability

A syntactically writable field is not automatically a safe Home Assistant control. Ypsilon 2.6 narrows the generic administrator `write_fields` service to reversible configuration fields and applies range/unit checks.

Mechanical/state-machine fields are intentionally excluded:

- field 34 — regeneration/system mode;
- field 49 — vacation mode.

They must use purpose-specific controls, which can enforce physical preconditions and reconciliation rules.

## Vacation semantics

WaterDevice uses field 49 as the vacation flag and field 34 as the physical system mode. Its normal UI enters vacation only from mode 0 and exits from stable mode 8.

Ypsilon therefore distinguishes:

- command/flag state;
- intermediate mechanical transition;
- stable vacation state.

The raw station is always retained and exposed independently.

## BL3372 envelope

The BroadLink BL3372 transport prepends a two-byte little-endian length to the raw Runxin frame before sending it through BroadLink command `0x6A`. Authentication, encryption, outer errors, retry budgets and the length prefix are transport concerns, not F79D field-codec concerns.

## Compatibility boundary

The project has strong evidence for the tested ATH/BWT Ypsilon G6 / Runxin F79D / BroadLink BL3372 combination. For another controller or firmware, establish framing, model id, field ids, byte order/scaling, write safety and phase semantics independently.

See [`adding-a-device-profile.md`](adding-a-device-profile.md) and [`hardware-verification.md`](hardware-verification.md).
