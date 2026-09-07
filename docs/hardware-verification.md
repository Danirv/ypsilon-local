[English](hardware-verification.md) | [Español](hardware-verification.es.md) | [Català](hardware-verification.ca.md)

# Hardware write verification

A field is marked `HARDWARE_WRITE_VERIFIED` only after the local integration has
proved the complete path against a physical controller. A protocol ACK alone is
not sufficient.

## Required sequence

For a reversible configuration field:

1. **Baseline GET** — read the current value locally and record it.
2. **SET candidate** — send one local write using the integration/codec under test.
3. **Independent GET** — read the controller again through a fresh local query.
4. **Physical/semantic check** — confirm the observed state means what the field
   is expected to mean, not merely that an ACK was returned.
5. **Restore** — write the original baseline value back.
6. **Independent restore GET** — verify that the original state is restored.

Do not use cached coordinator state as evidence. Verification must come from a
new physical read.

## Ambiguous write delivery

If the transport times out or loses the response after sending a SET, **do not
blindly resend the command**. The controller may already have executed it.
Perform an independent GET first and reconcile the physical state. This is
especially important for mechanical actions such as forced regeneration.

## Evidence levels

- app codec only → `LEGACY_APP_CODEC`;
- value observed in real state → `DEVICE_STATE_OBSERVED`;
- cloud-side value change observed → `CLOUD_WRITE_OBSERVED`;
- complete local SET/read-back procedure above → `HARDWARE_WRITE_VERIFIED`.

## Current Ypsilon G6 / F79D status

Verified locally end-to-end:

- field 4 — device clock / sync clock;
- field 6 — continuous-flow limit;
- field 7 — flow shutoff threshold, with `waterVolumeUnit=2`;
- field 10 — regeneration trigger time;
- field 43 — salt addition;
- field 47 — raw-water hardness.

Still pending:

- field 34 — forced regeneration;
- field 49 — vacation mode.

A contributor validating another Runxin model, firmware, rebrand or transport
must report that hardware separately. Evidence from one controller must not be
silently generalized to all Runxin devices.
