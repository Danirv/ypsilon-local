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

Known codecs include `u8`, `u16_le`, `u16_be`, `time_hm`, `duration_min_sec`, `bool`, `volume_pair` and `reminder_flags`.

The recovered WaterDevice codec establishes an important asymmetry:

- field 7 (`flowRateOff`) is `u16_le`;
- field 11 (`flowRate`) is `u16_be` because WaterDevice explicitly reverses that field before its generic integer decoder.

Volume-pair fields are unit dependent. See [`f79d.md`](f79d.md); a single universal formula is incorrect.

## Evidence model

`runxin/fields.py` records conservative provenance:

- `legacy_app_codec` — recovered from the legacy WaterDevice product codec;
- `device_state_observed` — seen in real Ypsilon/F79D state/captures;
- `hardware_write_verified` — local SET exercised end-to-end and confirmed by an independent fresh physical read;
- `cloud_write_observed` — a change observed through the vendor/cloud path;
- `inferred` — interpretation not directly confirmed.

A protocol ACK alone is never hardware-write evidence. Codec support and current-firmware physical acceptance are separate facts.

The field-7 correction deliberately removed its old `hardware_write_verified` label: the prior implementation encoded and decoded the same wrong byte order and could therefore self-confirm. It can regain `HW` only after the corrected LE path is physically revalidated.

Field 49 is the complementary example introduced by 2.6.1: the legacy codec can encode the vacation flag, but the tested G6 ACKed a direct local write while repeated fresh reads remained unchanged. That specific write method is therefore **not** a verified Home Assistant control.

## Read and write delivery semantics

Reads are idempotent and transports may retry them within bounded policy.

Writes are treated differently:

1. send the SET once;
2. do not blindly resend after an ambiguous timeout;
3. perform a strict fresh GET;
4. reconcile the physical result;
5. report success only when the requested state is confirmed.

Mechanical operations additionally require the expected physical/state-machine transition, not merely a matching bit.

## Home Assistant policy versus codec capability

A syntactically writable field is not automatically a safe Home Assistant control. The generic administrator `write_fields` service is limited to reversible configuration fields and applies range/unit checks.

Mechanical/state-machine fields are excluded from that generic service:

- field 34 — regeneration/system mode;
- field 49 — vacation state.

Field 34 is handled only by specific operations whose behavior is understood. **Field 49 has no writer in Home Assistant 2.6.1**: its state remains readable, but the failed direct-write method from 2.6.0 was withdrawn rather than replaced with a guessed sequence.

## Vacation semantics

The recovered legacy UI uses field 49 as the vacation flag and field 34 as physical system mode. It enters from mode 0, reaches stable vacation at mode 8 and reveals the legacy progression `0 -> 3 -> 7 -> 2 -> 8`.

Ypsilon still derives a read-only semantic state while retaining raw `station`:

- `off`: vacation flag false;
- `preparing`: flag true, station not 8;
- `active`: flag true, station 8.

On the tested current G6, however, direct local `field49=1` was ACKed without changing read-back. The newer vendor application also contains dedicated vacation-enter/exit operations. Consequently no local vacation action is exposed until a correct sequence is physically verified.

## Water/statistics semantics

Real controller history confirms field 37 is a within-day cumulative counter that resets at the day boundary, supporting Home Assistant `TOTAL_INCREASING` semantics.

Field 39 is a controller weekly average and is not the same quantity as the vendor application's week-by-week historical total bars. Field 41 is treatment/cycle capacity, not a cumulative meter. Neither declares a Home Assistant `state_class`.

Field 43 is an amount of salt added/bookkept by the controller, not a measured salt level.

## BL3372 envelope

The BroadLink BL3372 transport prepends a two-byte little-endian length to the raw Runxin frame before sending it through BroadLink command `0x6A`. Authentication, encryption, outer errors, retry budgets and the length prefix are transport concerns, not F79D field-codec concerns.

## Compatibility boundary

The project has strong evidence for the tested ATH/BWT Ypsilon G6 / Runxin F79D / BroadLink BL3372 combination. For another controller or firmware, establish framing, model id, field ids, byte order/scaling, write safety and phase semantics independently.

See [`f79d.md`](f79d.md), [`waterdevice-audit.md`](waterdevice-audit.md), [`hardware-verification.md`](hardware-verification.md) and [`adding-a-device-profile.md`](adding-a-device-profile.md).
