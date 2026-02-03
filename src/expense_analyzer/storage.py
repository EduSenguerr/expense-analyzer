from __future__ import annotations

import json
from pathlib import Path
from datetime import date

from expense_analyzer.parser import Transaction


def load_manual_entries(path: Path) -> list[Transaction]:
    """
    Load manual transactions from JSON.
    Returns an empty list if file doesn't exist.
    """
    if not path.exists():
        return []

    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        return []

    out: list[Transaction] = []
    for item in data:
        posted = date.fromisoformat(item["posted_date"])
        out.append(Transaction(posted_date=posted, description=item["description"], amount=float(item["amount"])))
    return out


def save_manual_entries(path: Path, transactions: list[Transaction]) -> None:
    """
    Save manual transactions to JSON.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    payload = [
        {
            "posted_date": str(t.posted_date),
            "description": t.description,
            "amount": t.amount,
        }
        for t in transactions
    ]

    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
