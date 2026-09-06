# Public release checklist

## Automated gates

- [ ] Behavioral and unit tests pass
- [ ] Bandit static scan passes
- [ ] pip-audit reports no known dependency vulnerabilities
- [ ] CycloneDX SBOM is attached
- [ ] Three platform packages build successfully
- [ ] Checksums are included

## Human gates

- [ ] Acceptance tests completed on Windows
- [ ] Acceptance tests completed on macOS
- [ ] Acceptance tests completed on Linux
- [ ] Project licence selected and reviewed
- [ ] Third-party notices reviewed
- [ ] Windows signing certificate configured
- [ ] Apple signing identity and notarisation configured
- [ ] Linux distribution/signing decision recorded
- [ ] Privacy and security documentation reviewed

Version 1.0.0 must not be tagged until every critical gate is complete.
