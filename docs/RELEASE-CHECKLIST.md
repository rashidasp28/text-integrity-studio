# Public release checklist

## Automated gates

Regression and security evidence was last verified on 13 September 2026 against
the `pypdf` 6.18.0 update in the
[Phase 0 corpus validation run](https://github.com/rashidasp28/text-integrity-studio/actions/runs/34771426309)
and the
[release-readiness run](https://github.com/rashidasp28/text-integrity-studio/actions/runs/34771426305).
The dependency update was merged to `main` as commit
`679046303e2c46eda463d47a98fafb58e2e8e095`.

- [x] Behavioral and unit tests pass
- [x] Bandit static scan passes
- [x] pip-audit reports no known dependency vulnerabilities
- [x] CycloneDX SBOM is generated

The three-platform build and checksum evidence was last verified on 6 September
2026 in the
[three-platform build run](https://github.com/rashidasp28/text-integrity-studio/actions/runs/34022808885)
for commit `827eddf4ad95fcc25dc0d5ea5b1f97ba0f591634`.

- [x] Three platform packages build successfully
- [x] Checksums are included
- [ ] Three-platform builds rerun after the `pypdf` 6.18.0 update

Do not treat the earlier platform artifacts as final release evidence. Rerun the
three-platform build from the current `main` branch before approving a release
candidate.

## Human gates

- [ ] Acceptance tests completed on Windows
- [ ] Acceptance tests completed on macOS
- [ ] Acceptance tests completed on Linux
- [x] Project licence selected: MIT
- [ ] Project licence legal review recorded
- [ ] Third-party notices reviewed
- [ ] Windows signing certificate configured
- [ ] Apple signing identity and notarisation configured
- [ ] Linux distribution/signing decision recorded
- [ ] Privacy and security documentation reviewed

Version 1.0.0 must not be tagged until every critical gate is complete.
