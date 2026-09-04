# Phase 0: behavioural evidence

## Objective

Create a reproducible evidence base before implementing cleaning algorithms.

## Inclusion rules

Every case must have a stable identifier, exact input, enabled options, exact expected output, expected findings, evidence source, observation date and confidence level.

## Evidence policy

- Never upgrade `documented`, `inferred` or `proposed` cases to `verified` without a reproducible observation.
- Do not treat unusual Unicode as evidence of AI authorship.
- Preserve legitimate multilingual characters in the Safe profile.
- Record reference-tool changes as new observations rather than silently overwriting history.

## Phase completion criteria

- At least 100 curated cases
- All ten observed AI Text Cleaner options represented
- Every relevant Unicode risk family represented
- At least twelve language or script contexts represented
- Transformation-order interactions tested
- Empty, malformed and large-input behaviour documented
- CI validates the schema and corpus on every change
