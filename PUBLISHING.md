# Publishing Ypsilon on GitHub and HACS

The source tree is prepared for a public repository named `ypsilon-local`. One account-specific value is intentionally not guessed: the maintainer's GitHub username.

## 1. Configure the repository owner

Run once before the first public push:

```bash
python scripts/configure_repository.py Danirv --repo ypsilon-local
```

GitHub Sponsors is configured in this repository for `Danirv`. Once the GitHub Sponsors account is approved, the repository Sponsor button will use it:

```bash
python scripts/configure_repository.py Danirv --repo ypsilon-local --github-sponsors Danirv
```

Or configure Ko-fi with `--ko-fi NAME`.

Then verify:

```bash
python scripts/publication_check.py
python scripts/audit.py
```

## 2. Create the GitHub repository

Recommended repository name: `ypsilon-local`

Recommended description:

> Local Home Assistant integration for Runxin F79D / BroadLink BL3372 water softeners, including ATH/BWT Ypsilon G6.

Recommended topics:

- `home-assistant`
- `hacs`
- `custom-component`
- `water-softener`
- `runxin`
- `broadlink`
- `ypsilon`

Enable **Issues** and verify **Sponsorships** is enabled so the `.github/FUNDING.yml` link is exposed. Optionally enable **Discussions** and **Private vulnerability reporting**.

## 3. Push and validate

Push the default branch. The repository includes:

- HACS validation (`hacs/action@main`)
- hassfest (`home-assistant/actions/hassfest@master`)
- offline audit / protocol regressions

Do not ignore validator failures before requesting HACS default inclusion.

## 4. Publish a GitHub Release

After the validation workflows are green, create and push a version tag matching `manifest.json`:

```bash
git tag -a v2.3.0 -m "Ypsilon 2.3.0"
git push origin v2.3.0
```

The release workflow verifies that the tag and manifest version match, builds a manual-install archive and creates a full GitHub Release with generated release notes.

## 5. Test through HACS as a custom repository

Add the GitHub repository to HACS as a custom **Integration**, install it, restart Home Assistant, configure the device and verify update/reload behavior before requesting default inclusion.

## 6. Request HACS default inclusion

Current HACS requirements include a public GitHub repository, passing HACS + hassfest actions, brand assets, repository description/topics/issues, and at least one full GitHub Release before submission. Submit the repository to `hacs/default` only after those checks pass.

HACS reviews can take significant time, so the custom-repository installation path should remain documented and supported.

## Release discipline

For each release:

1. Update `manifest.json` version.
2. Update `CHANGELOG.md` and `info.md`.
3. Run `python scripts/audit.py` and `python scripts/publication_check.py`.
4. Merge only with HACS/hassfest/audit green.
5. Tag exactly `v<manifest version>`.

Never commit vendor APKs, firmware, proprietary binary/script dumps, credentials, private/pairing keys, or unredacted packet captures.
