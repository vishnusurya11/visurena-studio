# Research 10 — Timeline solving: scenes → "who is where, when"

*Subagent report, 2026-08-23. Implemented in `scripts/analysis/step_04_timeline.py`.*

## The systems worth copying

**TLEX** (TimeLine EXtraction, arXiv 2406.05265; `pyTLEX`/`jTLEX`) — closest existing
system. Its decomposition, adopted wholesale:
1. **Partition** — ignore subordinating links (modal/embedded); DFS → components; each
   is a timeline. Embedded narration attaches as a **subordinated branch** (trunk +
   branches). *Our Part II Utah flashback is exactly this.*
2. **Pointize** — each interval → two points (`t⁻ < t⁺`); interval relations → point
   constraints.
3. **Timeline** — greedy **Kahn topological sort** → minimum normal-form timeline.
4. **Consistency** — merge `=`-connected points, detect cycles → **MLIC** (the exact
   relations involved in each inconsistency). 123 of 385 TimeML texts had them; expect
   them in LLM extraction too.
5. **Indeterminacy** — reachability check per ordered pair: unreachable = the order was
   *not forced* by the text → a confidence signal, not an error.

**STP** (Dechter/Meiri/Pearl) adds the METRIC layer TLEX lacks: constraints
`a ≤ t_j − t_i ≤ b`, distance graph + **Floyd-Warshall**; consistent iff no negative
cycle, and shortest paths yield **[earliest, latest] windows per event for free**.

**Allen algebra**: skip full path-consistency — it's incomplete for the full algebra
and narrative extraction rarely produces the exotic disjunctions that need it. Convert
to point algebra + STP (TLEX made the same call).

## Story-day chaining (how humans actually do it)

**ASOIAF fan chronology** = an informal STP by hand: a few **anchor events** with fixed
dates → **offset chaining** from verbatim phrases ("a fortnight later") → **travel
feasibility** fills silent gaps → explicit **±N slack** → **cross-POV shared events**
fuse per-POV chains.

**Film continuity**: a new **story day** begins at a NIGHT→DAY transition; CONTINUOUS
inherits; flashbacks get their **own day-numbering series**.

**Chapter-boundary cascade** (first match wins) — implemented verbatim:
1. explicit offset evidence → hard edge
2. NIGHT→DAY across the boundary → +1 day
3. same-day continuity cues → same day
4. no evidence → soft `[0, K]` gap, K from feasibility; report as indeterminate.

## Between observed scenes

Games (S.T.A.L.K.E.R. A-Life, Radiant AI) keep off-screen entities in a **coarser**
representation, never a simulated one. Time geography: between two observations the
feasible region is Hägerstrand's **space-time prism** — the *path* is observed, the
*prism* is possible. Literary mapping never fabricates positions between attested
mentions.

**Three interpolation states adopted**: `stationary-presumed` (same location either
side) · `in-transit` (location changed — this is what animates) · `unknown` (long gap
or evidence of absence; render faded, never a fabricated path).

## Flashback / frame

TLEX subordinated branch + film's separate day counters + **Story Curves** (IEEE TVCG
2018: telling order on X, story order on Y — a flashback is a dip). Verdict adopted:
**the navigable axis is telling order**; each scene maps to a position on one of two
clocks; overview uses **separate tracks**, never one interleaved chronological axis
(scales differ by orders of magnitude: days vs 13 years).

## Contradiction detection

1. **Bilocation** — per character, overlapping intervals at different locations (sweep).
2. **Travel feasibility = the alibi query** (moving-object databases): do the space-time
   prisms intersect? `distance / speed > elapsed` → contradiction. Run against **STP
   windows**, not point estimates. 1881 speeds: walking ~3 mph, **hansom cab ~5-10 mph**;
   Baker St → Brixton ≈ 5-6 miles ≈ 40-70 min.
3. **Negative cycles / MLIC** — the evidence itself unsatisfiable.
4. **FlawedFictions** (arXiv 2504.11900) finds LLMs *unreliable* at free-form plot-hole
   detection → do detection deterministically, use the LLM only for extraction/repair.
   **ConStory** discipline: every contradiction cites verbatim evidence on both sides.

## Publishability note (from the agent)

No open-source tool combines TLEX-style extraction + metric story-day solving +
character worldlines. A standalone package benchmarked on public-domain novels (with
the ASOIAF fan chronology as a human baseline) would be a credible artifact.

Key sources: TLEX arXiv:2406.05265 · pyTLEX EACL'24 · Planken STP/TCSP survey ·
van Beek IJCAI-89 · A Timeline of Ice and Fire + source spreadsheet · StudioBinder
story days · Miller space-time prisms · alibi query arXiv:0712.1996 · A-Life /
Radiant AI · Story Curves (Harvard VCG) · FlawedFictions · ConStory · Britannica
hansom cab.
