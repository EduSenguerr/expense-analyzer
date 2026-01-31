from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from expense_analyzer.analyze import Summary


def ensure_reports_dir(out_dir: Path) -> Path:
    """
    Ensure an output directory exists and return its resolved path.
    """
    out_dir = out_dir.expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def write_monthly_summary_json(reports_dir: Path, summary: Summary) -> Path:
    """
    Write a monthly summary to reports/ as JSON and return the created file path.
    """
    out_path = reports_dir / f"summary_{summary.month}.json"
    payload = asdict(summary)

    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return out_path
