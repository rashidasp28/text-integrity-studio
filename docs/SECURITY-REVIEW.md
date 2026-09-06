# Security review for v0.8.0 release candidate

## Boundaries reviewed

- The local server accepts connections only on loopback addresses.
- Request bodies, individual documents, archives, extracted text and batch files
  have explicit limits.
- DOCX input is processed as data. Archive paths, macros, entry counts,
  decompressed sizes and compression ratios are checked.
- HTML script, style and noscript content is excluded during extraction.
- Encrypted and oversized PDFs are rejected. PDF extraction is text-only.
- Source text, file paths and decoded payloads are excluded from server logs.
- Public-source search and external rewrite services remain disabled.

## Automated evidence

The Release readiness workflow runs Bandit, pip-audit, corpus validation, unit
tests and CycloneDX SBOM generation. Reports are retained as workflow artifacts.

## Residual risks

- PyInstaller executables are not yet signed.
- DOCX and PDF parsers process complex attacker-controlled formats.
- The browser interface has not completed independent penetration testing.
- Unicode policies can produce false positives in multilingual material.
- Cross-run binary reproducibility has not been independently established;
  dependencies are pinned, and each artifact carries its own checksum.

These items block the final v1.0.0 release where indicated in the release
checklist. The release candidate is intended for controlled testing.
