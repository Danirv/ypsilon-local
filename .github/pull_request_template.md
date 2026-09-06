## Summary

Describe the change and why it is needed.

## Validation

- [ ] `python scripts/audit.py` passes.
- [ ] `python scripts/publication_check.py` passes.
- [ ] No vendor APK, firmware, proprietary binary, pairing key, credential, MAC address, or unredacted capture is included.
- [ ] User-facing strings are translated in `en.json`, `ca.json`, and `es.json` when applicable.
- [ ] Behavior that sends a command to the valve has real-state verification or a documented reason why physical confirmation is impossible.

## Device test

Describe the hardware and firmware used for testing, if applicable.
