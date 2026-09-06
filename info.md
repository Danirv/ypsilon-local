# Ypsilon 2.3.0

Local Home Assistant integration for compatible Runxin F79D / BroadLink BL3372 water softeners, tested with ATH/BWT Ypsilon G6.

## 2.3.0

This release prepares the project for public GitHub and HACS distribution without changing the core local-control architecture introduced in 2.2.x:

- Apache-2.0 license, NOTICE, legal/interoperability note and third-party notice.
- HACS and hassfest GitHub Actions plus the project's offline audit.
- Automated GitHub Release workflow with tag/manifest version validation and a manual-install archive.
- Original local brand icon stored inside the custom integration (supported by current Home Assistant custom integrations).
- GitHub issue forms, pull-request template, CODEOWNERS scaffold, Dependabot, contributing/security/code-of-conduct documents.
- Modern minimal `hacs.json`.
- Publication helper/check scripts so repository-owner URLs and codeowners are not guessed.
- Public documentation rewritten to avoid redistributing or relying on vendor application/firmware material.
- Display name standardized to **Ypsilon** while the existing `ypsilon_local` integration domain remains unchanged.

Core 2.2.x behavior remains: strict post-write confirmation, regeneration-state verification, regeneration mode/maximum interval, diagnostic cleanup, Spanish/Catalan/English translations and unified protocol regression checks.
