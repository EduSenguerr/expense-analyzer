from __future__ import annotations

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

from expense_analyzer.parser import load_transactions
from expense_analyzer.normalize import normalize_description
from expense_analyzer.categorize import categorize_transaction
from expense_analyzer.analyze import build_monthly_summary, detect_unusual_spending


class ExpenseAnalyzerApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Expense Analyzer")
        self.root.geometry("980x600")

        self.csv_path: Path | None = None
        self.transactions = []

        self.status_var = tk.StringVar(value="Ready. Load a CSV to begin.")
        self._build_ui()

    def _build_ui(self) -> None:
        # Top bar
        top = ttk.Frame(self.root, padding=10)
        top.pack(fill="x")

        ttk.Button(top, text="Load CSV", command=self.load_csv).pack(side="left")
        self.file_label = ttk.Label(top, text="No file loaded", padding=(10, 0))
        self.file_label.pack(side="left")

        # Tabs
        self.tabs = ttk.Notebook(self.root)
        self.tabs.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.tab_transactions = ttk.Frame(self.tabs, padding=10)
        self.tab_summary = ttk.Frame(self.tabs, padding=10)
        self.tab_alerts = ttk.Frame(self.tabs, padding=10)

        self.tabs.add(self.tab_transactions, text="Transactions")
        self.tabs.add(self.tab_summary, text="Summary")
        self.tabs.add(self.tab_alerts, text="Alerts")

        # Transactions table
        self.txn_tree = ttk.Treeview(
            self.tab_transactions,
            columns=("date", "amount", "merchant", "category", "description"),
            show="headings",
            height=18,
        )
        self.txn_tree.pack(fill="both", expand=True)

        self.txn_tree.heading("date", text="Date")
        self.txn_tree.heading("amount", text="Amount")
        self.txn_tree.heading("merchant", text="Merchant")
        self.txn_tree.heading("category", text="Category")
        self.txn_tree.heading("description", text="Description")

        self.txn_tree.column("date", width=90, anchor="w")
        self.txn_tree.column("amount", width=90, anchor="e")
        self.txn_tree.column("merchant", width=160, anchor="w")
        self.txn_tree.column("category", width=120, anchor="w")
        self.txn_tree.column("description", width=480, anchor="w")

        # Summary text (simple for v0.1)
        self.summary_text = tk.Text(self.tab_summary, height=20, wrap="word")
        self.summary_text.pack(fill="both", expand=True)

        # Alerts table
        self.alert_tree = ttk.Treeview(
            self.tab_alerts,
            columns=("date", "category", "merchant", "amount", "reason"),
            show="headings",
            height=18,
        )
        self.alert_tree.pack(fill="both", expand=True)

        self.alert_tree.heading("date", text="Date")
        self.alert_tree.heading("category", text="Category")
        self.alert_tree.heading("merchant", text="Merchant")
        self.alert_tree.heading("amount", text="Amount")
        self.alert_tree.heading("reason", text="Reason")

        self.alert_tree.column("date", width=90, anchor="w")
        self.alert_tree.column("category", width=140, anchor="w")
        self.alert_tree.column("merchant", width=200, anchor="w")
        self.alert_tree.column("amount", width=90, anchor="e")
        self.alert_tree.column("reason", width=420, anchor="w")

        # Status bar
        status = ttk.Frame(self.root, padding=(10, 6))
        status.pack(fill="x")
        ttk.Label(status, textvariable=self.status_var).pack(side="left")

    def set_status(self, msg: str) -> None:
        self.status_var.set(msg)
        self.root.update_idletasks()

    def load_csv(self) -> None:
        file_path = filedialog.askopenfilename(
            title="Select bank statement CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not file_path:
            return

        try:
            self.csv_path = Path(file_path)
            self.transactions = load_transactions(self.csv_path)
        except Exception as e:
            messagebox.showerror("Could not load CSV", str(e))
            self.set_status("Error loading file.")
            return

        self.file_label.config(text=self.csv_path.name)
        self.set_status(f"Loaded {len(self.transactions)} transactions.")
        self._refresh_all_views()

    def _refresh_all_views(self) -> None:
        self._populate_transactions()
        self._populate_summary()
        self._populate_alerts()

    def _populate_transactions(self) -> None:
        for item in self.txn_tree.get_children():
            self.txn_tree.delete(item)

        for txn in self.transactions:
            merchant = normalize_description(txn.description)
            category = categorize_transaction(txn)
            self.txn_tree.insert(
                "",
                "end",
                values=(str(txn.posted_date), f"{txn.amount:.2f}", merchant, category, txn.description),
            )

    def _populate_summary(self) -> None:
        self.summary_text.delete("1.0", "end")
        if not self.transactions:
            return

        summaries = build_monthly_summary(self.transactions)

        for month, s in summaries.items():
            self.summary_text.insert("end", f"{month}\n")
            self.summary_text.insert("end", f"  Income:   {s.income_total:.2f}\n")
            self.summary_text.insert("end", f"  Expenses: {s.expense_total:.2f}\n")
            self.summary_text.insert("end", f"  Net:      {s.net_total:.2f}\n")
            self.summary_text.insert("end", "  Spending by category:\n")
            for cat, total in s.by_category.items():
                self.summary_text.insert("end", f"    - {cat}: {total:.2f}\n")
            self.summary_text.insert("end", "\n")

    def _populate_alerts(self) -> None:
        for item in self.alert_tree.get_children():
            self.alert_tree.delete(item)

        if not self.transactions:
            return

        alerts_by_month = detect_unusual_spending(self.transactions)

        # show all alerts across months for now (v0.1)
        for month, alerts in alerts_by_month.items():
            for a in alerts:
                self.alert_tree.insert(
                    "",
                    "end",
                    values=(a.posted_date, a.category, a.merchant, f"{a.amount:.2f}", a.reason),
                )


def main() -> None:
    root = tk.Tk()
    app = ExpenseAnalyzerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
