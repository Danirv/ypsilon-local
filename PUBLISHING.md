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

## 3. Publish a GitHub Release from the web

The preferred release path does not require a local Git clone:

1. Merge the version bump and release notes into `main` only after HACS, hassfest and the offline audit are green.
2. Open GitHub **Actions** → **Publish GitHub release**.
3. Select **Run workflow** and make sure the branch selector is `main`.
4. Run the workflow.

The workflow reads the version directly from `custom_components/ypsilon_local/manifest.json`, validates the source again, refuses to reuse an existing tag/release, and creates an annotated `v<manifest version>` tag on the exact `main` commit. The tag push then starts the release job, which validates the tagged source again, builds the manual-install ZIP, verifies tag/version equality and creates the GitHub Release.

This two-stage flow deliberately keeps the tag as the release trigger, so releases created from the web and releases created from Git remain equivalent and auditable.

### Git CLI alternative

If a local clone is available, the same release can still be started by tagging the exact manifest version:

```bash
VERSION="$(python -c 'import json; print(json.load(open("custom_components/ypsilon_local/manifest.json"))["version"])')"
git tag -a "v${VERSION}" -m "Ypsilon ${VERSION}"
git push origin "v${VERSION}"
```

Do not manually create a GitHub Release for the same tag; the workflow owns release creation.

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
5. Prefer **Actions → Publish GitHub release → Run workflow** on `main`; alternatively push exactly `v<manifest version>` from Git.
6. Verify the resulting release asset and main-branch validation runs.

Never commit vendor APKs, firmware, proprietary binary/script dumps, credentials, private/pairing keys, or unredacted packet captures.
