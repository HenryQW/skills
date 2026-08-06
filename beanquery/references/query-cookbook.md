# beanquery query cookbook

Set `LEDGER` to confirmed ledger path. Use `--format=csv` when agent must parse
results. Add `--numberify` for numeric currency columns.

## Discover ledger shape

```sh
bean-query "$LEDGER" ".tables"
bean-query "$LEDGER" ".describe postings"
bean-query "$LEDGER" ".describe entries"
bean-query "$LEDGER" ".errors"
```

## Search postings

```sql
SELECT date, description, account, position
WHERE account ~ '^Expenses:'
ORDER BY date, account;
```

```sql
SELECT date, payee, narration, account, number, currency
WHERE account = 'Assets:Checking'
ORDER BY date;
```

`WHERE` returns matching posting rows. It can omit balancing postings.

## Keep complete transactions

Use `FROM` with parent-transaction fields when transaction context matters:

```sql
SELECT date, description, account, position
FROM date >= 2024-01-01 AND date < 2025-01-01
WHERE account ~ '^Expenses:'
ORDER BY date, account;
```

Use `has_account()` to select transactions containing an account pattern while
retaining every posting in those transactions:

```sql
SELECT date, description, account, position
FROM has_account('^Expenses:')
ORDER BY date, account;
```

## Totals

```sql
SELECT account, sum(position) AS total
WHERE account ~ '^Expenses:'
GROUP BY account
ORDER BY account;
```

```sql
SELECT yearmonth(date) AS month, sum(number) AS total
WHERE account ~ '^Expenses:' AND currency = 'USD'
GROUP BY yearmonth(date)
ORDER BY month;
```

```sql
SELECT currency, sum(number) AS total
WHERE account = 'Assets:Checking'
GROUP BY currency
ORDER BY currency;
```

`sum(position)` and `sum(cost(position))` return inventories. Use `number()`
or posting `number` for scalar totals.

## Balances and reports

```sql
BALANCES;
BALANCES AT units;
BALANCES AT cost FROM CLOSE ON 2024-12-31;
BALANCES AT value FROM CLOSE ON 2024-12-31;
```

```sql
SELECT account, sum(cost(position)) AS total
FROM OPEN ON 2024-01-01 CLOSE ON 2024-12-31
WHERE account ~ '^(Income|Expenses):'
GROUP BY account
ORDER BY account;
```

`OPEN` summarizes activity before start date. `CLOSE` limits activity at end
date. `CLEAR` closes Income and Expenses into Equity.

## Journals

```sql
JOURNAL 'Assets:Checking';
JOURNAL 'Assets:Checking'
FROM OPEN ON 2024-01-01 CLOSE ON 2024-12-31;
JOURNAL 'Assets:Brokerage' AT cost;
```

Account argument is regex. Use anchors when exact account matching matters:
`'^Assets:Checking$'`.

## Directives and Beancount output

```sql
SELECT type, date, filename, lineno, description
FROM entries
WHERE type = 'transaction'
ORDER BY date, lineno;
```

```sql
SELECT date, currency, amount
FROM #prices
WHERE currency = 'USD'
ORDER BY date;
```

```sql
PRINT FROM date = 2024-01-15;
PRINT FROM narration ~ 'invoice';
```

`PRINT` emits matching entries in Beancount syntax. Use
`--format=beancount` when calling from CLI.

## Accounts and metadata

```sql
SELECT account, open.date, close.date
FROM #accounts
ORDER BY account;
```

```sql
SELECT date, account, any_meta('project') AS project
WHERE any_meta('project') IS NOT NULL
ORDER BY date;
```

```sql
SELECT date, account, entry_meta('location') AS location
WHERE entry_meta('location') IS NOT NULL;
```

`meta(key)` reads posting metadata. `entry_meta(key)` reads parent transaction
metadata. `any_meta(key)` checks posting metadata, then parent metadata.

## Currency and holdings

```sql
SELECT account, currency, number
WHERE account ~ '^Assets:'
ORDER BY account, currency;
```

```sql
SELECT date, position, cost(position) AS cost_basis,
       value(position, date) AS market_value
WHERE account = 'Assets:Brokerage'
ORDER BY date;
```

```sql
SELECT date, getprice('AAPL', 'USD', date) AS usd_price
FROM #prices
WHERE currency = 'AAPL'
ORDER BY date;
```

Price functions need matching entries and price-map data. Missing prices yield
`NULL` or conversion errors; inspect `prices` first.

## Output wrappers

```sh
bean-query "$LEDGER" --format=csv <<'BQL'
SELECT date, account, number, currency
WHERE account ~ '^Expenses:'
ORDER BY date, account;
BQL

bean-query "$LEDGER" --format=csv --numberify \
  "$QUERY" > report.csv
```

For empty output, check table, column, regex, date range, and `FROM` versus
`WHERE` placement before changing query.

## Named queries

Ledger `query` directives can be discovered and run in shell:

```text
.run
.run taxes
.run *
```
