# beanquery schema reference

Ledger source tables, columns, and nominal compiler types. Nullability varies by
entry type; run `.describe TABLE` against installed beanquery for live schema.

## Type key

```text
str          string
int          integer
Decimal      exact decimal number
date         YYYY-MM-DD date
Amount       number + currency
Position     units + optional cost
Inventory    collection of positions
set[str]     string set
dict         metadata map
```

## Tables

### `postings` (default)

One row per posting. Parent transaction fields repeat on each posting.

```text
type: str                 id: str
 date: date               year/month/day: int
filename: str?            lineno: int?              location: str?
flag: str                 payee: str?               narration: str?
description: str          tags: set[str]             links: set[str]
posting_flag: str         account: str              other_accounts: set[str]
number: Decimal           currency: str
cost_number: Decimal?     cost_currency: str?       cost_date: date?
cost_label: str           position: Position         price: Amount?
weight: Amount?           balance: Inventory         meta: dict?
entry: Transaction         accounts: set[str]
```

`position` combines posting units and cost. `balance` is running inventory for
posting account. `entry` is parent transaction. `accounts` contains every
account in parent transaction; `other_accounts` excludes current posting.

`SELECT *` uses journal columns only:

```text
date, flag, payee, narration, position
```

### `entries`

Every loaded Beancount directive, including non-transaction directives and
`query` directives.

```text
id: str                    type: str
filename: str              lineno: int
date: date                 year/month/day: int
flag: str?                 payee: str?               narration: str?
description: str?          tags: set[str]?            links: set[str]?
meta: dict                 accounts: set[str]
```

Transaction-only fields return `NULL` for other directive types.

### `transactions`

Transaction directives only. Columns mirror transaction fields:

```text
meta: dict                 date: date                flag: str
payee: str?                narration: str?            tags: set[str]
links: set[str]            accounts: set[str]
```

`postings` field is not exposed.

### `accounts`

Derived account open/close index. One row per known account.

```text
account: str               open: Open?                close: Close?
```

Useful fields: `open.date`, `open.account`, `open.currencies`, `open.booking`,
`close.date`, `close.account`.

### Directive tables

These tables filter `entries` by directive type. Metadata columns exist even
when omitted from `SELECT *`.

```text
prices:
  meta: dict, date: date, currency: str, amount: Amount

balances:
  meta: dict, date: date, flag: str, account: str,
  number: Decimal, tolerance: Decimal?, discrepancy: Amount?

commodities:
  meta: dict, date: date, name: str

notes:
  meta: dict, date: date, account: str, comment: str

events:
  meta: dict, date: date, type: str, description: str

documents:
  meta: dict, date: date, account: str, filename: list[str], tags: set[str]
```

Confirm directive-specific types with `.describe`; Beancount versions can
change namedtuple annotations.

## Structured values

Use dot attributes or metadata functions:

```sql
SELECT account, open.date, close.date FROM #accounts;
SELECT date, entry.meta['location'] WHERE entry IS NOT NULL;
SELECT date, any_meta('project') WHERE any_meta('project') IS NOT NULL;
```

Common structure fields:

```text
Amount:   number, currency
Position: units, cost
Cost:     number, currency, date, label, merge
Transaction: meta, date, flag, payee, narration, tags, links, accounts
Open:     meta, date, account, currencies, booking
Close:    meta, date, account
```

Some fields are nullable. Protect arithmetic and attribute access with
`IS NULL`/`IS NOT NULL` when needed.

## Live discovery

```sh
bean-query "$LEDGER" ".tables"
bean-query "$LEDGER" ".describe postings"
bean-query "$LEDGER" ".describe entries"
bean-query "$LEDGER" ".describe accounts"
bean-query "$LEDGER" ".help targets"
```
