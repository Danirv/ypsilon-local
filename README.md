# Ypsilon for Home Assistant

Local Home Assistant integration for compatible water softeners using a **Runxin F79D** controller and **BroadLink BL3372** Wi-Fi module, including the ATH/BWT Ypsilon G6 tested by this project.

The integration communicates directly over the LAN and does not depend on the vendor cloud for normal operation.

> **Status:** community integration, independently developed for interoperability. Not affiliated with or endorsed by ATH, BWT, Runxin or BroadLink.

## Highlights

- DHCP discovery for known compatible BroadLink module prefixes.
- Local polling with adaptive fast polling while water is flowing or the valve is mechanically moving.
- Real device-state reconciliation after writes: a transport ACK is never treated as proof that the requested state was physically adopted.
- Water consumption, remaining treatment capacity and instantaneous flow entities with unit-aware F79D decoding.
- Regeneration status, work pattern, maintenance reminders and diagnostics.
- Vacation mode with explicit `off` / `preparing` / `active` semantics and the same state-machine guards used by the legacy WaterDevice application.
- Safe controls for hardness, salt addition, leak-protection thresholds, regeneration schedule and clock.
- Forced regeneration with a mechanical-state confirmation window.
- Administrator-only advanced services restricted to known reversible fields; mechanical vacation/regeneration operations cannot bypass their purpose-specific guards.
- Catalan, Spanish and English translations.
- Transport-neutral, Home-Assistant-independent **Runxin/F79D protocol layer** separated from the BroadLink BL3372 transport.
- Declarative 52-field F79D catalogue with conservative evidence/provenance metadata.
- Offline protocol, entity, translation and architecture regression checks in `scripts/audit.py`.
- Local Home Assistant brand assets under `custom_components/ypsilon_local/brand/`.

## Supported hardware

Verified Home Assistant target:

- ATH/BWT Ypsilon G6
- Runxin F79D valve/controller
- BroadLink BL3372 module, BroadLink devtype `0x520F`

Other rebranded devices using the same controller/module may work, but compatibility must be verified per model and firmware. Separating protocol and transport does **not** imply that every Runxin or non-BroadLink device is supported.

## Installation

### HACS

Until the repository is accepted into the HACS default catalog, add it as a custom repository:

1. HACS → **Integrations** → menu → **Custom repositories**.
2. Add `https://github.com/Danirv/ypsilon-local` as an **Integration**.
3. Install **Ypsilon** and restart Home Assistant.
4. Go to **Settings → Devices & services → Add integration** and search for **Ypsilon**.

The repository has been submitted to the HACS default-catalog review queue as `hacs/default#10717`.

### Manual

Copy `custom_components/ypsilon_local` into `/config/custom_components/ypsilon_local` and restart Home Assistant.

## Entity model

Primary operational entities include:

- **Flow rate**
- **Daily consumption**
- **Weekly average consumption**
- **Remaining treatment capacity**
- **Operating status**
- **Regeneration mode**
- **Work pattern**
- **Vacation mode** and **Vacation status**
- **Active alerts**

Configuration controls include raw-water hardness, salt addition, continuous-flow safety time, maximum flow cutoff, regeneration trigger time and device clock.

Maintenance flags, wash-phase timings, salt-dissolution/pause countdowns, resin volume, filter-media interval, model, polling mode and communication telemetry are exposed as **diagnostic** entities so the normal device page stays focused on operational state.

### Vacation-state model

The switch reflects the controller's field-49 vacation flag. A separate enum reports the physical semantic state:

- `off`: vacation flag is not set;
- `preparing`: vacation flag is set and the valve has not yet reached the stable vacation position;
- `active`: vacation flag is set and `station == 8`.

The raw **Operating status** entity remains available independently, so semantic vacation state never hides the physical valve phase.

Adaptive polling treats stable vacation state as idle; transition phases continue using fast polling. Real water flow always takes precedence.

## Water units and F79D codec notes

Ypsilon 2.6 mirrors the legacy WaterDevice codec more closely:

- field 7 (`flowRateOff`) is **little-endian**;
- field 11 (`flowRate`) is **big-endian** because the legacy application explicitly reverses it;
- volume pairs 35/37/39/41 are decoded according to field 8 (`waterVolumeUnit`), rather than through one universal formula;
- legacy flow labels are `gpm`, `L/min`, and `m³/h` for unit codes 0, 1 and 2 respectively.

Only unit code 2 has been calibrated end-to-end against the project's physical Ypsilon G6. Field 7 remains exposed only in that unit family. Its corrected LE write encoding is sourced from the legacy codec; hardware-write evidence is intentionally marked pending again until the corrected implementation is revalidated against the physical controller.

## Water dashboard

Use **Daily consumption** as the consumed-water source. **Flow rate** is optional and represents the latest instantaneous sample; short draws that begin and end entirely between idle polls may not appear in the instantaneous entity, while the controller's cumulative daily counter remains authoritative.

## State verification and safety

The design deliberately separates:

1. command sent;
2. transport/protocol response;
3. fresh physical state returned by the controller;
4. Home Assistant entity state.

Writes are sent once and reconciled through a strict fresh read. Ambiguous delivery is never resolved by blindly sending the same mechanical command again.

This software can change water-softener settings and start mechanical operations. It is not a certified safety controller and should not be the sole flood/leak protection mechanism.

## Advanced services

The integration exposes administrator-only services:

- `ypsilon_local.write_fields`
- `ypsilon_local.advance_phase`

`write_fields` only accepts known reversible configuration fields and applies range/unit validation. Vacation mode and the regeneration state machine are intentionally excluded from that generic surface.

## Reusing the protocol work

```text
Home Assistant -> Ypsilon policy -> F79D client/codec -> raw Runxin frame
                                                     -> transport -> device
```

`custom_components/ypsilon_local/runxin/` contains no Home Assistant or BroadLink imports. `transport/broadlink_bl3372.py` owns the BroadLink-specific envelope/session logic.

Developer/research documentation:

- [`docs/architecture.md`](docs/architecture.md)
- [`docs/protocol.md`](docs/protocol.md)
- [`docs/f79d.md`](docs/f79d.md)
- [`docs/hardware-verification.md`](docs/hardware-verification.md)
- [`docs/broadlink-bl3372.md`](docs/broadlink-bl3372.md)
- [`docs/adding-a-transport.md`](docs/adding-a-transport.md)
- [`docs/adding-a-device-profile.md`](docs/adding-a-device-profile.md)

## Development

Run the complete offline regression audit:

```bash
python scripts/audit.py
```

Before publishing:

```bash
python scripts/publication_check.py
```

GitHub CI includes HACS validation, hassfest, the offline audit and release-tag/version checks.

## Branding

Home Assistant 2026.3+ supports brand assets shipped directly by custom integrations. Ypsilon includes matching icon/logo assets in its local `brand/` directory, so Home Assistant can use the integration artwork without a separate Home Assistant Brands submission. HACS validation also recognizes these local assets; client-side/CDN caches can delay a newly changed image becoming visible.

## Interoperability and legal notice

The local protocol implementation was independently developed through interoperability research and validation against observed device behavior. No vendor APK, firmware, proprietary binary, pairing/private key, credential or substantial decompiled vendor source is distributed with this project.

See [LEGAL.md](LEGAL.md), [THIRD_PARTY.md](THIRD_PARTY.md), [SECURITY.md](SECURITY.md) and [LICENSE](LICENSE).

## Sponsorship

Optional funding links are configured through `.github/FUNDING.yml`. Funding never changes functionality or support priority.

## Changelog

See [CHANGELOG.md](CHANGELOG.md).
