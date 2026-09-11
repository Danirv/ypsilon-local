# Changelog

All notable changes to this project are documented here.

## [2.5.0] - 2026-09-11

### Added
- Read-only `Work pattern` enum for F79D field 9 using the exact legacy WaterDevice code mapping.
- Centralized transport-neutral semantic mappings for F79D station, unit, regeneration-pattern and work-pattern codes.
- Semantic protocol summary in Home Assistant diagnostics while retaining the raw controller state.
- Regression tests for work-pattern mapping and Home Assistant state-class choices.

### Changed
- Correct Home Assistant statistics semantics: `averageWeeklyWaterConsumption` and `periodicWaterProduction` no longer declare `measurement`, because the former is already a historical aggregation and the latter is not a present-time measurement or cumulative meter.
- Keep `dailyWaterConsumption` as `total_increasing`, and keep instantaneous flow and remaining treatment capacity as `measurement`.
- Improve regeneration-mode translations without changing the stable `flow` / `time` entity states.
- Clarify time-mode day labels and rename the salt configuration as salt added.
- Mark field 9 as observed on real hardware while keeping it read-only; no new mechanical writes are enabled.
- Document the verified cubic-metre volume/flow interpretation and keep cloud-only `regenerationTimes` intentionally unmapped locally.

## [2.4.1] - 2026-09-07

### Added
- Explicit stale-data diagnostics with physical-data age.
- Write-specific transport hook so stateful transports can avoid blind retries after ambiguous delivery.
- Explicit F79D duration write codec, while retaining the legacy `WRITE_TIME` compatibility symbol.
- End-to-end hardware-write evidence for device clock, continuous-flow limit, flow cutoff, regeneration time, salt addition and raw-water hardness.
- Translatable administrator-service errors in English, Spanish and Catalan.

### Changed
- Serialise the full `SET -> strict GET -> reconciliation` mutation sequence so writes and automatic clock correction cannot interleave semantically.
- BroadLink read retries now use independent transient and re-authentication budgets.
- BroadLink writes are sent at most once; a lost ACK is reconciled through physical read-back instead of being resent blindly.
- Rapid coalesced entity writes now make every caller await and receive the final physical success/failure result.
- Advanced services are registered at integration setup time rather than depending on a loaded config entry.
- Field 5 remains read-only in Home Assistant and was removed from the advanced safe-write whitelist.
- Flow-cutoff configuration is only enabled for the verified cubic-metre unit mode.
- State attributes are data-only; static Catalan descriptions were removed from recorder-facing attributes.
- Filter-media field 52 is named as a service interval rather than elapsed working days.
- Publication/audit version checks are version-agnostic instead of hardcoding 2.4.0.
- F79D fields 34 (forced regeneration) and 49 (vacation mode) remain explicitly pending physical write verification.

## [2.4.0] - 2026-09-07

### Added
- Home-Assistant-independent `runxin/` package with raw frame codec, declarative F79D field catalogue and transport-neutral `F79DClient`.
- `transport/` abstraction and isolated `BroadlinkBL3372Transport` implementation.
- Conservative per-field evidence/provenance metadata for interoperability research.
- Internal architecture, protocol, F79D, BroadLink transport, new-transport and new-device-profile documentation.
- Offline architecture regressions to ensure the reusable Runxin layer stays free of Home Assistant/BroadLink dependencies.

### Changed
- Split BL3372 TFB/session/encryption/retry concerns from F79D field/framing concerns without changing Home Assistant entities, config-entry identity or write verification behavior.
- Kept `api.py` and `protocol.py` as compatibility facades so existing integration imports/research helpers continue to work.
- Moved field-52 caching and write-settle policy to the Ypsilon composition layer instead of the reusable F79D client.
- Clarified that BroadLink outer error `-5` is empirically transient on the tested device; the exact internal MCU/UART cause is not proven.
- Expanded README/contribution guidance around protocol reuse and future extraction to a standalone Python package.

## [2.3.0] - 2026-09-07

### Added
- Apache-2.0 licensing, NOTICE, legal/interoperability and third-party documentation.
- Local custom-integration brand icon (light and dark variants).
- HACS validation, hassfest, offline-audit and automated GitHub Release workflows.
- GitHub issue forms, PR template, CODEOWNERS scaffold, Dependabot, contributing/security/code-of-conduct files.
- `scripts/configure_repository.py` and `scripts/publication_check.py` for safe first publication without guessing the maintainer's GitHub account.
- Public publishing checklist and release procedure.

### Changed
- Public display name standardized from `Ypsilon Local` to `Ypsilon`; domain remains `ypsilon_local` for compatibility.
- `hacs.json` reduced to the currently supported minimal metadata.
- README rewritten for public interoperability/HACS distribution and vendor-artifact hygiene.

## [2.2.1] - 2026-09-06
- Unified protocol regression tests into `scripts/audit.py`; removed the duplicated test path.

## [2.2.0] - 2026-09-06
- Added strict read-back verification after writes; stale coordinator data cannot confirm a SET.
- Added longer verification for mechanical regeneration transitions.
- Added regeneration mode and maximum regeneration interval.
- Moved maintenance flags, timing fields, operation/remaining days, model, polling mode, resin volume and filter working days to Diagnostics.
- Corrected residual-water semantics to remaining treatment capacity rather than physical storage.
- Fixed v1→v2 MAC migration and preserved registry identities where possible.
- Closed temporary config-flow clients and made advanced services administrator-only.
- Prevented stationary `valve closed` state from forcing permanent fast polling.
- Removed custom-component `strings.json`; added Spanish translation.
- Cleaned legacy Device Time / Wash start time registry entries.

## [2.1.0]
- Rejected incomplete multi-field volume values instead of publishing false zeroes.
- Rejected invalid time values before they could reach entities or clock calculations.
- Expanded protocol and consistency auditing.

## [2.0.0]
- Preserved the BroadLink client/session and field-52 cache across option reloads.
- Added explicit session close on entry removal and correct advanced-service lifecycle.
- Hardened device-clock correction so an optional clock check cannot invalidate a good poll.

## [1.9.0]
- Coalesced rapid repeated edits to reduce unnecessary writes to the slow valve link.
- Added the Active alerts aggregate sensor.
- Removed a non-existent leakage field from the alert model and added audit coverage.

## [1.8.0]
- Separated writable Device Time from read-only Wash start time semantics.

## [1.7.0]
- Continued entity/diagnostic cleanup and protocol hardening.

## [1.6.0]
- Improved adaptive polling and state handling.

## [1.5.0]
- Expanded controls and diagnostics while keeping writes restricted to verified field encodings.

## [1.4.0]
- Improved protocol/entity mapping and safety checks.

## [1.3.0]
- Improved coordinator behavior and integration diagnostics.

## [1.2.0]
- Added further local control and state decoding improvements.

## [1.1.0]
- Corrected flow scaling; raw field 11 is exposed through the appropriate configured unit family.
- Added adaptive polling.

## [1.0.0]
- Completed local bidirectional read/write support for verified F79D fields.
- Added multi-field control frames and robust ACK handling.
- Added post-write reconciliation and Home Assistant errors for failed writes.
- Moved runtime state to `ConfigEntry.runtime_data`, added reconfiguration, firmware information and advanced services.

## [0.8.0]
- Added bidirectional control, DHCP discovery and MAC-based identity/migration.
