# Third-party notices

Text Integrity Studio v0.8.0 uses the following runtime dependencies:

| Component | Purpose | Licence | Project |
|---|---|---|---|
| defusedxml 0.7.1 | Defensive parsing of DOCX XML | Python Software Foundation License | https://github.com/tiran/defusedxml |
| pypdf 6.17.0 | Local PDF text extraction | BSD-3-Clause | https://pypdf.readthedocs.io/ |

Build and security tooling includes PyInstaller, Bandit, pip-audit and
CycloneDX BOM. These tools are used during development and packaging and are
not all runtime components. The generated CycloneDX SBOM is the authoritative
inventory for a specific release environment.

This notice is not a substitute for legal review. Text Integrity Studio is
distributed under the MIT License included in the repository.
