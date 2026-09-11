# Ypsilon 2.6.1

Local Home Assistant integration for compatible Runxin F79D / BroadLink BL3372 water softeners, tested with ATH/BWT Ypsilon G6.

## 2.6.1

This corrective release tightens the project's evidence policy after validating v2.6.0 against real hardware and the legacy WaterDevice application.

Highlights:

- removes the writable Vacation mode switch after a real Ypsilon G6 ACKed the local field-49 write but fresh read-back remained unchanged;
- keeps Vacation status available as a read-only semantic sensor and retains field-49 codec support for interoperability research without claiming hardware write support;
- preserves `dailyWaterConsumption` as a resettable `TOTAL_INCREASING` controller counter, backed by observed within-day growth and day-boundary resets;
- clarifies field 39 as the controller's weekly-average value, not the vendor application's historical/current-week bar total;
- clarifies field 41 as treatment capacity per cycle rather than a cumulative consumption meter;
- clarifies field 43 as the amount of salt added/bookkept by the controller, not a measured salt level and not something the integration decrements after regeneration;
- documents the legacy WaterDevice/F79D evidence in English, Catalan and Spanish;
- adds regressions for water-counter resets, statistics semantics, salt semantics and the read-only vacation policy;
- replaces the v2.6.0 reused square branding asset with properly proportioned square icon and landscape logo families, including exact 2x and dark variants;
- expands the offline audit to validate brand geometry and prevent withdrawn vacation controls/translations from returning.

### Home Assistant statistics migration

Older versions briefly generated long-term statistics for weekly-average and cycle-capacity entities. Home Assistant may offer to delete those obsolete statistics now that their corrected entities intentionally have no `state_class`. This does not delete the entities or ordinary recorder history.

The transport-neutral `runxin/` layer remains independent from Home Assistant and BroadLink. The Home Assistant integration continues to support only the verified F79D model 9 + BroadLink BL3372 (`0x520F`) combination until additional hardware is tested.
