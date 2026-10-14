# Expense Categorizer

A small utility that converts bank statement CSV exports into a single,
model-friendly JSON file for automatic expense categorization.

## What it does

1. Reads all `*.csv` bank statement files in this folder (e.g. `Apr 2026.csv`, `Aug 2026.csv`).
2. Cleans up the bank's export format — skips the account-info line, parses dates and amounts, and strips formatting from the `Amount` field.
3. Merges everything into one chronologically-sorted list of transactions.
4. Outputs `expenses.json`, where each transaction has an empty `"category": null` field ready to be filled in by a categorizing model (LLM, rule engine, etc.).

## Why

Bank CSV exports are messy to work with: an account header line before the
real header, quoted negative amounts, truncated merchant names, and no
categorization at all. This script normalizes that into a clean, structured
JSON with a summary block and an `instructions` field so a downstream model
knows exactly what categories to assign.

## Files

| File | Purpose |
|---|---|
| `expenses_to_json.py` | The converter script |
| `expenses.json` | Generated output (created when the script runs) |
| `*.csv` | Raw bank statement exports (KeyBank) |

## Requirements

- Python 3.8+ (standard library only — no dependencies to install)

## Usage

```bash
python expenses_to_json.py
```

That's it. It picks up every `.csv` in the folder, so to add a new month
just drop the new statement file in and re-run.

## Output format

```json
{
  "account": "Key Smart Checking",
  "generated_at": "2026-10-13T20:00:00",
  "summary": {
    "total_transactions": 83,
    "total_income": 5854.57,
    "total_spending": -4778.90,
    "net": 1075.67,
    "date_range": ["2026-04-02", "2026-09-01"]
  },
  "instructions": "Categorize each transaction by filling in 'category' using these categories: income, rent, utilities, groceries, dining_out, transportation, shopping, subscriptions, entertainment, health, transfers, fees, other. Amounts are negative for spending, positive for deposits.",
  "transactions": [
    {
      "date": "2026-04-02",
      "amount": -34.23,
      "description": "TARGET.COMBROOKLYN PARKMN US",
      "source_file": "Apr 2026.csv",
      "category": null
    }
  ]
}
```

### Transaction fields

| Field | Type | Notes |
|---|---|---|
| `date` | string | ISO format (`YYYY-MM-DD`) |
| `amount` | number | Negative = spending, positive = deposit |
| `description` | string | Merchant/description as printed by the bank (often truncated) |
| `source_file` | string | Which CSV the transaction came from |
| `category` | string \| null | Filled in by the categorizing model |

## Customizing

- **Categories:** edit the `instructions` string in `expenses_to_json.py` to change the category list the model is told to use.
- **Output filename:** change `OUTPUT_FILE` at the top of the script.
- **Account name:** the `"account"` field is currently hardcoded to the KeyBank account; adjust if you mix statements from other banks.

## Notes

- Statement files can overlap (e.g. the April export includes early-May transactions). Transactions from overlapping dates appear once per file — they are separate statements, not duplicates.
- Merchant descriptions are truncated by the bank (e.g. `POS MAC WAL-MART #4053 INDIANAPOL IN`), which is expected — the categorizing model should handle that.
