# Security Policy

## Supported versions

Security fixes are applied to the latest minor release. Older minors are best-effort.

| Version | Supported |
|---------|-----------|
| 0.3.x   | ✅        |
| < 0.3   | ❌        |

## Reporting a vulnerability

Please report security issues **privately** — do not open a public GitHub issue.

- **Preferred:** GitHub private advisory → [Report a vulnerability](https://github.com/AIQSO/qr-builder/security/advisories/new)
- **Email:** dev@aiqso.io

Include:
- Affected version(s) and a minimal reproduction
- Impact assessment (what an attacker can achieve)
- Any known mitigations or patches

You will receive an acknowledgement within 72 hours. Disclosure will be coordinated after a fix is available.

## Dependency scanning

- `pip-audit` runs in CI on every push and PR
- Dependabot opens PRs weekly for dependency updates
- Optional extras `amzqr` / `pyqart` are unmaintained upstream; pin exact versions if using in production

## Hardening recommendations for operators

- Always set `QR_BUILDER_BACKEND_SECRET` in production (minimum 32 bytes)
- Replace `QR_BUILDER_ALLOWED_ORIGINS=*` with an explicit domain list
- Enforce HTTPS upstream (reverse proxy or ingress)
- Enable `QR_BUILDER_AUTH_ENABLED=true` for any public deployment
- Restrict `QR_BUILDER_MAX_UPLOAD_MB` and `QR_BUILDER_MAX_BATCH_SIZE` to match your traffic model
