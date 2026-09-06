# Security policy

## Supported versions

Text Integrity Studio is release-candidate software. Only the newest version on
the `main` branch receives security fixes.

## Reporting a vulnerability

Do not publish exploitable details in a public issue. Use GitHub's private
security-advisory reporting feature for this repository. Include the affected
version, reproduction steps, impact and any suggested mitigation.

## Security boundaries

- Text processing is local by default.
- The visual interface binds only to `127.0.0.1` or `localhost`.
- API requests are limited to 6 MB. Document, archive, extracted-text and batch
  operations have narrower limits appropriate to their formats.
- Source text is not written to application logs.
- The application does not predict or attempt to evade proprietary detectors.
- Release-candidate binaries are not yet code-signed. Verify the included
  SHA-256 checksum.

Automated release checks include static Python analysis, dependency
vulnerability auditing, a CycloneDX SBOM and the complete regression suite.
Passing these tools does not replace independent review.

Do not use pre-release builds for confidential or regulated documents without
an independent organisational security review.
