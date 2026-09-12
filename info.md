# Ypsilon 2.6.2

Local Home Assistant integration for compatible Runxin F79D / BroadLink BL3372 water softeners, tested with ATH/BWT Ypsilon G6.

## 2.6.2

This maintenance release completes the native F79D field audit and corrects metadata that was merged after the already-published v2.6.1 tag.

Highlights:

- exposes previously omitted readable F79D fields 2, 3, 13, 14, 24, 25 and 48 as diagnostics;
- models fields 2 (`language`), 3 (`deviceTimeScheme`), 24 (`outRelayMode`) and 48 (`absorbSaltMode`) as semantic Home Assistant enums instead of raw integers;
- keeps fields 13, 14 and 25 numeric; field 25 is the controller's resin-maintenance regeneration threshold, not a regeneration counter;
- preserves raw enum codes as diagnostic attributes while presenting stable localized enum states;
- corrects the field-6 continuous-water configuration range to 0–120 minutes;
- corrects the unit-code-2 field-7 cutoff range to 0–10.00 m³/h (raw 0–1000);
- adds complete English, Catalan and Spanish state translations and recovered-setting documentation;
- strengthens field-surface and recovered-setting regression tests so enum semantics, translations and ranges cannot silently regress;
- keeps all previously established 2.6.1 safety decisions, including read-only vacation status and strict physical read-back validation.

### Upgrade note

No entity registry migration is required for existing entities. Newly surfaced diagnostic entities use stable unique IDs. Most low-level diagnostics are disabled by default; the native resin-maintenance regeneration threshold (field 25) is enabled by default because it is directly useful for derived maintenance calculations.

The transport-neutral `runxin/` layer remains independent from Home Assistant and BroadLink. The Home Assistant integration continues to support only the verified F79D model 9 + BroadLink BL3372 (`0x520F`) combination until additional hardware is tested.
