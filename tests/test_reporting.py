from expense_analyzer.reporting import write_monthly_summary_json
from expense_analyzer.analyze import Summary
from pathlib import Path


def test_write_monthly_summary_json(tmp_path: Path) -> None:
    summary = Summary(
        month="2026-01",
        income_total=1000.0,
        expense_total=200.0,
        net_total=800.0,
        by_category={"Rent": 200.0},
    )

    out = write_monthly_summary_json(tmp_path, summary)
    assert out.exists()
    text = out.read_text(encoding="utf-8")
    assert '"month": "2026-01"' in text
