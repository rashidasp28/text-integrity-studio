# Public release checklist

## Automated gates

The current release dependency is `pypdf` 6.21.4, merged to `main` on
8 November 2026 as commit
[`a048854`](https://github.com/rashidasp28/text-integrity-studio/commit/a048854b7fadc94123ea373cab5ef62e3235e3f1).
Its pull-request commit `950312bd76d5276f70bf10565220cb8a6057d45e`
passed [Phase 0 corpus validation](https://github.com/rashidasp28/text-integrity-studio/actions/runs/41331539068)
and [release readiness](https://github.com/rashidasp28/text-integrity-studio/actions/runs/41331539072).
These runs included the behavioral corpus, unit tests, CLI smoke test,
release-gate verification, Bandit static analysis, dependency vulnerability
audit, CycloneDX SBOM generation and regression automation.

- [x] Behavioral and unit tests pass for the 6.21.4 pull-request commit
- [x] Bandit static scan passes for the 6.21.4 pull-request commit
- [x] pip-audit reports no known dependency vulnerabilities for the 6.21.4 pull-request commit
- [x] CycloneDX SBOM is generated for the 6.21.4 pull-request commit
- [ ] Windows, macOS and Linux packages rebuilt from current `main` after the 6.21.4 update
- [ ] New package checksums recorded for the 6.21.4 build

The previous
[three-platform build](https://github.com/rashidasp28/text-integrity-studio/actions/runs/35691283538)
passed on 22 September 2026 for `pypdf` 6.19.0 at commit
`7ac3f95488ba37e4dc1d98eec6d46348c945187c`.
Its historical artifact digests are retained below for traceability. They
must not be treated as checksums for the 6.21.4 release candidate:

- Linux: `sha256:c3b6b8a216fd2f990428d1e2bea65203f45a1e3c4457e916961f9ac5053cc75c`
- macOS: `sha256:bd990a238396cbe8191dda43dd2c8f9440cf960a09a256aebc36c82c4ab5ce41`
- Windows: `sha256:bd6284a11746bd8e042375cd3059f90c9979ced3977ed1a471a63adeb6611c1a`

Run the three-platform standalone build against current `main`, verify the
packaged PDF import regression and artifact checksums, then replace the
historical evidence with the new run and digests. Automated checks do not
replace platform-specific human acceptance tests.

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
