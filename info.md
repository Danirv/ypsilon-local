# Ypsilon 2.5.0

Local Home Assistant integration for compatible Runxin F79D / BroadLink BL3372 water softeners, tested with ATH/BWT Ypsilon G6.

## 2.5.0

This release improves semantic accuracy without widening the mechanical write surface:

- adds a read-only Work pattern enum for F79D field 9 using the exact legacy WaterDevice code mapping;
- keeps the stable regeneration-mode states while presenting them more clearly as metered/volume-based versus time/day-based;
- corrects Home Assistant state classes so historical weekly averages and controller cycle/configuration quantities are not misrepresented as present-time measurements;
- keeps daily consumption as `total_increasing`, and instantaneous flow plus remaining treatment capacity as `measurement`;
- documents the evidence behind those state-class choices using legacy WaterDevice semantics, observed device behavior and Home Assistant's statistics model;
- records that the daily counter semantics are strongly supported, while a continuous within-day monotonic/reset trace remains an optional future validation point;
- centralizes F79D enum semantics in the transport-neutral protocol layer;
- enriches diagnostics with interpreted protocol codes while retaining raw state;
- documents verified cubic-metre volume and flow semantics and leaves cloud-only `regenerationTimes` intentionally unmapped;
- adds regression tests for enum mappings and state-class choices.

No new protocol writes are enabled in this release. Work pattern remains read-only, and the existing conservative write/read-back policy is unchanged.

The reusable `runxin/` package remains independent from Home Assistant and BroadLink. The Home Assistant integration itself still supports only the verified F79D model 9 + BroadLink BL3372 (`0x520F`) combination until additional hardware is tested.
