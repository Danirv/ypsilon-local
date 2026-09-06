# Security policy

## Supported versions

Security fixes are applied to the latest released version.

## Reporting a vulnerability

Do not publish credentials, pairing material, private keys, account tokens, unique device identifiers, or exploit details that would put users at immediate risk.

If GitHub Private Vulnerability Reporting is enabled for this repository, use it. Otherwise open a minimal issue asking for a private contact channel and omit sensitive details from the issue.

For ordinary functional bugs, use the bug report template.

## Safety boundary

This integration can change configuration, close/control water-related behavior, and start a mechanical regeneration cycle. It is not a certified safety controller and must not be the sole protection against flooding, unsafe plumbing conditions, or equipment damage.
