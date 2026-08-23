# Database Schema

**File:** `db/visurena_studio.db` (SQLite, in-repo, gitignored via `*.db`)

Rationale for every choice below lives in [../DECISIONS.md](../DECISIONS.md).

---

## `codex` — the catalog of source works

One row per book. Content productions derive from it; nothing derives *into* it.

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | `TEXT` PK | no | `YYYYMMDDHHMMSS` — 14 chars, **UTC**, second precision |
| `name` | `TEXT` | no | the book's name |
| `universe` | `TEXT` | **yes** | e.g. Cosmere |
| `world` | `TEXT` | **yes** | e.g. Roshar |
| `series` | `TEXT` | **yes** | e.g. Stormlight Archive |
| `series_index` | `INTEGER` | **yes** | position in the series — "book 3 of" |
| `source_type` | `TEXT` | **yes** | `gutenberg` \| `epub` \| `local` — approved 2026-08-22 |
| `source_ref` | `TEXT` | **yes** | `pg160`, or a repo-relative path — approved 2026-08-22 |
| `updated_at` | `TEXT` | no | ISO-8601 UTC, e.g. `2026-08-22T14:30:15Z` |

**The `id` is THE id across the entire system** — every stage table, production folder,
and artifact references this value. It is never regenerated or reformatted downstream.

### There is no `created_at`

The `id` **is** the creation timestamp, to the second. Storing it twice invites
drift. Parse it from the id.

### `id` vs `source_ref` — different things

| | What it is | Example |
|---|---|---|
| `id` | **our** row identity | `20260822143015` |
| `source_ref` | **where the actual text lives**, so analysis can fetch it | `pg160` |

A Gutenberg id is Project Gutenberg's own catalogue number (Dracula is 345). The existing
parser already uses them — `uv run python -m studio_parser pg160`. Without a source
pointer a row is a name with nowhere to read the book from, so analysis cannot run.

### Sorting and filtering

Fixed-width zero-padded text means lexicographic order **is** chronological order.

```sql
-- newest first, straight off the primary key index
SELECT * FROM codex ORDER BY id DESC;

-- everything added in August 2026 — range scan, uses the index
SELECT * FROM codex
 WHERE id >= '20260801000000'
   AND id <  '20260901000000';
```

Do **not** write `WHERE id LIKE '202608%'`. SQLite only optimises `LIKE` into an index
scan under specific collation settings; otherwise it silently degrades to a full scan.

Sorting or filtering on `name`, `series`, `universe` or `world` is an ordinary index and
is unaffected by `id` being text.

### Uniqueness — NOTE

At second precision, two inserts in the same second **collide**. Owner decision
(2026-08-22): entry is manual for now, and bulk inserts must wait ≥1 second between
rows (or retry with `id + 1 second` on conflict). `id` is the `PRIMARY KEY`, so a
collision is rejected loudly rather than silently overwriting — but any future batch
importer MUST implement the delay or the retry before it ships.

---

## Stage tracking — DEFERRED

Owner will decide at build time. The two candidates:

**Option A — columns on `codex`**

`analysis_status`, `analysis_started_at`, `analysis_updated_at` directly on the row.
Each new content type adds 3 columns and a migration. Easy to eyeball in a DB browser.

**Option B — a `codex_stages` table**

```
codex_stages(codex_id, stage, status, started_at, updated_at)
PRIMARY KEY (codex_id, stage)
```

Adding `audiobook`, `shorts` or `video` is an INSERT, never a migration. Same shape as
the Step ledger in [../ARCHITECTURE.md](../ARCHITECTURE.md), so there is one mechanism
instead of two that drift.

At one stage the two are identical effort; at five stages A is 15 columns and 5
migrations.

### Status values, whichever option wins

```
pending -> running -> completed
                   -> failed
```

Enforced with a `CHECK` constraint so a typo is rejected at write time rather than
quietly inventing a fifth state.

- `pending` is required — a new row has no analysis yet, and *"what needs analysing?"* is
  the most common query this table will serve.
- `failed` is required — without it a crashed run is indistinguishable from a running
  one, so the scheduler either retries forever or never retries.
- The originally sketched `started` and `in progress` are the same state; they collapse
  into `running`.

---

## Open items

| Item | Blocking |
|---|---|
| Choose stage tracking option A or B | first stage implementation |
| Resolve `db/visurena_studio.db` vs `D:\Projects\GlobalDatabases\visurena_studio.db` | P0 |
