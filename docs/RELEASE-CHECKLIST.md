# Public release checklist

## Automated gates

Evidence last verified on 6 September 2026 in the [release-readiness run](https://github.com/rashidasp28/text-integrity-studio/actions/runs/34022808882) and the [three-platform build run](https://github.com/rashidasp28/text-integrity-studio/actions/runs/34022808885).

- [x] Behavioral and unit tests pass
- [x] Bandit static scan passes
- [x] pip-audit reports no known dependency vulnerabilities
- [x] CycloneDX SBOM is attached
- [x] Three platform packages build successfully
- [x] Checksums are included

These checks apply to commit `827eddf4ad95fcc25dc0d5ea5b1f97ba0f591634`. Run them again after any code, dependency, workflow or packaging change.

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
