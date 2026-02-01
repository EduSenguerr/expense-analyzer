from __future__ import annotations

import re


_COMMON_NOISE = re.compile(
    r"""
    \b(
        purchase|pos|debit|credit|visa|mastercard|amex|
        online|payment|txn|transaction|
        authorization|auth|card|
        inc|llc|ltd|co
    )\b
    """,
    re.IGNORECASE | re.VERBOSE,
)

_MULTI_SPACE = re.compile(r"\s+")
_TRAILING_NUMBERS = re.compile(r"[\s#-]*\d{2,}$")  # e.g. "#1234", "- 000123"


def normalize_description(description: str) -> str:
    """
    Normalize a bank statement description into a cleaner merchant-style label.

    Heuristics:
    - Uppercase for consistency
    - Remove common noise words
    - Remove trailing numbers (store IDs, transaction IDs)
    - Collapse whitespace
    """
    text = (description or "").strip()
    if not text:
        return "UNKNOWN"

    text = text.upper()

    # Remove common noise words
    text = _COMMON_NOISE.sub(" ", text)

    # Remove trailing ids/numbers often appended by banks
    text = _TRAILING_NUMBERS.sub("", text)

    # Normalize whitespace
    text = _MULTI_SPACE.sub(" ", text).strip()

    return text or "UNKNOWN"
