# Architecture

Ypsilon is a Home Assistant integration first, but the reverse-engineered device
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
  transport-neutral `F79DClient`.

`transport/`
: How a raw Runxin frame reaches a controller. `broadlink_bl3372.py` owns
  BroadLink authentication, encryption, packet `0x6A`, TFB length wrapping,
  outer error handling and retry/session behavior.

`api.py`
: Composition adapter for the Ypsilon G6. It wires `F79DClient` to
  `BroadlinkBL3372Transport` and retains the public/internal names used by the
  Home Assistant code before v2.4. It also owns the Ypsilon-specific field-52
  cache and write-settle timing.

`coordinator.py`
: Home Assistant polling, stale-state tolerance, adaptive cadence, clock
  reconciliation and strict write read-back. An ACK is never treated as proof
  of physical state.

entity platforms
: Presentation and safe user controls only. They should not construct packets.

## Dependency rules

The following are deliberate invariants and are checked by `scripts/audit.py`:

- `runxin/` must not import Home Assistant or BroadLink.
- Runxin framing must not know about BL3372 TFB/encryption/session details.
- `transport/base.py` must not know F79D fields.
- `api.py` composes layers; it should not contain `send_packet`, encryption or
  field codec logic.
- Home Assistant entity ids, config-entry version and unique-id strategy are not
  changed by protocol refactors.

## Why the reusable code is still inside this repository

Home Assistant Core prefers device communication in a standalone PyPI library.
That is also the cleanest long-term reuse model. This project currently has one
fully verified device/transport combination, so publishing and maintaining a
second package now would add release/dependency overhead before there is a real
consumer.

For v2.4 the code is therefore structured to be **extractable**, not extracted.
If another integration/transport/profile starts consuming the protocol layer,
`runxin/` can later become a separately versioned package with minimal churn.

Do not make another Home Assistant custom integration depend at runtime on an
installed copy of `custom_components.ypsilon_local`. HACS does not provide a
stable dependency contract between arbitrary custom integrations. Contribute a
transport/profile here, vendor the pure source where licensing permits, or wait
for a future standalone package.

## Compatibility policy

v2.4 is an internal architecture change:

- domain remains `ypsilon_local`;
- config-flow version remains 2;
- MAC-based unique ids are unchanged;
- entity unique ids and translation keys are unchanged;
- polling, write verification and field-52 cache behavior are preserved;
- `protocol.py` remains as a compatibility facade for research scripts and old
  internal imports, but new code should use `runxin/`.

The integration still supports only the hardware combination it can safely
probe and validate. Making the codec reusable does **not** mean all Runxin valves
or all transports are supported by Home Assistant.
