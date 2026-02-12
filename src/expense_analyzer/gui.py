from __future__ import annotations

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

from expense_analyzer.parser import load_transactions
from expense_analyzer.normalize import normalize_description
from expense_analyzer.categorize import categorize_transaction
from expense_analyzer.analyze import build_monthly_summary, detect_unusual_spending
from expense_analyzer.storage import load_manual_entries, save_manual_entries

APP_ROOT = Path(__file__).resolve().parents[2]  # project root
MANUAL_PATH = APP_ROOT / "data" / "manual_entries.json"
SETTINGS_PATH = APP_ROOT / "data" / "settings.json"


class ExpenseAnalyzerApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Expense Analyzer")
        self.root.geometry("980x600")

        self.csv_path: Path | None = None
        self.csv_transactions = []
        self.manual_transactions = []
        self._row_meta: dict[str, tuple[str, int]] = {}

        self.status_var = tk.StringVar(value="Ready. Load a CSV to begin.")

        from expense_analyzer.settings_store import load_settings

        self.settings = load_settings(SETTINGS_PATH)

        self._build_ui()
        self._update_counts()
        
        self.manual_transactions = load_manual_entries(MANUAL_PATH)
        if self.manual_transactions:
            self.set_status(f"Loaded {len(self.manual_transactions)} manual entries.")
            self._refresh_all_views()

    def _build_ui(self) -> None:
        # Top bar
        top = ttk.Frame(self.root, padding=10)
        top.pack(fill="x")

        ttk.Button(top, text="Load CSV", command=self.load_csv).pack(side="left")
        ttk.Button(top, text="Add Expense", command=self.add_expense_dialog).pack(side="left", padx=(8, 0))
        ttk.Button(top, text="Clear Entry", command=self.clear_selected_entry).pack(side="left", padx=(8, 0))
        ttk.Button(top, text="Export CSV", command=self.export_combined_csv).pack(side="left", padx=(8, 0))
        self.file_label = ttk.Label(top, text="No file loaded", padding=(10, 0))
        self.file_label.pack(side="left")
        self.count_label = ttk.Label(top, text="CSV: 0 | Manual: 0 | Total: 0", padding=(14, 0))
        self.count_label.pack(side="left")

        # Tabs
        self.tabs = ttk.Notebook(self.root)
        self.tabs.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.tab_transactions = ttk.Frame(self.tabs, padding=10)
        self.tab_summary = ttk.Frame(self.tabs, padding=10)
        self.tab_alerts = ttk.Frame(self.tabs, padding=10)
        self.tab_budgets = ttk.Frame(self.tabs, padding=10)

        self.tabs.add(self.tab_transactions, text="Transactions")
        self.tabs.add(self.tab_summary, text="Summary")
        self.tabs.add(self.tab_alerts, text="Alerts")
        self.tabs.add(self.tab_budgets, text="Budgets & Goals")

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

        self._build_budgets_tab()

        # Status bar
        status = ttk.Frame(self.root, padding=(10, 6))
        status.pack(fill="x")
        ttk.Label(status, textvariable=self.status_var).pack(side="left")

    def _build_budgets_tab(self) -> None:
        from expense_analyzer.settings_store import DEFAULT_SETTINGS
    
        # Vars
        self.income_target_var = tk.StringVar(value="")
        self.savings_goal_var = tk.StringVar(value="")
    
        top = ttk.Frame(self.tab_budgets)
        top.pack(fill="x")
    
        ttk.Label(top, text="Income target (monthly)").grid(row=0, column=0, sticky="w", pady=4)
        ttk.Entry(top, textvariable=self.income_target_var, width=14).grid(row=0, column=1, sticky="w", padx=8)
    
        ttk.Label(top, text="Savings goal (monthly)").grid(row=0, column=2, sticky="w", pady=4, padx=(20, 0))
        ttk.Entry(top, textvariable=self.savings_goal_var, width=14).grid(row=0, column=3, sticky="w", padx=8)
    
        ttk.Button(top, text="Save", command=self.save_budget_settings).grid(row=0, column=4, padx=(20, 0))
    
        # Budgets table
        table_frame = ttk.Frame(self.tab_budgets)
        table_frame.pack(fill="both", expand=True, pady=(12, 0))
    
        self.budget_tree = ttk.Treeview(
            table_frame,
            columns=("category", "budget"),
            show="headings",
            height=10,
        )
        self.budget_tree.pack(fill="both", expand=True)
    
        self.budget_tree.heading("category", text="Category")
        self.budget_tree.heading("budget", text="Monthly Budget")
        self.budget_tree.column("category", width=220, anchor="w")
        self.budget_tree.column("budget", width=140, anchor="e")
    
        # Double-click edit
        self.budget_tree.bind("<Double-1>", self._edit_budget_cell)
    
        # Progress panel
        self.budget_progress_text = tk.Text(self.tab_budgets, height=10, wrap="word")
        self.budget_progress_text.pack(fill="x", pady=(12, 0))
    
        self._load_settings_into_ui()
        self._refresh_budget_progress()

        self._refresh_budget_progress()
      
    def set_status(self, msg: str) -> None:
        self.status_var.set(msg)
        self.root.update_idletasks()

    def _update_counts(self) -> None:
        """
        Update the top-bar counter showing CSV/manual/total transaction counts.
        """
        csv_count = len(self.csv_transactions)
        manual_count = len(self.manual_transactions)
        total = csv_count + manual_count
        self.count_label.config(text=f"CSV: {csv_count} | Manual: {manual_count} | Total: {total}")

    def load_csv(self) -> None:
        file_path = filedialog.askopenfilename(
            title="Select bank statement CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not file_path:
            return

        try:
            self.csv_path = Path(file_path)
            self.csv_transactions = load_transactions(self.csv_path)
        except Exception as e:
            messagebox.showerror("Could not load CSV", str(e))
            self.set_status("Error loading file.")
            return

        self.file_label.config(text=self.csv_path.name)
        self.set_status(
            f"Loaded {len(self.csv_transactions)} CSV transactions (+ {len(self.manual_transactions)} manual)."
        )         
        self._refresh_all_views()

    def add_expense_dialog(self) -> None:
        """
        Open a small dialog to manually add an expense.
        Only asks for date, amount, and description. Category is inferred automatically.
        """
        win = tk.Toplevel(self.root)
        win.title("Add Expense")
        win.geometry("420x220")
        win.transient(self.root)
        win.grab_set()
    
        # Variables
        date_var = tk.StringVar(value="")
        amount_var = tk.StringVar(value="")
        desc_var = tk.StringVar(value="")
    
        # Layout
        frame = ttk.Frame(win, padding=12)
        frame.pack(fill="both", expand=True)
    
        ttk.Label(frame, text="Date (YYYY-MM-DD)").grid(row=0, column=0, sticky="w")
        date_entry = ttk.Entry(frame, textvariable=date_var, width=24)
        date_entry.grid(row=0, column=1, sticky="ew", pady=6)
    
        ttk.Label(frame, text="Amount").grid(row=1, column=0, sticky="w")
        amount_entry = ttk.Entry(frame, textvariable=amount_var, width=24)
        amount_entry.grid(row=1, column=1, sticky="ew", pady=6)
    
        ttk.Label(frame, text="Merchant / Description").grid(row=2, column=0, sticky="w")
        desc_entry = ttk.Entry(frame, textvariable=desc_var, width=24)
        desc_entry.grid(row=2, column=1, sticky="ew", pady=6)
    
        frame.columnconfigure(1, weight=1)
    
        def on_add() -> None:
            from datetime import date
            from expense_analyzer.parser import Transaction
    
            raw_date = date_var.get().strip()
            raw_amount = amount_var.get().strip()
            raw_desc = desc_var.get().strip()
    
            if not raw_date or not raw_amount or not raw_desc:
                messagebox.showwarning("Missing info", "Please fill date, amount, and description.")
                return
    
            # Parse date
            try:
                posted = date.fromisoformat(raw_date)
            except ValueError:
                messagebox.showerror("Invalid date", "Date must be in YYYY-MM-DD format.")
                return
    
            # Parse amount
            try:
                amount = float(raw_amount)
            except ValueError:
                messagebox.showerror("Invalid amount", "Amount must be a number, e.g. -12.50")
                return
    
            # Force expenses to be negative (UX: user can type positive, we convert)
            if amount > 0:
                amount = -amount
    
            txn = Transaction(posted_date=posted, description=raw_desc, amount=amount)
            self.manual_transactions.append(txn)
            save_manual_entries(MANUAL_PATH, self.manual_transactions)
            
            self.set_status("Added expense (saved).")
            self._refresh_all_views()
    
            win.destroy()
    
        btns = ttk.Frame(frame)
        btns.grid(row=3, column=0, columnspan=2, sticky="e", pady=(12, 0))
    
        ttk.Button(btns, text="Cancel", command=win.destroy).pack(side="right")
        ttk.Button(btns, text="Add", command=on_add).pack(side="right", padx=(0, 8))
    
        # UX: focus first field
        date_entry.focus_set()

    def export_combined_csv(self) -> None:
        """
        Export the combined (CSV + manual) dataset into a new CSV file with
        normalized merchant and inferred category columns.
        """
        import csv
    
        transactions = self.csv_transactions + self.manual_transactions
        if not transactions:
            messagebox.showinfo("Export CSV", "There are no transactions to export yet.")
            return
    
        default_name = "expense_analyzer_export.csv"
        if self.csv_path:
            default_name = f"cleaned_{self.csv_path.stem}.csv"
    
        out_path_str = filedialog.asksaveasfilename(
            title="Export combined dataset",
            defaultextension=".csv",
            initialfile=default_name,
            filetypes=[("CSV files", "*.csv")],
        )
        if not out_path_str:
            return
    
        out_path = Path(out_path_str)
    
        try:
            with out_path.open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=["date", "amount", "merchant", "category", "description"],
                )
                writer.writeheader()
    
                for txn in transactions:
                    merchant = normalize_description(txn.description)
                    category = categorize_transaction(txn)
                    writer.writerow(
                        {
                            "date": str(txn.posted_date),
                            "amount": f"{txn.amount:.2f}",
                            "merchant": merchant,
                            "category": category,
                            "description": txn.description,
                        }
                    )
    
            self.set_status(f"Exported CSV: {out_path.name}")
            messagebox.showinfo("Export CSV", f"Saved:\n{out_path}")
        except Exception as e:
            messagebox.showerror("Export failed", str(e))

    def clear_selected_entry(self) -> None:
        """
        Delete the selected transaction row from the current session.
        Manual entries are removed permanently from storage.
        CSV entries are removed only from the loaded CSV session list.
        """
        selection = self.txn_tree.selection()
        if not selection:
            messagebox.showinfo("Clear Entry", "Select a transaction in the Transactions tab first.")
            return
    
        item_id = selection[0]
        meta = self._row_meta.get(item_id)
        if not meta:
            messagebox.showerror("Clear Entry", "Could not resolve the selected row. Try refreshing.")
            return
    
        source, idx = meta
    
        values = self.txn_tree.item(item_id, "values")
        date_str = values[0] if len(values) > 0 else ""
        amount_str = values[1] if len(values) > 1 else ""
        merchant_str = values[2] if len(values) > 2 else ""
    
        if source == "csv":
            confirm = messagebox.askyesno(
                "Clear Entry (CSV)",
                f"This will remove the entry from the current session only.\n"
                f"It will NOT modify your original bank CSV.\n\n"
                f"{date_str} | {amount_str} | {merchant_str}\n\n"
                f"Continue?"
            )
            if not confirm:
                return
    
            # Remove from in-memory CSV list
            if 0 <= idx < len(self.csv_transactions):
                self.csv_transactions.pop(idx)
    
            self.set_status("Removed CSV entry (session only).")
            self._refresh_all_views()
            return
    
        # manual
        confirm = messagebox.askyesno(
            "Clear Entry (Manual)",
            f"This will permanently delete this manual entry.\n\n"
            f"{date_str} | {amount_str} | {merchant_str}\n\n"
            f"Continue?"
        )
        if not confirm:
            return
    
        if 0 <= idx < len(self.manual_transactions):
            self.manual_transactions.pop(idx)
    
        # Persist manual deletion
        from expense_analyzer.storage import save_manual_entries
        save_manual_entries(MANUAL_PATH, self.manual_transactions)
    
        self.set_status("Deleted manual entry (saved).")
        self._refresh_all_views()
       
    def clear_manual_entries(self) -> None:

        """
        Clear all manual entries from memory and disk.
        """
        if not self.manual_transactions:
            messagebox.showinfo("Clear manual entries", "There are no manual entries to clear.")
            return
    
        confirm = messagebox.askyesno(
            "Clear manual entries",
            "This will delete ALL manual entries you added manually.\n\n"
            "CSV-loaded transactions will not be affected.\n\n"
            "Continue?"
        )
        if not confirm:
            return
    
        # Clear in-memory list
        self.manual_transactions = []
    
        # Remove file on disk (if present)
        try:
            if MANUAL_PATH.exists():
                MANUAL_PATH.unlink()
        except Exception as e:
            messagebox.showerror("Error", f"Could not delete manual entries file:\n{e}")
            return
    
        self.set_status("Manual entries cleared.")
        self._refresh_all_views()
    
    def _load_settings_into_ui(self) -> None:
        self.income_target_var.set(f"{self.settings.income_target:.2f}")
        self.savings_goal_var.set(f"{self.settings.savings_goal:.2f}")
    
        for item in self.budget_tree.get_children():
            self.budget_tree.delete(item)
    
        for cat, budget in sorted(self.settings.category_budgets.items()):
            self.budget_tree.insert("", "end", values=(cat, f"{budget:.2f}"))

    def save_budget_settings(self) -> None:
        from expense_analyzer.settings_store import BudgetSettings, save_settings
    
        # Parse top fields
        try:
            income_target = float(self.income_target_var.get().strip() or "0")
            savings_goal = float(self.savings_goal_var.get().strip() or "0")
        except ValueError:
            messagebox.showerror("Invalid number", "Income target and savings goal must be numbers.")
            return
    
        # Read budgets table
        budgets: dict[str, float] = {}
        for item in self.budget_tree.get_children():
            cat, budget_str = self.budget_tree.item(item, "values")
            try:
                budgets[str(cat)] = float(str(budget_str))
            except ValueError:
                budgets[str(cat)] = 0.0
    
        self.settings = BudgetSettings(
            income_target=income_target,
            savings_goal=savings_goal,
            category_budgets=budgets,
        )
    
        messagebox.showinfo("Debug", f"Saving settings to:\n{SETTINGS_PATH}")

        save_settings(SETTINGS_PATH, self.settings)
        self.set_status("Saved budgets & goals.")
        self._refresh_budget_progress()
    
    def _edit_budget_cell(self, event) -> None:
        item = self.budget_tree.identify_row(event.y)
        col = self.budget_tree.identify_column(event.x)
    
        # Only edit the "budget" column (#2)
        if not item or col != "#2":
            return
    
        x, y, w, h = self.budget_tree.bbox(item, col)
        current = self.budget_tree.set(item, "budget")
    
        entry = ttk.Entry(self.budget_tree)
        entry.place(x=x, y=y, width=w, height=h)
        entry.insert(0, current)
        entry.focus_set()
    
        def commit_edit(_event=None) -> None:
            val = entry.get().strip()
            try:
                float(val or "0")
            except ValueError:
                messagebox.showerror("Invalid budget", "Budget must be a number.")
                entry.destroy()
                return
    
            self.budget_tree.set(item, "budget", val)
            entry.destroy()
            self._refresh_budget_progress()
    
        entry.bind("<Return>", commit_edit)
        entry.bind("<FocusOut>", commit_edit)

    def _refresh_budget_progress(self) -> None:
        self.budget_progress_text.delete("1.0", "end")
    
        transactions = self.csv_transactions + self.manual_transactions
        if not transactions:
            self.budget_progress_text.insert("end", "Load a CSV or add expenses to see progress.\n")
            return
    
        # Pick the most recent month in data
        summaries = build_monthly_summary(transactions)
        if not summaries:
            return
    
        latest_month = sorted(summaries.keys())[-1]
        s = summaries[latest_month]
    
        # Read current settings (if not loaded yet, act like zeros)
        income_target = 0.0
        savings_goal = 0.0
        budgets: dict[str, float] = {}
    
        if hasattr(self, "settings"):
            income_target = float(self.settings.income_target)
            savings_goal = float(self.settings.savings_goal)
            budgets = dict(self.settings.category_budgets)
    
        lines = []
        lines.append(f"Month: {latest_month}\n")
        lines.append(f"Income: {s.income_total:.2f} / Target: {income_target:.2f}\n")
        lines.append(f"Expenses: {s.expense_total:.2f}\n")
        lines.append(f"Net: {s.net_total:.2f} / Savings goal: {savings_goal:.2f}\n\n")
    
        lines.append("Budgets by category:\n")
        for cat, spent in s.by_category.items():
            budget = float(budgets.get(cat, 0.0))
            remaining = budget - spent
            lines.append(f"  - {cat}: spent {spent:.2f} / budget {budget:.2f} (remaining {remaining:.2f})\n")
    
        self.budget_progress_text.insert("end", "".join(lines))

    def _refresh_all_views(self) -> None:
        self._update_counts()
        self._populate_transactions()
        self._populate_summary()
        self._populate_alerts()

    def _populate_transactions(self) -> None:
        for item in self.txn_tree.get_children():
            self.txn_tree.delete(item)

        self._row_meta.clear()

        rows = []
        for i, txn in enumerate(self.csv_transactions):
            rows.append(("csv", i, txn))
        for i, txn in enumerate(self.manual_transactions):
            rows.append(("manual", i, txn))
    
        for source, idx, txn in rows:
            merchant = normalize_description(txn.description)
            category = categorize_transaction(txn)
    
            item_id = self.txn_tree.insert(
                "",
                "end",
                values=(str(txn.posted_date), f"{txn.amount:.2f}", merchant, category, txn.description),
            )
    
            self._row_meta[item_id] = (source, idx)

    def _populate_summary(self) -> None:
        self.summary_text.delete("1.0", "end")

        transactions = self.csv_transactions + self.manual_transactions
        if not transactions:
            return

        summaries = build_monthly_summary(transactions)

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

        transactions = self.csv_transactions + self.manual_transactions
        if not transactions:
            return

        alerts_by_month = detect_unusual_spending(transactions)

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
