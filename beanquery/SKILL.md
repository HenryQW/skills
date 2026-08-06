---
name: beanquery
description: Query existing Beancount ledgers with bean-query and Beancount Query Language (BQL). Use when an agent needs quick read-only ledger lookups, balances, journals, transaction searches, or CSV results.
---

# beanquery

Use `bean-query` for fast, read-only queries against an existing Beancount
ledger. Do not edit ledger files or use BQL `CREATE`/`INSERT`.

## Progressive loading

Read this file first. Load one reference only when task needs deeper detail:

- Exact tables, columns, types, or structured fields: [schema](references/schema.md)
- Ready-made reports and search patterns: [query cookbook](references/query-cookbook.md)
- BQL grammar, semantics, operators, and edge cases: [BQL](references/bql.md)

Do not load all references for routine query. Re-check live `.describe` output
when ledger schema or installed beanquery version may differ.

## Procedure

1. Resolve ledger path. Never guess it; ask user when unknown.
2. Check command and ledger:

   ```sh
   test -f "$LEDGER"
   command -v bean-query || python3 -m beanquery --help
   ```

3. Inspect schema when query shape is unclear:

   ```sh
   bean-query "$LEDGER" ".tables"
   bean-query "$LEDGER" ".describe postings"
   ```

4. Run one-shot query. Quote query as one shell argument:

   ```sh
   bean-query "$LEDGER" --format=csv \
     "SELECT date, account, position WHERE account ~ '^Expenses:' ORDER BY date;"
   ```

5. Use `--format=csv` for agent parsing. Use text for quick human inspection.
   Use `--numberify` when spreadsheet-like numeric currency columns are needed.
6. Load once without `--no-errors` when ledger health matters. Report Beancount
   validation errors; `--no-errors` only hides their output.

For long BQL, pipe stdin instead of fighting shell quoting:

```sh
cat <<'BQL' | bean-query "$LEDGER" --format=csv
SELECT date, account, number, currency
WHERE account ~ '^Expenses:'
ORDER BY date, account;
BQL
```

## Ledger model

Ledger source exposes:

```text
postings       default table; one row per transaction posting
entries        every Beancount directive
transactions   transaction directives
accounts       account open/close dates
commodities, prices, balances, notes, events, documents
```

Default queries scan `postings`. Common posting columns:

```text
date, year, month, day, flag, payee, narration, description
account, other_accounts, accounts, position, number, currency
cost_number, cost_currency, cost_date, price, weight, balance
posting_flag, meta, entry, filename, lineno, location, id, type, tags, links
```

Use `FROM entries` for directive-level rows. Use `FROM #` for one constant row;
without it, `SELECT 1` repeats once per posting.

## Core query rules

- `SELECT` queries default `postings`; each row is one posting.
- `WHERE account ~ 'REGEX'` filters posting rows. Use directive fields in
  `FROM` (`date`, `year`, `narration`, `flag`) when complete transactions must
  remain for balancing context.
- Use `BALANCES` for account totals, `JOURNAL` for account registers, and
  `PRINT` for Beancount-formatted directives.
- Use explicit `GROUP BY` for every non-aggregate target. `sum(position)` returns
  inventory; `sum(cost(position))` returns cost-basis inventory.
- `OPEN ON`, `CLOSE ON`, and `CLEAR` perform accounting transformations, not
  simple date predicates.
- `~` and `!~` are case-insensitive regex operators. Dates use `YYYY-MM-DD`.
  Check optional values with `IS NULL` or `IS NOT NULL`.

Load [query cookbook](references/query-cookbook.md) for task recipes. Load
[BQL reference](references/bql.md) for grammar, operators, functions, or edge
cases.

## Discovery and troubleshooting

```sh
bean-query "$LEDGER" ".tables"
bean-query "$LEDGER" ".describe postings"
bean-query "$LEDGER" ".describe entries"
```

Use `.help targets`, `.help from`, and `.help where` for complete type-aware
columns and functions. If result is empty, verify default table, column name,
regex, date range, and whether filter belongs in `FROM` or `WHERE`. Use
`.errors` to inspect load errors.

Interactive shell commands include `.tables`, `.describe`, `.errors`, `.reload`,
`.parse`, `.explain`, `.set pager false`, `.format csv`, `.output FILE`, and
`.run NAME` for Beancount `query` directives.
