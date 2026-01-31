from __future__ import annotations

import re


_MONTH_RE = re.compile(r"^\d{4}-\d{2}$")


def validate_month(month: str) -> str:
    """
    Validate a month key in the form YYYY-MM.
    Returns the same string if valid, raises ValueError otherwise.
    """
    month = month.strip()
    if not _MONTH_RE.match(month):
        raise ValueError("Month must be in YYYY-MM format (example: 2026-01).")
    return month
