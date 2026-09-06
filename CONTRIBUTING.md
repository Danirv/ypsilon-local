# Contributing

Contributions are welcome. The project prioritizes reliable local control, explicit state reconciliation, and conservative handling of commands that can move the valve or consume water/salt.

## Before opening a pull request

1. Run `python scripts/audit.py`.
2. Run `python scripts/publication_check.py` in a configured public clone.
3. Keep user-facing strings in the translation files (`en`, `ca`, `es`).
4. Prefer small, reviewable changes and preserve entity unique IDs unless a migration is provided.
5. For writes, distinguish command transport, protocol ACK, and confirmed device state.

## Protocol research and test data

Interoperability research is welcome, but this repository must not contain vendor APKs, firmware images, proprietary scripts/binaries, credentials, private or pairing keys, account tokens, or unredacted captures containing user/device identifiers.

Small sanitized protocol fixtures that are necessary to test independently written code are acceptable when they contain no secrets and no substantial vendor code/content.

## New devices

For a new device or firmware, include the brand/model, valve/controller model, BroadLink module/devtype if known, and which fields/commands were actually verified. Do not mark an untested field writable merely because its numeric ID looks plausible.

## License

By contributing, you agree that your contribution is licensed under the repository's Apache License 2.0.
