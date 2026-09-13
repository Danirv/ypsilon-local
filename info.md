# Ypsilon 2.6.3

Local Home Assistant integration for compatible Runxin F79D / BroadLink BL3372 water softeners, tested with ATH/BWT Ypsilon G6.

## 2.6.3

This maintenance release fixes the F79D field-7 (`flowRateOff`) wire codec using physical Ypsilon G6 evidence and restores its hardware-write verification status.

Highlights:

- restores field 7 to **16-bit big-endian** for both reads and writes;
- documents the decisive hardware vector: wire bytes `03 E8` are raw `1000` in BE and correspond to the vendor application's `10.00 m³/h`; the regressed LE interpretation produced raw `59395` / `593.95 m³/h` in Home Assistant;
- writes `2.00 m³/h` as raw `200` / bytes `00 C8` instead of the incorrect LE bytes `C8 00`;
- restores `HARDWARE_WRITE_VERIFIED` for field 7 based on the earlier physically verified BE implementation plus the current independent read-back evidence;
- keeps the safe Home Assistant range at `0.00–10.00 m³/h` for the physically calibrated cubic-metre unit mode;
- preserves strict post-write reconciliation: an ACK alone is still never accepted as proof that the controller adopted a setting;
- adds protocol and audit regressions for the exact real-device byte vectors and the historical `59395` misdecode;
- keeps field 52 on its intentional slow-refresh cache rather than moving it into the normal 1..51 polling block;
- reviews English, Catalan and Spanish translations; no translation key or label change is required for this wire-codec fix.

### Upgrade note

No entity registry migration is required. The existing flow-rate cutoff number retains the same unique ID, range, unit and translations; only its raw wire encoding/decoding is corrected.

The transport-neutral `runxin/` layer remains independent from Home Assistant and BroadLink. The Home Assistant integration continues to support only the verified F79D model 9 + BroadLink BL3372 (`0x520F`) combination until additional hardware is tested.
