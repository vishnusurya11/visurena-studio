# Research — How mature library systems structure storage (folders vs DB)

*Subagent report, 2026-08-22. Feeds LIBRARY_STRUCTURE.md.*

## The pattern across every mature system

**Nobody mirrors a deep taxonomy on disk.** The filesystem never carries more than ~two
semantic levels; everything above/across series is metadata:

| System | Disk carries | Hierarchy lives in |
|---|---|---|
| **Calibre** | `Author/Title (id)/` — the **(id) is the real identity**, names are cosmetic | `metadata.db` (SQLite). Hand-editing folders explicitly forbidden. "Save to disk" exports arbitrary folder hierarchies as **derived, disposable projections** |
| **Audiobookshelf** | `Author/Series/Book` + a naming microformat (dashes/braces/brackets) | The folders ARE its metadata input — it has no authoritative DB upstream. The microformat is the cost of that |
| **Plex/Jellyfin** | strict `Show/Season NN/...` conventions | Conventions compensate for no DB input. **Collections (the "universe" analog) are not folders at all.** Documented failure: rename a folder → matching breaks, watch history lost. The *arr tools fixed this with flat tool-owned stores + hardlinked convention trees as views |
| **Komga/Kavita** | 1 folder per series, one-shots special-cased | Collections ("Marvel Universe") and cross-series read lists ("Civil War order" = our Cosmere reading order) come from **metadata**, never folders |

**Calibre's 20-year position**: a single static hierarchy serves exactly one query; metadata
serves all of them. Hierarchy in metadata, stable-id paths on disk, trees only as generated
exports.

## DAM / data-engineering side

- Flat + tags: an asset can "exist in multiple places without duplication"; a folder tree
  forces single placement. Folder-keeping DAM practice caps at 2-4 levels.
- **S3 rule**: keys immutable; mutable attributes (series membership IS mutable) never go in
  the key. Rename = full copy.
- **Windows MAX_PATH (260)**: a mirrored tree burns ~70+ chars on taxonomy before any
  artifact name; flat `library/<id>_<slug>/` burns ~35. Deep nesting + long render filenames
  is the documented failure case.
- **Junctions** (`mklink /J`): directory links needing **no admin/Developer Mode** (unlike
  symlinks on Windows) — the right mechanism for generated browse-trees. Caveat: recursive
  tools follow them, so the view root must be excluded from backups/deletes.

## Edge cases that break hierarchy-in-paths (Cosmere has all of them)

1. Series reassignment: 1 SQL update flat vs mass dir moves + path link rot mirrored.
2. Standalones: fake `_standalone/` level, and a *move* when Sanderson retcons them into a series.
3. **Crossovers**: Arcanum Unbounded spans many worlds; Hoid crosses everything; Secret
   History runs parallel to another book. **The taxonomy is a DAG, not a tree** — a real
   tree forces one parent; junctions can place one book under two worlds.
4. Era splits/rebrandings (Mistborn era 1 vs 2) = mass moves under mirroring.
5. Slug churn: title fixes are safe only if the id, not the name, is identity.
6. Windows: dir moves non-atomic, open handles block renames — a reorg can fail halfway.

## Recommendation (adopted into LIBRARY_STRUCTURE.md)

**Flat store (only source of truth) + generated junction browse-view.**

- Store: `library/<id>_<slug>/` — id is identity, slug cosmetic and allowed to go stale;
  fixed artifact subdirs (`source/ analysis/ audio/ video/ publish/`) so globs work.
  Slug rules: lowercase, ASCII, `-`, **never encode series/sequence/universe in the slug**.
  Tool-owned; never hand-edited (Calibre's rule).
- View: `views/by-universe/Cosmere/Roshar/The Stormlight Archive/01 - The Way of Kings` →
  junction to the flat folder. Regenerated wholesale from the DB on any change; idempotent;
  data never moves. Standalones get `_Standalone/`; crossover books appear under multiple
  worlds. Series index `NN - Title` (zero-padded; decimals like `3.5` for novellas).
  Excluded from backups.
- Series/world/universe-level artifacts: **anything that can own artifacts is an
  id-addressed entity, not a path prefix** — group entities get their own flat folders too.
- **The one invariant**: every stored reference uses id + relative path in the flat store,
  NEVER a `views/` path. That's what makes taxonomy edits free forever.

Key sources: Calibre FAQ · Audiobookshelf directory docs · Jellyfin/Plex naming docs + the
"renamed folder, lost history" failure thread · Komga/Kavita wikis · Stacks & AEM DAM guides ·
S3 key best practices · MS MAX_PATH + junctions docs.
