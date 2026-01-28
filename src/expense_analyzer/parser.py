from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from datetime import date


@dataclass(frozen=True)
class Transaction:
    posted_date: date
    description: str
    amount: float


def load_transactions(csv_path: Path) -> list[Transaction]:
    """
    Load transactions from a CSV with columns: date, description, amount.

    Rules:
    - date: YYYY-MM-DD
    - amount: negative = expense, positive = income
    """
    rows: list[Transaction] = []

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)

        required = {"date", "description", "amount"}
        if not required.issubset(set(reader.fieldnames or [])):
            raise ValueError(f"CSV must contain columns: {sorted(required)}")

        for line_num, row in enumerate(reader, start=2):
            raw_date = (row.get("date") or "").strip()
            raw_desc = (row.get("description") or "").strip()
            raw_amount = (row.get("amount") or "").strip()

            if not raw_date or not raw_desc or not raw_amount:
                raise ValueError(f"Missing value on line {line_num}")

            posted = date.fromisoformat(raw_date)
            amount = float(raw_amount)

            rows.append(Transaction(posted_date=posted, description=raw_desc, amount=amount))

    return rows
