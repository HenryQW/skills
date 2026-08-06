# beanquery BQL reference

BQL is SQL-like, not full SQL. Use live help for installed version:

```text
.help targets
.help from
.help where
```

## Statement forms

```sql
SELECT [DISTINCT] target [, target ...]
  [FROM table | filter [OPEN ON date] [CLOSE [ON date]] [CLEAR]]
  [WHERE filter]
  [GROUP BY expression [, expression ...] [HAVING aggregate_filter]]
  [ORDER BY expression [ASC|DESC] [, ...]]
  [PIVOT BY target, group_target]
  [LIMIT integer];

BALANCES [AT units|cost|value] [FROM filter] [WHERE filter];
JOURNAL [account-regex] [AT units|cost|value] [FROM filter];
PRINT [FROM filter];
```

Semicolon is optional. Keywords are case-insensitive. Query arguments passed to
CLI are joined with spaces; quote full query or pipe stdin.

## Tables and row grain

Without `FROM`, `SELECT` uses `postings`. Each row is one posting.

```sql
SELECT date, account, position;
SELECT date, description FROM entries;
SELECT account, open.date FROM #accounts;
SELECT 1 FROM #;
```

`FROM #` selects empty table with one placeholder row, useful for constants.
`SELECT *` on default postings means journal-style columns, not every column.
Use explicit targets when output contract matters.

`FROM #name` or quoted table names can select named tables. `.tables` gives
installed table names.

## FROM versus WHERE

On default postings:

- `WHERE` filters individual posting rows. Account filters usually belong here.
- `FROM` filter evaluates parent/directive fields such as `date`, `year`,
  `narration`, and `flag`. It can retain every posting in matching
  transactions.
- `FROM has_account('REGEX')` selects transactions containing matching account
  and retains their postings.

```sql
-- Only expense posting rows
SELECT date, account, position
WHERE account ~ '^Expenses:';

-- All postings for transactions containing expense account
SELECT date, account, position
FROM has_account('^Expenses:');
```

For `entries`, `FROM entries` changes row source to directives; `WHERE` then
filters directive rows.

## Date windows

```sql
FROM date >= 2024-01-01 AND date < 2025-01-01
FROM OPEN ON 2024-01-01 CLOSE ON 2024-12-31
FROM CLOSE ON 2024-12-31
FROM CLEAR
```

`OPEN ON` creates summarized opening context for activity before date.
`CLOSE ON` removes activity after close date and can add closing context.
`CLEAR` transfers final Income and Expenses balances to Equity. These are
accounting transformations, not simple predicates.

Use half-open date predicates for ordinary row filtering:

```sql
WHERE date >= 2024-01-01 AND date < 2025-01-01
```

## Targets and aliases

Targets can be columns, literals, expressions, or functions:

```sql
SELECT date, account AS account_name, number * 2 AS doubled;
SELECT DISTINCT currency ORDER BY currency;
SELECT date, narration ORDER BY date DESC, narration ASC;
```

`AS name` controls result header. `ORDER BY` accepts target name, 1-based target
index, or new expression. `GROUP BY` accepts target name, 1-based target index,
or expression.

Prefer explicit `GROUP BY` for stable agent queries:

```sql
SELECT account, sum(position) AS total
GROUP BY account
ORDER BY account;
```

`HAVING` must use aggregate expression:

```sql
SELECT account, sum(number) AS total
GROUP BY account
HAVING sum(number) != 0;
```

## Operators and literals

```text
=  !=  <  <=  >  >=       comparisons
~  !~  ?~                regex, negated regex, pattern against collection
IN  NOT IN               membership
IS NULL                  null test
AND OR NOT               boolean logic
+ - * / %                arithmetic
```

`~` and `!~` use case-insensitive regular-expression search. `?~` checks one
pattern against any value in a collection; `has_account()` wraps this pattern.
Strings use single quotes. Literals include integers, decimals, booleans,
`NULL`, and `YYYY-MM-DD` dates.

BQL propagates `NULL` through most functions and operators. Use `IS NULL`,
`IS NOT NULL`, `coalesce()`, or casts before arithmetic on optional values.

## Aggregation

Aggregates operate over input rows or groups:

```text
count(*)             all input rows
count(expr)          non-NULL expr rows
sum(expr)            numeric, amount, position, or inventory sum
first(expr)          first value seen
last(expr)           last value seen
min(expr), max(expr) extrema
```

`sum(position)` returns `Inventory`; `sum(cost(position))` returns cost-basis
inventory. `sum(number)` returns `Decimal`. Mixed aggregate/non-aggregate
queries should name every grouping column explicitly.

## Functions

Functions are type-dispatched. A valid function name with wrong argument type
fails compilation. See `references/schema.md` for value types and
`.help targets` for installed signatures.

```sql
SELECT year(date), quarter(date), root(account), number(position)
WHERE date >= 2024-01-01;
```

Metadata access:

```sql
meta('key')                    posting metadata
entry_meta('key')              parent transaction metadata
any_meta('key')                posting, then parent metadata
open_meta(account, 'key')      account open metadata
currency_meta('USD', 'key')    commodity metadata
```

Inventory and prices:

```sql
units(position)                strip cost
cost(position)                 cost basis
value(position, date)          market value
convert(position, 'USD')       convert using price map
getprice('AAPL', 'USD', date)  fetch price
only('USD', inventory)         one currency from inventory
empty(inventory)               inventory emptiness
```

## Subqueries and collections

Single-column subqueries can feed `IN`, `ANY`, and `ALL`:

```sql
SELECT account
WHERE account IN (SELECT account FROM #accounts);
```

Use `IN` for membership. Use `ANY`/`ALL` for comparison against subquery or
collection values. Subqueries must return one visible column.

## Convenience statements

`JOURNAL` expands to date, flag, payee, narration, account, position, and
running balance. Account argument is regex:

```sql
JOURNAL '^Assets:Checking$';
```

`BALANCES` groups positions by account and sorts by account hierarchy:

```sql
BALANCES AT cost FROM CLOSE ON 2024-12-31;
```

`PRINT` selects `entries` and renders original directives as Beancount:

```sql
PRINT FROM narration ~ 'invoice';
```
