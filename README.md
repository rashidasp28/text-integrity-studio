# Text Integrity Studio

Local-first Unicode inspection, safe text cleaning and optional meaning-preserving refinement.

## Project status

Phases 1 to 3 and the first Phase 4 deterministic rewrite build are active.
The behavioural evidence drives the Python inspection and cleaning engine,
local visual application and protected-fact rewrite workflow.

The initial corpus contains 115 cases spanning character controls, whitespace,
punctuation, compatibility normalisation, bidirectional text, contextual
joiners, confusables, protected structures and encoding repair.

This project does not claim that unusual Unicode characters prove AI authorship, or that removing characters changes an AI detector's verdict.

## Behavioural corpus

Cases are stored in `corpus/cases/*.json`. Every case records its source, confidence, enabled rules, expected output and expected findings.

Validate the corpus:

```bash
python scripts/validate_corpus.py
```

Run tests:

```bash
python -m unittest discover -s tests -v
```

## Five-minute quick start

Install the package in editable mode:

```bash
python -m pip install -e .
```

Inspect a UTF-8 file without changing it:

```bash
text-integrity inspect input.txt
```

Clean a file with the conservative Safe profile:

```bash
text-integrity clean input.txt --profile safe --output cleaned.txt --report audit.json
```

Use `-` as the input path to read from standard input. The Publishing profile
also converts typographic dashes, quotation marks and ellipses. Encoding repair,
NFKC normalisation, Markdown removal and confusable replacement remain explicit
opt-in rules through repeated `--rule` options.

The engine runs locally and does not transmit or retain source text. Findings
identify unusual characters and policy decisions, not AI authorship.

## Visual studio preview

Start the local visual interface:

```bash
text-integrity studio
```

The tool opens `http://127.0.0.1:8765` in the default browser. The interface
and processing API bind only to the local computer, impose a 2 MB request
limit, retain no text and make no external requests. Press `Ctrl+C` in the
terminal to stop it.

The visual interface supports TXT and Markdown import, Safe, Publishing and
Custom rule selection, highlighted differences, applied-rule explanations,
copying and downloading cleaned text, JSON audit export, undo and reset.

Version 0.2 adds a local Pre-submission Integrity Review. It inventories
author-year citations and citation keys, reconciles them with a References or
Bibliography section, and flags long quotations without nearby recognised
citations. Its results are local diagnostics, not plagiarism findings, AI
classifications or predictions of a Turnitin score.

## Standalone alpha builds

Version 0.3 adds automated standalone builds for Windows, macOS and Linux.
Successful GitHub Actions runs publish one-file application artifacts with a
SHA-256 checksum. Open the downloaded application and keep its terminal window
open while using the local browser interface. Press `Ctrl+C` to stop it.

Alpha binaries are not yet code-signed. Operating systems may display an
unknown-publisher warning. Verify the checksum before running a downloaded
artifact. Signed installers remain a later release milestone.

## Advanced hidden-data inspection

Version 0.4 inventories every Unicode code point and gives invisible characters
visible labels. It groups Unicode tag characters, zero-width binary sequences
and variation-selector sequences, then attempts decoding only when a recognised
codec produces printable UTF-8. Results are possible payloads, not confirmed AI
watermarks or evidence of authorship.

## Meaning-preserving rewrite

Version 0.5 begins Phase 4 with a deterministic style backend. It identifies a
conservative set of wordy phrases and presents each revision for individual
acceptance. Measurements, dates, citations, numbers, URLs, email addresses and
identifiers are inventoried as protected facts, and accepted revisions are
rejected if that fact signature changes. The JSON audit records accepted and
rejected suggestion IDs and the protected spans used for validation.

Analyse a file from the command line:

```bash
text-integrity rewrite input.txt
```

Apply selected suggestions after reviewing their IDs:

```bash
text-integrity rewrite input.txt --accept S0001 --output revised.txt --report rewrite-audit.json
```

## Confidence levels

- `verified`: directly reproduced against a reference tool
- `documented`: stated in authoritative documentation but not reproduced
- `inferred`: reasonable hypothesis requiring testing
- `proposed`: desired Text Integrity Studio behaviour

## Licence

No production licence has been selected yet. Phase 0 contains independently authored specifications and test data.
