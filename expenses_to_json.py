#!/usr/bin/env python3
"""
Convert bank statement CSV exports into a single JSON file that's easy
for a model to categorize.

- Reads all *.csv files in the script's directory (bank statement exports).
- Skips the account-info line (e.g. "141942055965,Key Smart Checking").
- Outputs transactions sorted by date, each with an empty "category" field.
"""

import csv
import json
import re
from datetime import datetime
from pathlib import Path

OUTPUT_FILE = "expenses.json"


def parse_csv(path: Path) -> list[dict]:
    """Parse one bank statement CSV and return a list of transaction dicts."""
    transactions = []
    with path.open(newline="", encoding="utf-8-sig") as f:
        lines = [line for line in f if line.strip()]
    # Find the header line (skips blank lines and the account-info line,
    # e.g. "141942055965,Key Smart Checking").
    for i, line in enumerate(lines):
        if "Date" in line:
            reader = csv.DictReader(lines[i:])
            break
    else:
        raise ValueError(f"No 'Date' header line found in {path.name}")

    for row in reader:
        date_raw = (row.get("Date") or "").strip()
        amount_raw = (row.get("Amount") or "").strip().replace("$", "").replace(",", "")
        description = (row.get("Description") or "").strip()
        if not date_raw:
            continue
        try:
            date = datetime.strptime(date_raw, "%m/%d/%Y").date().isoformat()
        except ValueError:
            date = date_raw
        try:
            amount = float(amount_raw)
        except ValueError:
            amount = None
        transactions.append(
            {
                "date": date,
                "amount": amount,
                "description": description,
                "source_file": path.name,
                "category": None,  # <-- filled in by the categorizing model
            }
        )
    return transactions


def main() -> None:
    here = Path(__file__).parent
    csv_files = sorted(here.glob("*.csv"))
    if not csv_files:
        raise SystemExit(f"No CSV files found in {here}")

    all_transactions: list[dict] = []
    for csv_file in csv_files:
        txns = parse_csv(csv_file)
        print(f"{csv_file.name}: {len(txns)} transactions")
        all_transactions.extend(txns)

    # Sort chronologically (oldest first).
    all_transactions.sort(key=lambda t: t["date"])

    income = sum(t["amount"] for t in all_transactions if (t["amount"] or 0) > 0)
    spending = sum(t["amount"] for t in all_transactions if (t["amount"] or 0) < 0)

    data = {
        "account": "Key Smart Checking",
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "total_transactions": len(all_transactions),
            "total_income": round(income, 2),
            "total_spending": round(spending, 2),
            "net": round(income + spending, 2),
            "date_range": [
                min(t["date"] for t in all_transactions),
                max(t["date"] for t in all_transactions),
            ],
        },
        "instructions": (
            "Categorize each transaction by filling in 'category' using these "
            "categories: income, rent, utilities, groceries, dining_out, "
            "transportation, shopping, subscriptions, entertainment, "
            "health, transfers, fees, other. Amounts are negative for "
            "spending, positive for deposits."
        ),
        "transactions": all_transactions,
    }

    out = here / OUTPUT_FILE
    out.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"\nWrote {len(all_transactions)} transactions to {out}")


if __name__ == "__main__":
    main()
