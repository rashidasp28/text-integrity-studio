"""Built-in profiles and option expansion."""

from __future__ import annotations

SAFE_RULES = (
    "remove_hidden",
    "convert_nbsp",
    "normalize_unusual_spaces",
    "remove_trailing_whitespace",
)

PUBLISHING_RULES = SAFE_RULES + (
    "normalize_dashes",
    "normalize_quotes",
    "convert_ellipsis",
)

PROFILES = {
    "safe": SAFE_RULES,
    "safe_profile": SAFE_RULES,
    "publishing": PUBLISHING_RULES,
    "publishing_profile": PUBLISHING_RULES,
}


def expand_options(options: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    """Expand profile aliases while preserving deterministic rule order."""
    requested = set(options)
    expanded = set(requested)
    for profile, rules in PROFILES.items():
        if profile in requested:
            expanded.update(rules)

    order = (
        "repair_encoding",
        "normalize_nfkc",
        "remove_hidden",
        "convert_nbsp",
        "normalize_unusual_spaces",
        "remove_trailing_whitespace",
        "normalize_dashes",
        "normalize_quotes",
        "convert_ellipsis",
        "remove_asterisks",
        "remove_markdown_headings",
        "convert_lookalikes",
    )
    return tuple(rule for rule in order if rule in expanded)
