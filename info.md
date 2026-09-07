# Ypsilon 2.4.1

Local Home Assistant integration for compatible Runxin F79D / BroadLink BL3372 water softeners, tested with ATH/BWT Ypsilon G6.

## 2.4.1

This maintenance release hardens write delivery and state reconciliation without changing entity ids, config-entry identity or the supported hardware gate:

- serializes the complete `SET -> strict local read-back -> reconciliation` sequence;
- never blindly retries an ambiguous BroadLink write; physical state is read before deciding the outcome;
- separates bounded read retries from write delivery semantics;
- records end-to-end hardware verification for device time, continuous-flow limit, flow cutoff, regeneration time, salt addition and raw-water hardness;
- keeps forced regeneration and vacation mode explicitly pending hardware-write verification;
- exposes stale-data age during tolerated communication failures;
- keeps state attributes language-neutral and improves EN/ES/CA translations;
- separates clock-time and duration codecs for future Runxin profiles;
- makes publication and protocol audits version-independent.

The reusable `runxin/` package remains independent from Home Assistant and BroadLink. The Home Assistant integration itself still supports only the verified F79D model 9 + BroadLink BL3372 (`0x520F`) combination until additional hardware is tested.
