# Library Structure & Hierarchy — Proposed Design

**Status: PROPOSAL, 2026-08-22 — owner reviews.** Evidence:
[research/01_library_structures.md](research/01_library_structures.md) (Calibre, Plex/*arr,
Komga, DAM, Windows specifics) and
[research/02_franchise_hierarchies.md](research/02_franchise_hierarchies.md) (VFX pipelines,
TV bibles, Coppermind live API, game franchises).

**Owner constraint (locked): the codex table's grain is the BOOK.** One row per book, always.
Universe / world / series describe a book; they never become codex rows.

## The two findings that decide everything

1. **Nobody mirrors a deep taxonomy on disk.** Calibre, Plex's ecosystem, Komga, DAM practice
   — all converge on: flat id-keyed storage as the only truth; hierarchy in the DB; browse
   trees only as *generated, disposable* views. Because the taxonomy is **mutable** (books get
   reassigned, standalones join series) and, for Cosmere, **not even a tree** — Nightblood
   belongs to Warbreaker AND Stormlight; Hoid belongs to everything. Paths make taxonomy
   immutable-by-accident; DB rows keep it one UPDATE away.
2. **Every studio system is the same shape**: a strict work tree (universe>world>series>book) +
   shared entities homed at the *narrowest scope that contains them* + a many-to-many
   **appearance/casting** join that carries per-appearance metadata (Hoid *as Wit*). Coppermind
   itself — queried live — runs exactly this: ONE Hoid page at universe scope, category tags
   as the DAG, `Zahel → #REDIRECT Vasher` for aliases.

## Folders (the decision)

**Flat, id-keyed, two kinds of folders. No hierarchy in paths, ever.**

```
library/
  20260822113400_sherlock/          # BOOK folders (codex rows) — exactly as today
    source/  analysis/  audiobook/  video/  publish/     # fixed subdirs, uniform for globs
  _scopes/                          # SCOPE folders — series/world/universe-level artifacts
    sherlock-holmes/                #   series: Holmes & Watson canonical sheets, series bible
    cosmere/                        #   universe: Hoid sheet, investiture rules  (future)
    roshar/                         #   world: geography, cultures              (future)
views/                              # OPTIONAL generated browse tree (Windows junctions,
                                    #   no admin needed) — regenerable, excluded from backups
```

Rules (each one bought with a documented failure elsewhere):
- **Book folder = `<codex_id>_<slug>`**; the id is identity (Calibre's `(id)`), the slug is
  cosmetic and may go stale after a title fix without consequence. Slug: lowercase, ascii,
  `-`; **never encode series/index/universe in it** (mutable data stays out of keys — S3 rule).
- **Never hand-move anything under `library/`** (Calibre's rule; Plex's "renamed folder, lost
  watch history" thread is the cautionary tale).
- Every stored reference = codex_id + **relative** path. Nothing ever references `views/`.
- Scope folders use stable human slugs (few of them, human-curated, effectively immutable).
- Windows bonus: flat paths burn ~35 chars vs ~70+ for a mirrored tree — MAX_PATH headroom
  for long render filenames.
- `views/by-universe/Cosmere/Roshar/The Stormlight Archive/01 - The Way of Kings` → junction
  into the flat store, regenerated wholesale from the DB; a crossover book can appear under
  TWO worlds (impossible in a real tree, trivial with junctions). Build only when wanted.

## Database (phased — build nothing before it's needed)

**Phase now (Sherlock, single books):** exactly what exists — `codex` with
`universe/world/series/series_index` TEXT columns. Sufficient until something must *attach*
to a series.

**Phase 2 — trigger: the first series-level artifact** (a Holmes character sheet spanning
books, a series bible, a Cosmere rules doc). A file cannot foreign-key a text column, so at
that moment:

```sql
atlas   (id TEXT PK,          -- stable slug: 'cosmere', 'roshar', 'sherlock-holmes'
         parent_id TEXT REFERENCES atlas(id),
         kind TEXT CHECK (kind IN ('universe','world','series')),
         name TEXT NOT NULL)
-- codex UNCHANGED in grain: gains atlas_id FK (narrowest node, usually the series);
-- the text columns become derivable and can be kept or dropped.
```

*(`atlas` = working name for the hierarchy table — the map of universes/worlds/series.
Owner may rename.)* Adjacency list only — 4 shallow levels need nothing fancier.

**Phase 3 — trigger: cross-book entities** (the analysis stage's character registry going
multi-book):

```sql
entity     (id, home_atlas_id | home_codex_id,   -- narrowest containing scope
            kind,                                 -- character/location/item/faction/rule
            name)
entity_alias (entity_id, name)                    -- 'Zahel' → Vasher, as data
appearance (entity_id, codex_id,                  -- the casting junction
            alias_used, role, notes)              -- per-appearance metadata ON the link
```

**Continuity flow when a new book of a series completes** (Coppermind's, verbatim): append the
book's events to each cast entity's canonical sheet (its history gains a section) → bump the
sheet's version → tag downstream artifacts `needs_update_for(<codex_id>)` instead of silently
editing. Productions cast entity sheets at **pinned versions** (USD/AYON), so regenerating an
old book's video after a retcon still uses the sheet-version that matched it.

## What this means for Sherlock today

Nothing changes: `library/20260822113400_sherlock/` is already correct. When *The Sign of the
Four* arrives and we want one Holmes sheet across both books, that's the Phase-2/3 trigger:
`library/_scopes/sherlock-holmes/` + the `atlas` and `entity` tables.

## Open questions for review

1. Name the hierarchy table: `atlas` (proposed) — or your pick.
2. Scope folders at `library/_scopes/<slug>/` (proposed) vs a separate top-level folder.
3. `views/` junction browse-tree: build at command-center time, earlier, or never?
4. Phase-2 migration detail: keep the codex text columns alongside `atlas_id` (denormalized,
   convenient) or drop them (normalized)?
5. Add `library/` to `.gitignore` (still pending from earlier).
