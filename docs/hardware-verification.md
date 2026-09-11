[English](hardware-verification.md) | [Español](hardware-verification.es.md) | [Català](hardware-verification.ca.md)

# Hardware write verification

A field is marked `HARDWARE_WRITE_VERIFIED` only after the local integration has proved the complete write/read-back path against a physical controller. A protocol ACK or a self-consistent codec is not enough.

The v2.6.1 vacation-mode correction is an intentional example of this rule: field 49 is writable in the recovered legacy codec, but the tested current Ypsilon G6 ACKed the direct local write without changing fresh read-back state. Therefore Home Assistant exposes vacation state read-only.

## Required sequence

For a reversible configuration field:

1. **Baseline GET** — read the current value locally.
2. **SET candidate** — send one local write with the codec under test.
3. **Independent GET** — read the controller again through a fresh local query.
4. **Physical/semantic check** — confirm that the observed state means what the field is expected to mean.
5. **Restore** — write the original baseline value back.
6. **Independent restore GET** — verify restoration.

Do not use cached coordinator state as evidence.

For a mechanical action, add the expected phase/state transition to steps 3–4. A matching configuration bit without the expected physical transition is insufficient.

## Ambiguous delivery

If a SET is sent and the transport response is lost or times out, do **not** blindly resend it. The controller may already have executed the command. Perform a fresh GET and reconcile the physical state first.

This rule is mandatory for mechanical actions such as regeneration or vacation-state transitions.

## Evidence levels

- app codec only → `LEGACY_APP_CODEC`;
- value observed in real state → `DEVICE_STATE_OBSERVED`;
- cloud-side change observed → `CLOUD_WRITE_OBSERVED`;
- complete local SET/read-back procedure → `HARDWARE_WRITE_VERIFIED`.

Codec knowledge and hardware acceptance are deliberately independent. A field may retain a write codec in `runxin/fields.py` for interoperability research while being absent from the Home Assistant write surface.

## Current Ypsilon G6 / F79D status

Verified locally end-to-end:

- field 4 — device clock / clock sync;
- field 6 — continuous-flow limit;
- field 10 — regeneration trigger time;
- field 43 — added-salt bookkeeping value;
- field 47 — raw-water hardness.

Pending or requiring revalidation:

- **field 7 — flow shutoff threshold:** WaterDevice proves the correct wire codec is little-endian. Versions before 2.6 used BE in both write and read paths, so their read-back could self-confirm the wrong byte order. The old `HW` label is withdrawn until the corrected LE path is exercised on the physical controller;
- **field 34 — mechanical regeneration/state-machine writes:** only specifically observed/tested actions should be exposed; codec support alone is not sufficient to generalise all values;
- **field 49 — vacation mode:** direct local `1/0` control is explicitly **not verified** on the tested current G6 and is not exposed by Home Assistant 2.6.1.

## Field 49 / vacation-mode failure evidence

The recovered legacy WaterDevice UI indicates this semantic model:

- enter only from station/system mode 0;
- set the vacation flag;
- legacy preparation progresses through `0 -> 3 -> 7 -> 2 -> 8`;
- stable vacation is represented by field 49 true + station 8;
- the legacy UI uses 25% of the normal slow-wash duration for the vacation brine-draw progress display;
- exit is initiated from station 8.

On the project's current physical G6, v2.6.0 then performed the critical hardware check:

1. baseline read showed `vacationPattern=false` and service state;
2. direct local field-49 SET was sent;
3. transport/protocol layer returned ACK;
4. repeated independent local reads continued returning `vacationPattern=false`;
5. verification timed out without physical confirmation.

This disproves the assumption that a direct field-49 write is a working local vacation action on that tested firmware. The result is stronger than “pending”: the **specific direct-write method used in v2.6.0 is rejected as a user-facing control** until a different local sequence is discovered and physically verified.

The current vendor application also contains dedicated vacation-enter/exit operations rather than relying only on the generic control path, so Ypsilon must not guess a multi-field or mechanical replacement sequence.

Consequently v2.6.1 keeps:

- field-49 read/decode support;
- field-49 legacy encode support in the transport-neutral protocol layer for research/interoperability;
- the read-only Vacation status semantic sensor;

and removes:

- the Home Assistant Vacation mode switch;
- any coordinator method that directly writes field 49.

## Water-counter/statistics evidence

A real history export from the tested G6 confirms `dailyWaterConsumption` rises within the day and resets around the day boundary. This supports the Home Assistant `TOTAL_INCREASING` state class for field 37.

The same evidence, together with vendor-app screenshots, confirms that field 39's live controller value is not the same quantity as the app's week-by-week historical total bars. Fields 39 and 41 therefore intentionally have no Home Assistant `state_class`.

## Salt evidence

Field 43 has full local SET/read-back verification and a cloud-side observed change. Its legacy label/behavior is “salt added” in kilograms. This verifies the configuration/bookkeeping field, not a physical salt-level sensor. The integration must not infer or decrement “salt remaining” from this field.

## Generalisation rule

Evidence from one controller/firmware must not be silently generalised to all Runxin devices. Before extending support to another transport, rebrand or firmware, verify the field codec and the physical semantics independently.

See also [`waterdevice-audit.md`](waterdevice-audit.md) for the complete legacy-app/device evidence summary.
