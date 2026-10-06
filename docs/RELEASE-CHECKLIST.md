# Public release checklist

## Automated gates

Regression and security evidence was last verified on 22 September 2026 against
the `pypdf` 6.19.0 update in the
[Phase 0 corpus validation run](https://github.com/rashidasp28/text-integrity-studio/actions/runs/35691283512)
and the
[release-readiness run](https://github.com/rashidasp28/text-integrity-studio/actions/runs/35691283558).
The dependency update was merged to `main` as commit
`7ac3f95488ba37e4dc1d98eec6d46348c945187c`.

- [x] Behavioral and unit tests pass
- [x] Bandit static scan passes
- [x] pip-audit reports no known dependency vulnerabilities
- [x] CycloneDX SBOM is generated

The three-platform build and checksum evidence was verified on 22 September
2026 in the
[three-platform build run](https://github.com/rashidasp28/text-integrity-studio/actions/runs/35691283538)
for commit `7ac3f95488ba37e4dc1d98eec6d46348c945187c`.

- [x] Three platform packages build successfully
- [x] Checksums are included
- [x] Three-platform builds rerun after the `pypdf` 6.19.0 update

Artifact digests recorded by the build workflow:

- Linux: `sha256:c3b6b8a216fd2f990428d1e2bea65203f45a1e3c4457e916961f9ac5053cc75c`
- macOS: `sha256:bd990a238396cbe8191dda43dd2c8f9440cf960a09a256aebc36c82c4ab5ce41`
- Windows: `sha256:bd6284a11746bd8e042375cd3059f90c9979ced3977ed1a471a63adeb6611c1a`

These workflow results establish current automated build evidence. They do not
replace the platform-specific human acceptance tests below.

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
