# Legacy WaterDevice / F79D audit

This document records the evidence used by Ypsilon Local to distinguish **wire codec knowledge**, **observed controller state**, and **physically verified writes**. It exists specifically to prevent a recovered application field from being mistaken for a safe current-firmware control.

## Sources and evidence policy

The project independently inspected the legacy WaterDevice product bundle for interoperability and compared its field codec/UI behavior with local F79D traffic and physical Ypsilon G6 read-back.

Evidence labels in `runxin/fields.py` mean:

- `LEGACY_APP_CODEC`: field/encoding recovered from the legacy product codec;
- `DEVICE_STATE_OBSERVED`: the field has been observed in real controller state;
- `HARDWARE_WRITE_VERIFIED`: a local write was followed by fresh read-back confirming the requested value on the tested hardware;
- `CLOUD_WRITE_OBSERVED`: the same setting was also observed changing through the vendor path.

A transport ACK alone is **not** hardware-write verification. Physical controller evidence also takes precedence when it contradicts an inferred interpretation of the recovered application codec.

## F79D operation and field map

The recovered profile uses query opcode `0x09` and control opcode `0x19`. The project catalogue covers fields 1–52. Important codec findings:

- field 7 `flowRateOff`: **16-bit big-endian on the tested Ypsilon G6**, hardware-write verified;
- field 11 `flowRate`: 16-bit big-endian on the wire;
- field 33: two reminder flags, not one integer;
- fields 35/37/39/41: three-byte volume values split across two TLVs; decoding depends on field 8 `waterVolumeUnit`;
- fields 50/51: salt-dissolution and pause-1 remaining minutes;
- field 52: filter-media service interval, queried separately by this integration.

### Field 7: legacy-codec discrepancy resolved by hardware

The recovered WaterDevice path appeared to route field 7 through a generic little-endian helper. Real hardware contradicts that interpretation conclusively:

```text
wire bytes: 03 E8
big-endian:    0x03E8 = 1000 -> 10.00 m³/h
little-endian: 0xE803 = 59395 -> 593.95 m³/h
```

The vendor application displayed 10.00 m³/h while Ypsilon 2.6.2, after changing field 7 to LE, displayed 593.95 m³/h. The same byte pair therefore proves the tested controller is BE.

The write path is independent corroboration. A requested 2.00 m³/h is raw 200 (`0x00C8`) and must be transmitted as `00 C8`. The LE regression transmitted `C8 00`; the controller ACKed the transport/protocol request but repeated fresh reads did not confirm the requested value. Ypsilon's strict reconciliation correctly surfaced `Write ACKed but not confirmed` instead of accepting the ACK as state.

Earlier project versions using BE had already completed successful local SET/read-back verification for field 7. The project therefore restores `HARDWARE_WRITE_VERIFIED` for field 7 while keeping the application-codec discrepancy documented rather than hiding it.

### Volume-pair decoding

The legacy codec reconstructs `[base_high, continuation_low, continuation_high]` and reverses that three-byte sequence.

- unit codes 0 and 1 use a normal 24-bit little-endian integer;
- unit code 2 uses base-100 decimal packing and the displayed cubic-metre quantity is divided by 100.

If the unit field or continuation TLV is absent, Ypsilon Local fails closed instead of guessing a value.

## Water quantities

### Field 37–38: daily consumption

This is the controller's cumulative consumption for the current day. Real history from the tested G6 shows the value increasing through the day and resetting around the day boundary. Home Assistant therefore exposes it as `TOTAL_INCREASING`, where a reset starts a new meter cycle rather than being treated as negative consumption.

### Field 39–40: controller weekly average

The legacy codec names this `averageUsedWater`. It is a current aggregate reported by the controller. It is **not** the same quantity as the vendor application's week-by-week history chart. Ypsilon Local therefore exposes field 39 as **Controller weekly average consumption** with no `state_class`.

### Field 41–42: treatment capacity per cycle

The legacy settings UI treats this as water-treatment capacity/configuration per cycle, not a cumulative consumption meter. It therefore has no Home Assistant `state_class`.

### Statistics migration

Older integration versions briefly declared `MEASUREMENT` for the weekly-average and cycle-capacity entities. Home Assistant may consequently offer to delete their obsolete long-term statistics after upgrade. That cleanup is expected; it does not remove the normal entity.

## Salt semantics

### Field 43: `addSalt`

The legacy settings UI exposes this value as a 0–100 kg amount of salt added and writes it using the generic control path. The project has physically verified local write/read-back and also observed the value changing through the vendor path.

It is a controller bookkeeping/configuration value, **not a physical remaining-salt sensor**. Ypsilon Local therefore does not decrement it after regeneration and does not use it as an estimate of salt remaining.

Physical salt warnings are separate fields: field 31 for low brine concentration and field 33 low flag for the salt/add-salt reminder.

## Vacation semantics and v2.6.1 safety decision

The legacy embedded WaterDevice UI contains calls equivalent to entering vacation with field 49 `holidayMode=1`, leaving with `holidayMode=0` once station 8 is reached, and a legacy preparation progression `0 -> 3 -> 7 -> 2 -> 8`.

This proves how the legacy product UI and codec represented vacation mode. It does **not** prove that a direct local field-49 write is accepted by every current controller firmware.

On the project's tested Ypsilon G6, v2.6.0 sent the local field-49 write, received a transport/protocol ACK, then repeatedly performed fresh state reads. `vacationPattern` remained `false` until timeout. Therefore field 49 remains readable and encodable for interoperability research, but is not `HARDWARE_WRITE_VERIFIED` and Home Assistant exposes no writable Vacation switch.

The newer vendor application also contains dedicated vacation enter/exit operations outside the generic control path, reinforcing the need to avoid assuming that one field write is sufficient on current firmware.

## Regeneration and mechanical state

The legacy UI uses field 34 `systemMode` for regeneration/phase control. Ypsilon Local keeps mechanical commands separated from ordinary reversible settings and always reconciles them using fresh device state. An ACK is never considered proof of valve movement.

## Alarm semantics confirmed from legacy UI

Known field-12 close reasons include 257 manual/position-dependent close, 513 leak detected, 769 continuous-flow timeout and 1025 flow-rate limit exceeded. Other diagnostic fields include clock, position and memory faults plus low-brine, resin and filter/salt reminders.

## Field 52 polling policy

The normal F79D state query remains fields 1..51. Field 52 is a slow-changing filter-media service interval and is queried/cached separately by the Ypsilon composition layer. This is an integration polling optimisation, not a limitation of the protocol field catalogue.

## Release rule

A future control is exposed in Home Assistant only when all required layers are understood:

1. field/frame encoding;
2. device preconditions/state-machine semantics;
3. physical controller acceptance;
4. fresh read-back confirmation;
5. timeout/error/restart behavior.

Knowing only step 1 is enough for a codec implementation, but not enough for a user-facing control.
