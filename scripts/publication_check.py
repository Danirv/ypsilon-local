#!/usr/bin/env python3
"""Fail CI when publication placeholders or release metadata are inconsistent."""

from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "custom_components" / "ypsilon_local" / "manifest.json"


def main() -> int:
    errors: list[str] = []
    manifest = json.loads(MANIFEST.read_text())
    version = manifest.get("version")
    if version != "2.4.0":
        errors.append(f"manifest version is {version!r}, expected '2.4.0'")
    for field in ("documentation", "issue_tracker"):
        if "__GITHUB_USER__" in str(manifest.get(field, "")):
            errors.append(f"manifest {field} still contains __GITHUB_USER__")
    owners = manifest.get("codeowners") or []
    if not owners or any("__GITHUB_USER__" in owner for owner in owners):
        errors.append("manifest codeowners has not been configured")
    codeowners = (ROOT / ".github" / "CODEOWNERS").read_text()
    if "__GITHUB_USER__" in codeowners:
        errors.append(".github/CODEOWNERS has not been configured")
    for relative in ("README.md", "PUBLISHING.md", "docs/README.ca.md", "docs/README.es.md"):
        content = (ROOT / relative).read_text()
        if "__GITHUB_USER__" in content or "__GITHUB_REPO__" in content:
            errors.append(f"{relative} still contains repository placeholders")
    if not (ROOT / "custom_components" / "ypsilon_local" / "brand" / "icon.png").exists():
        errors.append("brand/icon.png is missing")
    if not (ROOT / "LICENSE").exists():
        errors.append("LICENSE is missing")
    if errors:
        print("PUBLICATION CHECK FAILED")
        for error in errors:
            print(f"- {error}")
        print("Run: python scripts/configure_repository.py YOUR_GITHUB_USERNAME")
        return 1
    print("PUBLICATION CHECK CLEAN")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
