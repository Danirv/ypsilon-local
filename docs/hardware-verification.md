[English](hardware-verification.md) | [Español](hardware-verification.es.md) | [Català](hardware-verification.ca.md)

# Hardware write verification

A field is marked `HARDWARE_WRITE_VERIFIED` only after the local integration has proved the complete write/read-back path against a physical controller. A protocol ACK or a self-consistent codec is not enough.

## Required sequence

For a reversible configuration field:

1. **Baseline GET** — read the current value locally.
2. **SET candidate** — send one local write with the codec under test.
3. **Independent GET** — read the controller again through a fresh local query.
4. **Physical/semantic check** — confirm that the observed state means what the field is expected to mean.
5. **Restore** — write the original baseline value back.
6. **Independent restore GET** — verify restoration.

Do not use cached coordinator state as evidence.

## Ambiguous delivery

If a SET is sent and the transport response is lost or times out, do **not** blindly resend it. The controller may already have executed the command. Perform a fresh GET and reconcile the physical state first.

This rule is mandatory for mechanical actions such as regeneration or vacation-state transitions.

## Evidence levels

- app codec only → `LEGACY_APP_CODEC`;
- value observed in real state → `DEVICE_STATE_OBSERVED`;
- cloud-side change observed → `CLOUD_WRITE_OBSERVED`;
- complete local SET/read-back procedure → `HARDWARE_WRITE_VERIFIED`.

## Current Ypsilon G6 / F79D status

Verified locally end-to-end:

- field 4 — device clock / clock sync;
- field 6 — continuous-flow limit;
- field 10 — regeneration trigger time;
- field 43 — salt addition;
- field 47 — raw-water hardness.

Pending or requiring revalidation:

- **field 7 — flow shutoff threshold:** WaterDevice proves the correct wire codec is little-endian. Versions before 2.6 used BE in both write and read paths, so their read-back could self-confirm the wrong byte order. The old `HW` label is therefore withdrawn until the corrected LE path is exercised on the physical controller;
- field 34 — forced regeneration;
- field 49 — vacation mode.

## Mechanical state verification

For field 34 and field 49, matching a single configuration bit is insufficient. Verification must also include the expected physical/state-machine transition.

For vacation mode, the legacy application provides this semantic model:

- enter only from station/system mode 0;
- field 49 becomes true;
- the controller progresses through its mechanical vacation preparation;
- stable vacation is represented by field 49 true + station 8;
- exit is initiated from station 8 and must reconcile back to the non-vacation physical state.

Only after that complete behavior is observed should field 49 receive `HARDWARE_WRITE_VERIFIED`.

Evidence from one controller/firmware must not be silently generalized to all Runxin devices.
