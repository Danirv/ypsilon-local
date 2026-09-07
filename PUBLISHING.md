# Publishing Ypsilon on GitHub and HACS

The source tree is prepared for the public `Danirv/ypsilon-local` repository and HACS distribution.

## 1. Repository metadata

If preparing a fresh clone/template, configure the repository owner once:

```bash
python scripts/configure_repository.py Danirv --repo ypsilon-local
```

Funding can be configured through GitHub Sponsors and/or Ko-fi. Then verify:

```bash
python scripts/publication_check.py
python scripts/audit.py
python -m compileall -q custom_components/ypsilon_local scripts
```

## 2. Repository requirements

Recommended description:

> Local Home Assistant integration for Runxin F79D / BroadLink BL3372 water softeners, including ATH/BWT Ypsilon G6.

Keep Issues enabled and useful topics such as `home-assistant`, `hacs`, `custom-component`, `water-softener`, `runxin`, `broadlink`, and `ypsilon`.

The repository includes HACS validation, hassfest, the offline protocol/architecture audit, and an automated release workflow. Do not ignore validator failures before publishing or while a HACS default-inclusion request is open.

## 3. Publish a GitHub Release

After the validation workflows are green, tag the exact manifest version:

```bash
VERSION="$(python -c 'import json; print(json.load(open("custom_components/ypsilon_local/manifest.json"))["version"])')"
git tag -a "v${VERSION}" -m "Ypsilon ${VERSION}"
git push origin "v${VERSION}"
```

The release workflow validates the source again, verifies tag/version equality, builds the manual-install archive, and creates a full GitHub Release.

## 4. Test through HACS

Before requesting default inclusion, add the repository to HACS as a custom **Integration**, install/update it, restart Home Assistant, configure the device, and verify the real hardware path.

## 5. HACS default inclusion

Current HACS requirements include a public GitHub repository, passing HACS + hassfest actions, brand assets, repository description/topics/issues, and a full GitHub Release created after successful validation actions.

The project currently has an inclusion request open at `hacs/default#10717`. Normal repository maintenance and new releases can continue while it waits in the review queue; do not open duplicate inclusion PRs or comment on the queue PR unless critical information or reviewer feedback requires it.

## Release discipline

For each release:

1. Update `manifest.json` version.
2. Update `CHANGELOG.md` and `info.md`.
3. Run `python scripts/audit.py`, `python scripts/publication_check.py`, and compileall.
4. Merge only with HACS/hassfest/audit green.
5. Tag exactly `v<manifest version>` so the release workflow creates the full release.
6. Verify the resulting release asset and main-branch validation runs.

Never commit vendor APKs, firmware, proprietary binary/script dumps, credentials, private/pairing keys, or unredacted packet captures.
