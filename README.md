# Ypsilon for Home Assistant

Local Home Assistant integration for compatible water softeners using a **Runxin
F79D** controller and **BroadLink BL3372** Wi-Fi module, including the ATH/BWT
Ypsilon G6 tested by the project.

The integration communicates directly over the LAN and does not depend on the
vendor cloud for normal operation.

> **Status:** community integration, independently developed for interoperability.
> Not affiliated with or endorsed by ATH, BWT, Runxin or BroadLink.

## Highlights

- DHCP discovery for known compatible BroadLink module prefixes.
- Local polling with adaptive fast polling while water is flowing or the valve
  is in an active regeneration phase.
- Real device-state reconciliation after writes: transport success/ACK is not
  treated as proof that the valve adopted the requested value.
- Water consumption and flow entities suitable for Home Assistant's water
  dashboard.
- Regeneration status, remaining treatment capacity, maintenance reminders and
  diagnostics.
- Safe user controls for hardness, salt addition, leak-protection thresholds,
  regeneration schedule, clock and vacation mode.
- Forced regeneration with a mechanical-state confirmation window.
- Advanced raw write/phase services restricted to Home Assistant administrators
  and known writable fields.
- Catalan, Spanish and English translations.
- Transport-neutral, Home-Assistant-independent **Runxin/F79D protocol layer**
  separated from the BroadLink BL3372 transport for reuse and future device
  research.
- Declarative 52-field F79D catalogue with conservative evidence/provenance
  metadata.
- Offline protocol and architecture regression checks in `scripts/audit.py`.

## Supported hardware

Verified Home Assistant target:

- ATH/BWT Ypsilon G6
- Runxin F79D valve/controller
- BroadLink BL3372 module, BroadLink devtype `0x520F`

Other rebranded devices using the same controller/module may work, but
compatibility must be verified per model/firmware. Please use the device
compatibility issue template rather than assuming a field is safe to write.

**v2.4 does not make non-BroadLink devices automatically supported by the Home
Assistant integration.** It separates the protocol from the transport so the
reverse-engineered F79D work can be reused by contributors implementing another
transport or device profile.

## Installation

### HACS

Until the repository is accepted into the HACS default catalog, add it as a
custom repository:

1. HACS → **Integrations** → menu → **Custom repositories**.
2. Add `https://github.com/Danirv/ypsilon-local` as an **Integration**.
3. Install **Ypsilon** and restart Home Assistant.
4. Go to **Settings → Devices & services → Add integration** and search for
   **Ypsilon**.

The repository has been submitted to the HACS default-catalog review queue as
[`hacs/default#10717`](https://github.com/hacs/default/pull/10717).

### Manual

Copy `custom_components/ypsilon_local` into
`/config/custom_components/ypsilon_local` and restart Home Assistant.

## Configuration

Home Assistant can discover supported devices through DHCP. Manual setup accepts
the device's local IP address. The polling interval can later be changed from
the integration options.

The config entry is identified by the device MAC so normal DHCP address changes
do not create a new logical device. A reconfiguration flow is available when
the IP must be changed explicitly.

## Entity model

Primary operational entities include:

- **Flow rate**
- **Daily consumption**
- **Weekly average consumption**
- **Residual water / remaining treatment capacity**
- **Operating status**
- **Regeneration mode** (flow/volume or time/days)
- **Active alerts**

Configuration controls include:

- raw water hardness;
- salt addition;
- continuous-flow safety time;
- maximum permitted flow threshold;
- regeneration trigger time;
- device clock and clock-sync button;
- vacation mode;
- force regeneration.

Maintenance flags, wash-phase timings, resin volume, filter working days, model,
polling mode and communication telemetry are exposed as **diagnostic** entities
so the normal device page remains focused on operational state.

`Operation days` and `Remaining days` are only meaningful in the time/day
regeneration path. When the device is configured for flow/volume regeneration,
`Residual water` is the useful remaining-capacity value. `Maximum regeneration
interval` is exposed separately as a diagnostic limit.

## Water dashboard

Use **Daily consumption** as the consumed-water source. **Flow rate** is optional
and represents the latest sampled instantaneous flow; it is not used to
reconstruct missed short draws. The controller's cumulative daily counter
remains the authoritative consumption source.

## State verification and polling

The design deliberately separates:

1. command sent;
2. protocol transport/ACK;
3. subsequent physical device state returned by the controller;
4. Home Assistant entity state.

Normal polling may temporarily preserve stale values through short communication
errors. A write confirmation does **not** accept stale coordinator data: it
performs a strict read and checks the requested value. Mechanical regeneration
transitions have a longer confirmation window.

Adaptive polling reduces traffic while idle. A short flow event that starts and
finishes entirely between two idle polls can still be missed by the
instantaneous flow entity; the daily cumulative counter should still capture
the consumed volume.

## Advanced services

The integration exposes administrator-only services for advanced protocol work:

- `ypsilon_local.write_fields`
- `ypsilon_local.advance_phase`

They are intentionally restricted to known writable fields. Do not use them as
a substitute for the normal entities unless you understand the valve state
machine.

## Reusing the protocol work

The reverse-engineered device knowledge is split into layers:

```text
Home Assistant -> Ypsilon policy -> F79D client/codec -> raw Runxin frame
                                                     -> transport -> device
```

`custom_components/ypsilon_local/runxin/` contains no Home Assistant or
BroadLink imports. `transport/broadlink_bl3372.py` owns the BroadLink-specific
envelope/session logic. A new transport only needs to provide a raw
`transact(frame: bytes) -> bytes` transaction.

This is deliberately **source-reusable/extractable**, not yet a separately
versioned PyPI API. Do not make another HACS integration depend at runtime on an
installed `custom_components/ypsilon_local`; contribute here, vendor the pure
source where appropriate, or wait for a future standalone library if multiple
real consumers justify one.

Developer/research documentation:

- [`docs/architecture.md`](docs/architecture.md)
- [`docs/protocol.md`](docs/protocol.md)
- [`docs/f79d.md`](docs/f79d.md)
- [`docs/broadlink-bl3372.md`](docs/broadlink-bl3372.md)
- [`docs/adding-a-transport.md`](docs/adding-a-transport.md)
- [`docs/adding-a-device-profile.md`](docs/adding-a-device-profile.md)

## Development

Run the complete offline consistency/protocol regression audit:

```bash
python scripts/audit.py
```

Before publishing a clone/release, also run:

```bash
python scripts/publication_check.py
```

GitHub CI includes HACS validation, hassfest, the offline audit and
release-tag/version checks.

See [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md), and
[PUBLISHING.md](PUBLISHING.md).

## Interoperability, trademarks and safety

The local protocol implementation was independently developed through
interoperability research and validation against observed device behavior.
**No vendor APK, firmware, proprietary binary, private/pairing key, credential
or substantial vendor source/decompiled code is distributed with this project.**
See [LEGAL.md](LEGAL.md).

ATH, BWT, Runxin, BroadLink, Ypsilon and other referenced names may be
trademarks of their respective owners and are used only to identify compatible
hardware.

This software can change water-softener settings and start mechanical
operations. It is not a certified safety controller and should not be the sole
flood/leak protection mechanism.

## Sponsorship

Optional funding links are configured through `.github/FUNDING.yml`, including
Ko-fi. If the integration saves you time and you want to support continued
maintenance, use the repository's standard **Sponsor** button. Funding never
changes functionality or support priority.

## License

Apache License 2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).

## Changelog

See [CHANGELOG.md](CHANGELOG.md).
