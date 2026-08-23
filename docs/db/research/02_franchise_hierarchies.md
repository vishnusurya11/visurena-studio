# Research — How studios & franchises model hierarchy + shared assets

*Subagent report, 2026-08-22. Feeds LIBRARY_STRUCTURE.md. Includes live Coppermind API queries.*

## The one shape every system converges on

> **A strict containment tree for WORK + home-scoped SHARED ENTITIES + a metadata-bearing
> many-to-many "appearance/casting" join.** ShotGrid, AYON, Kitsu, USD, TV bibles, Coppermind,
> and game franchises are all instances of this shape.

## 1. VFX pipelines — the two-branch model

- **AYON**: two top-level branches — `shots/` (Episode>Sequence>Shot, the work breakdown) and
  `assets/` (characters/props/environments). Shots never *contain* assets; they **load
  published asset Products at pinned immutable Versions** (v001…).
- **ShotGrid**: Asset↔Shot is a junction entity (`AssetShotConnection`) and **the junction
  carries relationship-scoped metadata** (e.g. "in camera" per shot). → "Hoid *as Wit* in this
  book": the alias lives on the LINK, not on either endpoint.
- **Kitsu**: "casting" — assets cast into shots, into episodes (multi-level!), even into other
  assets. Casting at multiple hierarchy levels = exactly "artifact belongs to series vs book."
- **USD**: shot files are thin and *compose* self-contained asset packages by reference;
  sequence-level files hold opinions inherited by all shots. **Reference-don't-copy +
  version-pinning is the industry invariant.**
- **Prism**: identical sub-structure inside every asset and every shot folder — uniformity
  lesson for folder layout.

## 2. TV production

Show bible = series-scoped, **accretes after every episode** (continuity trackers, character
bibles "consistent from episode to episode and season to season"). Episode docs never restate
the world. → series-level artifacts are aggregates that grow as book-level work completes.

## 3. Coppermind (queried live via MediaWiki API) — the Cosmere answers from the source

- **ONE Hoid page** (pageid 13), scoped to the whole cosmere; History = one chronological arc
  crossing every series; per-world abilities as sections. Never a per-series copy.
- **Scoping = category tags, a DAG with multiple parents, not a tree.** Nightblood
  (Warbreaker→Stormlight crossover) carries BOTH `Warbreaker` AND `Stormlight_Archive` +
  `Nalthians` (origin) + `General_Cosmere`. One page, multiple memberships.
- **Aliases are redirects**: `Zahel` is literally `#REDIRECT Vasher`. One entity, many names.
- **`General Cosmere`** = their explicit universe-level not-owned-by-any-series bucket.
- **Retcons (Secret History)**: canonical pages updated **in place**, gated by a spoiler
  window, and stale pages tracked with debt categories (`Update_for_Rhythm_of_War`). The
  timeline is never forked. → new book lands ⇒ append to entity sheets, bump version, tag
  downstream artifacts `needs_update_for(book)`.

## 4. Game franchises

Shared engine/asset base reused across titles (AC Black Flag ~80% reuse of AC3); DLC ships as
separate packages that *depend on* the base, never re-bundle it. New content references old.

## 5. Data modeling

- **Promote a text column to a table the moment anything must ATTACH to it** — an artifact
  cannot foreign-key a string. (Normalization: repeated/related attributes become entities.)
- Shallow 4-level tree → **adjacency list** (`parent_id` + recursive CTE) is enough; skip
  closure tables until queries prove slow.
- **Crossovers never bend the tree** — the containment tree stays strict (every book exactly
  one series); crossings live in junction tables with metadata (alias, role, prominence).

## 6. Cosmere hard cases — resolved

| Case | Solution (from the systems studied) |
|---|---|
| Hoid in every series | One canonical sheet at universe scope |
| Hoid = "Wit" here, "Topaz" there | Alias on the appearance link |
| Nightblood / Vasher-Zahel crossovers | Home = origin scope; *additionally cast into* other series via links |
| Worldhoppers as a class | Universe-level tag on entities, not a folder |
| Secret History retcons | Update canonical in place + spoiler window + `needs_update_for` debt tags |
| Book analysis mentioning Hoid | Book stores reference + local observations; canonical sheet aggregates per-book sections |

## 7. Recommended model (adopted into LIBRARY_STRUCTURE.md)

(a) Work tree: universe > world > series > book — strict, one parent each.
(b) Shared entities homed at the **narrowest scope that fully contains them** (Kaladin →
series; Roshar geography → world; Hoid, Investiture → universe).
(c) `appearance(entity, scope, alias_used, role, notes)` junction carrying per-appearance data.
(d) One `scope_node`-style table (adjacency list, kind ∈ universe/world/series) the moment
artifacts must attach above book level; entities/aliases/appearances tables alongside.
(e) Casting pulls canonical sheets at **pinned versions**; on a new book: append to sheets,
bump version, tag downstream `needs_update_for`.

Key sources: AYON entity docs · ShotGrid AssetShotConnection thread + hierarchy article ·
Kitsu breakdown/TV docs · Prism folder docs · OpenUSD intro/tutorials · Scriptation/ScreenCraft
show-bible guides · Coppermind live API (Hoid/Kaladin/Nightblood/Vasher/category graph) +
spoiler policy · Steamworks/GDK DLC docs · normalization + hierarchy-pattern references.
