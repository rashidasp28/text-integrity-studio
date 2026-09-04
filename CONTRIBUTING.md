# Contributing

Thank you for helping improve Text Integrity Studio.

## Development checks

Use Python 3.11 or newer. Before proposing a change, run:

```bash
python scripts/validate_corpus.py
python -m unittest discover -s tests -v
```

New deterministic behaviour requires a behavioural corpus case. Character
policy changes must include multilingual preservation tests. UI changes should
remain usable without an internet connection.

## Integrity policy

Contributions must improve transparent inspection, attribution, citation
quality or safe document processing. Features intended to conceal plagiarism,
misrepresent authorship, manipulate hidden characters or evade an academic
integrity detector will not be accepted.

## Pull requests

Keep changes focused, explain the user-visible behaviour and state how it was
tested. Do not commit source documents, personal data, model weights or build
artifacts.
