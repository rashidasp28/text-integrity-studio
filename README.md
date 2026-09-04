# Text Integrity Studio

Local-first Unicode inspection, safe text cleaning and optional meaning-preserving refinement.

## Project status

Phase 1 is active: the behavioural evidence now drives a functional Python
inspection and deterministic cleaning engine.

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

## Confidence levels

- `verified`: directly reproduced against a reference tool
- `documented`: stated in authoritative documentation but not reproduced
- `inferred`: reasonable hypothesis requiring testing
- `proposed`: desired Text Integrity Studio behaviour

## Licence

No production licence has been selected yet. Phase 0 contains independently authored specifications and test data.
