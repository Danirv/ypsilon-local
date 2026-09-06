# Changelog

All notable changes to this project are documented here.

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

## [2.1.0] - 2026-09-06
- Unified protocol regression tests into `scripts/audit.py`; removed the duplicated test path.

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

## [0.4.0]
- Distinguished transient BroadLink `-5` MCU-busy behavior from expired-session conditions and reduced bus contention.

## [0.3.0]
- Improved volume/state classes, diagnostics and temporary communication-failure tolerance.

## [0.2.0]
- Corrected flow unit/scale behavior and daily-consumption modeling.
