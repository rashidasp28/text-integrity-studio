# Text Integrity Studio

Local-first Unicode inspection, safe text cleaning and optional meaning-preserving refinement.

## Project status

Phase 0 is active: behavioural evidence and executable acceptance tests.

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

## Confidence levels

- `verified`: directly reproduced against a reference tool
- `documented`: stated in authoritative documentation but not reproduced
- `inferred`: reasonable hypothesis requiring testing
- `proposed`: desired Text Integrity Studio behaviour

## Licence

No production licence has been selected yet. Phase 0 contains independently authored specifications and test data.
