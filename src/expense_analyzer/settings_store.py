from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class BudgetSettings:
    income_target: float
    savings_goal: float
    category_budgets: dict[str, float]


DEFAULT_SETTINGS = BudgetSettings(
    income_target=0.0,
    savings_goal=0.0,
    category_budgets={
        "Rent": 0.0,
        "Groceries": 0.0,
        "Coffee": 0.0,
        "Transport": 0.0,
        "Subscriptions": 0.0,
        "Uncategorized": 0.0,
    },
)


def load_settings(path: Path) -> BudgetSettings:
    if not path.exists():
        return DEFAULT_SETTINGS

    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return DEFAULT_SETTINGS

    income_target = float(data.get("income_target", 0.0))
    savings_goal = float(data.get("savings_goal", 0.0))
    category_budgets = data.get("category_budgets", {})

    if not isinstance(category_budgets, dict):
        category_budgets = {}

    # Ensure floats
    cleaned: dict[str, float] = {}
    for k, v in category_budgets.items():
        try:
            cleaned[str(k)] = float(v)
        except Exception:
            cleaned[str(k)] = 0.0

    # Merge with defaults to keep known categories
    merged = dict(DEFAULT_SETTINGS.category_budgets)
    merged.update(cleaned)

    return BudgetSettings(
        income_target=income_target,
        savings_goal=savings_goal,
        category_budgets=merged,
    )


def save_settings(path: Path, settings: BudgetSettings) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(settings), indent=2), encoding="utf-8")
