[English](architecture.md) | [Español](architecture.es.md) | [Català](architecture.ca.md)

# Architecture

Ypsilon is a Home Assistant integration first, but reverse-engineered device
knowledge is intentionally kept below the Home Assistant layer so it can be
reused and, if the ecosystem grows, extracted into a standalone Python package.

## Dependency direction

```text
Home Assistant entities / config flow / services
                 |
                 v
        Ypsilon integration policy
        (api.py + coordinator.py)
                 |
        +--------+---------+
        |                  |
        v                  v
   Runxin F79D          transport
   client/codec         implementation
        |                  |
        +--------+---------+
                 |
                 v
             hardware
```

The concrete tested path is:

```text
Home Assistant
  -> YpsilonLocalClient
  -> F79DClient
  -> F79D field codec
  -> Runxin raw frame
  -> BroadlinkBL3372Transport
  -> BL3372 0x6A/encryption/TFB
  -> Runxin F79D valve
```

### Layer responsibilities

`runxin/`
: Home-Assistant-independent device/protocol knowledge. It owns the observed
  Runxin frame format, the F79D field catalogue, encoding/decoding and a small
  transport-neutral `F79DClient`. It may call optional transport hooks such as
  `transact_write()` but never imports a concrete transport.

`transport/`
: How a raw Runxin frame reaches a controller. `broadlink_bl3372.py` owns
  BroadLink authentication, encryption, packet `0x6A`, TFB length wrapping,
  outer errors and bounded session/retry behavior. Reads may be retried within
  known-safe limits; writes are sent at most once when delivery is ambiguous.

`api.py`
: Composition adapter for the Ypsilon G6. It wires `F79DClient` to
  `BroadlinkBL3372Transport` and retains the public/internal names used before
  v2.4. It also owns Ypsilon-specific field-52 caching and write-settle timing.

`coordinator.py`
: Home Assistant polling, stale-state tolerance, adaptive cadence, clock
  reconciliation and strict physical write read-back. It serializes the whole
  semantic mutation (`SET -> strict GET -> reconciliation`). An ACK is never
  treated as proof of physical state, and a lost response never causes a blind
  resend before the device is read again.

entity platforms
: Presentation and safe user controls only. They should not construct packets.

## Dependency rules

The following are deliberate invariants and are checked by the offline audit:

- `runxin/` must not import Home Assistant or BroadLink.
- Runxin framing must not know BL3372 TFB/encryption/session details.
- `transport/base.py` must not know F79D fields.
- transports must return raw Runxin frames, not decoded device dictionaries.
- `api.py` composes layers; it must not contain packet/encryption/field-codec logic.
- Home Assistant entity ids, config-entry version and MAC identity strategy are
  not changed by protocol refactors.
- write retries must respect idempotency: an ambiguous SET is reconciled before
  any possible resend.

## Why the reusable code is still inside this repository

A standalone PyPI communication library is the clean long-term reuse model.
This project currently has one fully verified device/transport combination, so
maintaining another package would add release/dependency overhead before there
is a second real consumer.

The code is therefore **extractable, not extracted**. If another transport,
device profile or project starts consuming the protocol layer, `runxin/` can
later become a separately versioned package with minimal churn.

Do not make another Home Assistant custom integration depend at runtime on an
installed `custom_components.ypsilon_local`. Contribute a transport/profile
here, vendor the pure source where the license permits, or wait for a future
standalone package.

## Extension model

A second transport for the same F79D should implement the raw-frame transaction
contract without changing the F79D codec. A second Runxin controller should add
a new device profile and only share framing when captures prove it is actually
compatible. Do not generalize the current 52-field catalogue to all Runxin
controllers by assumption.

## Compatibility policy

The 2.4.x architecture keeps:

- domain `ypsilon_local`;
- config-entry version 2;
- MAC-based unique ids;
- existing entity unique ids and translation keys;
- `protocol.py` and `api.py` compatibility facades.

The integration still supports only the hardware combination it can safely
probe and validate: F79D model 9 with BroadLink BL3372 devtype `0x520F`. Making
the lower layers reusable does **not** mean every Runxin valve or transport is
supported by Home Assistant.
