[English](hardware-verification.md) | [Español](hardware-verification.es.md) | [Català](hardware-verification.ca.md)

# Hardware write verification

A field is marked `HARDWARE_WRITE_VERIFIED` only after the local integration has proved the complete write/read-back path against a physical controller. A protocol ACK or a self-consistent codec is not enough.

The v2.6.1 vacation-mode correction remains an intentional example of this rule: field 49 is writable in the recovered legacy codec, but the tested current Ypsilon G6 ACKed the direct local write without changing fresh read-back state. Therefore Home Assistant exposes vacation state read-only.

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
- **field 7 — flow shutoff threshold, 16-bit big-endian**;
- field 10 — regeneration trigger time;
- field 43 — added-salt bookkeeping value;
- field 47 — raw-water hardness.

Pending or deliberately unverified:

- **field 34 — mechanical regeneration/state-machine writes:** only specifically observed/tested actions should be exposed; codec support alone is not sufficient to generalise all values;
- **field 49 — vacation mode:** direct local `1/0` control is explicitly **not verified** on the tested current G6 and remains absent from Home Assistant.

## Field 7 / flow cutoff evidence

The physical G6 resolves the field-7 byte order independently of the recovered legacy-app interpretation:

```text
wire bytes: 03 E8
big-endian:    0x03E8 = 1000 -> 10.00 m³/h
little-endian: 0xE803 = 59395 -> 593.95 m³/h
```

The vendor application showed 10.00 m³/h while Ypsilon 2.6.2, using the LE regression, displayed 593.95 m³/h. The same controller therefore proves that the actual field-7 wire value is BE.

The write path provides a second independent check. A requested 2.00 m³/h corresponds to raw 200 (`0x00C8`) and therefore bytes `00 C8`. The regressed LE path sent `C8 00`; the transport/protocol layer ACKed the request, but repeated fresh reads did not adopt the requested value and the coordinator raised `Write ACKed but not confirmed`. That is the intended safety behavior.

Earlier project builds using BE had already completed successful physical SET/read-back verification for field 7. Combined with the current independent wire/read-back observation, this restores `HARDWARE_WRITE_VERIFIED` for field 7. The recovered WaterDevice path that appeared LE is retained as conflicting interoperability evidence rather than being allowed to override the tested controller.

## Field 49 / vacation-mode failure evidence

The recovered legacy WaterDevice UI indicates this semantic model:

- enter only from station/system mode 0;
- set the vacation flag;
- legacy preparation progresses through `0 -> 3 -> 7 -> 2 -> 8`;
- stable vacation is represented by field 49 true + station 8;
- the legacy UI uses 25% of the normal slow-wash duration for the vacation brine-draw progress display;
- exit is initiated from station 8.

On the project's current physical G6, v2.6.0 performed the critical hardware check: baseline read showed `vacationPattern=false`, a direct local field-49 SET was sent, transport/protocol returned ACK, repeated independent local reads continued returning `false`, and verification timed out without physical confirmation.

This disproves the specific direct-write method as a user-facing control on that firmware. The current vendor application also contains dedicated vacation enter/exit operations rather than relying only on the generic control path, so Ypsilon must not guess a multi-field or mechanical replacement sequence.

Consequently Ypsilon keeps field-49 read/decode support, legacy encode support for research/interoperability, and the read-only Vacation status sensor, while omitting a writable Vacation switch.

## Water-counter/statistics evidence

A real history export from the tested G6 confirms `dailyWaterConsumption` rises within the day and resets around the day boundary. This supports the Home Assistant `TOTAL_INCREASING` state class for field 37.

The same evidence, together with vendor-app screenshots, confirms that field 39's live controller value is not the same quantity as the app's week-by-week historical total bars. Fields 39 and 41 therefore intentionally have no Home Assistant `state_class`.

## Salt evidence

Field 43 has full local SET/read-back verification and a cloud-side observed change. Its legacy label/behavior is “salt added” in kilograms. This verifies the configuration/bookkeeping field, not a physical salt-level sensor. The integration must not infer or decrement “salt remaining” from this field.

## Field 52 polling note

Field 52 is intentionally not part of the normal 1..51 state block. The Ypsilon composition layer reads and caches it separately because it is a slow-changing service interval. This is a polling optimisation and does not weaken its observed-state evidence.

## Generalisation rule

Evidence from one controller/firmware must not be silently generalised to all Runxin devices. Before extending support to another transport, rebrand or firmware, verify the field codec and the physical semantics independently.

See also [`waterdevice-audit.md`](waterdevice-audit.md) for the complete legacy-app/device evidence summary.
