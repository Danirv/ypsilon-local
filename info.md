# Ypsilon 2.6.0

Local Home Assistant integration for compatible Runxin F79D / BroadLink BL3372 water softeners, tested with ATH/BWT Ypsilon G6.

## 2.6.0

This release aligns the local protocol implementation more closely with the legacy WaterDevice codec and improves vacation-state handling, safety policy, diagnostics and branding.

Highlights:

- corrects field 7 (`flowRateOff`) to little-endian while retaining field 11 (`flowRate`) as big-endian;
- makes volume-pair decoding depend on `waterVolumeUnit`;
- corrects unit-code-1 flow display to L/min;
- adds a separate Vacation status enum (`off`, `preparing`, `active`) without hiding the raw valve phase;
- applies the legacy application's vacation entry/exit state-machine guards;
- prevents stable vacation mode from forcing permanent fast polling;
- adds diagnostic countdowns for fields 50 and 51;
- interprets known field-12 system-close reason codes while preserving the raw value;
- narrows and validates the generic administrator raw-write surface;
- changes field 31's visible meaning to low brine concentration;
- withdraws field 7's previous hardware-write evidence until the corrected LE path is physically revalidated;
- refreshes English, Catalan and Spanish translations and protocol documentation;
- ships refreshed matching Home Assistant icon/logo brand assets.

The transport-neutral `runxin/` layer remains independent from Home Assistant and BroadLink. The Home Assistant integration itself continues to support only the verified F79D model 9 + BroadLink BL3372 (`0x520F`) combination until additional hardware is tested.
