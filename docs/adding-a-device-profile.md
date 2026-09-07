# Adding another Runxin device profile

Do not start by copying the F79D field table and renaming it. The old WaterDevice
applications contain model-dependent behavior, so a second Runxin controller
must be treated as a separate profile until captures prove what is shared.

## Suggested workflow

1. Identify the controller/model and transport independently.
2. Capture read-only traffic first.
3. Confirm whether the raw frame format matches `runxin/framing.py`.
4. Establish the model/identity field and a minimal safe read set.
5. Build a declarative field catalogue with explicit codecs and evidence.
6. Add offline golden-frame/regression tests.
7. Only then investigate writes, one field at a time, with physical read-back.
8. Keep Home Assistant controls narrower than the protocol's theoretical write
   capability until ranges and consequences are understood.

## Reusing the shared framing

If the new device uses the same `5A 5C` / `DF FD` envelope and request/response
opcodes, reuse `runxin/framing.py`. If not, add a separate framing implementation
rather than weakening validation to accept unrelated packet formats.

## Field catalogue

Use `FieldSpec` / `FieldCodec` from `runxin/fields.py` as the pattern. Keep:

- field id;
- stable semantic name;
- read codec;
- known write codec, if any;
- unit/scaling notes;
- provenance/evidence.

Avoid hiding uncertainty. `inferred` is preferable to presenting a guess as a
verified protocol fact.

## Home Assistant support is a separate decision

A reusable profile can exist in the repository before the Ypsilon integration
supports it. Adding it to automatic discovery/config flow requires additional
work: model naming, device identity, entity applicability, safe-write policy,
translations, diagnostics and real-device testing.

This separation lets reverse-engineering work be useful without pretending a
new model is production-ready.

## Evidence hygiene

Submit sanitised captures, decoded field tables and independently written test
fixtures. Do not commit vendor APKs, firmware, decompiled source dumps, private
keys, credentials or secrets.
