# Research 4 — Format precedents & DRAFT timeline-format specification

*Autoresearch thread, 2026-08-22. Status: **DRAFT PROPOSAL — nothing locked, owner reviews.***
*Sections marked ⏳ await cross-checking against the wave-2 agent reports (critics / narratology / practitioner tools).*

---

## Part 1 — Prior art: does a machine-readable novel-timeline format exist?

**No.** Third independent confirmation of the gap (wave-1 agents found no story-bible incumbent; this thread found no timeline-format incumbent):

| Project | What it actually is | Why it doesn't cover us |
|---|---|---|
| [narrative-context-protocol](https://github.com/narrative-first/narrative-context-protocol) (81★, active, 3.0.0-rc.1) | Interchange for *authorial intent* — layered core (identifiers, provenance, attestations) + Dramatica Storyform profile | No character tracking across time, no location transitions, no story-time vs discourse-time. Different problem. **But its layered core/profile/extension architecture is worth copying.** |
| [project-89/narrative-canon](https://github.com/project-89/narrative-canon) (0★, MIT, active) | Agent-first story-*authoring* environment; world chronology of typed canon events + snapshot ledger | Authoring, not extraction. Character state tracking and witness/POV explicitly absent; richer temporal rules "roadmap work". **Its "canon ledger from snapshots at commit boundaries" validates the event-log approach.** |
| [narrative-state-engine](https://github.com/daviburg/narrative-state-engine) | AI-DM game-session state (timeline/event/entity JSON schemas) | Game sessions, not literary text; no dual clock, no evidence grounding. |
| [Microsoft Timeline Storyteller](https://github.com/microsoft/timelinestoryteller) | Timeline *visualization* environment | Presentation, not representation. |

## Part 2 — Design precedents worth stealing

**1. OpenTimelineIO — per-object schema versioning.** Every serialized object carries `"OTIO_SCHEMA": "Clip.5"` (name + version per *type*, not per file); the library upgrades old schemas on read and can downgrade on write ([versioning docs](https://opentimelineio.readthedocs.io/en/latest/tutorials/versioning-schemas.html)). This is how a format survives years of evolution without breaking old files. Steal verbatim.

**2. Event sourcing — the architectural match for "state over time".** State changes stored as an immutable event sequence; current state is a *fold* over events; state-at-any-past-point is a partial fold; **projections** are derived read-models, independently rebuildable from the same log ([Azure pattern doc](https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing)). Mapped to novels:

- the **event log** = what happens in the book (extracted once, heavily verified)
- "Where is Mina in chapter 18?", "What wounds does Jonathan carry at the end?", "Character sheet as of chapter N (spoiler-safe)", "All scenes at Castle Dracula" = **projections — computed by code, never extracted separately.**

This dissolves the consistency problem that kills hand-maintained wikis: facts recorded once at the event level cannot disagree between the character page and the location page, because both pages are derived.

**3. FHIR — minimal governed core + extensions.** The spec stays implementable because everything beyond agreed-common requirements is an extension with governance rules ([FHIR extensibility](https://hl7.org/fhir/extensibility.html)). Our core stays small (entities, events, anchors, time); production-specific needs (visual prompt blocks, voice casting) are extension namespaces, not core fields.

---

## Part 3 — DRAFT specification

### The brick of the format

> **A narrative event: (who, did what, to whom, where, at story-time T, told at text-position P, witnessed by W, evidenced by span S).**
>
> Everything else — character sheets, timelines, location indexes, continuity states, spoiler-gated views — is a projection over the event log.

### Dual clock (the non-negotiable core idea)

Every event is anchored twice:

- **`anchor` (discourse position)** — where the text tells it: chapter / scene / paragraph range / char offsets. Always known **precisely** — extraction can never fail to know where it is reading.
- **`story_time`** — when it happens in the world. Often **fuzzy** ("three days later", "meanwhile"). Absolute when the text gives it (Dracula's diary dates!), otherwise expressed as **relations to other events** (Allen-style interval relations: `before`, `after`, `during`, `meets`, `overlaps`, `simultaneous_with`) plus optional `story_day` numbering (film-production "D1/N3" convention). ⏳ validate relation subset against agent-B narratology report.

Flashback = event whose story_time sorts earlier than events at smaller anchors. Fabula vs syuzhet drops out of the data instead of needing special cases: sort by `anchor` → the book as told; sort by `story_time` → the world's chronology.

### Core objects (draft)

```yaml
# file header
format: {name: TBD, version: 0.1}          # per-object schema tags like OTIO
codex_id: "20260822143015"                  # THE id — from the codex table
source: {type: gutenberg, ref: pg345}

entities:                                   # the registry (analysis pass 0/2)
  - id: ch_harker
    kind: character                         # character | location | item | faction | creature
    canonical_name: "Jonathan Harker"
    aliases: ["Harker", "my friend Jonathan"]
  - id: loc_castle
    kind: location
    canonical_name: "Castle Dracula"
    parent: loc_transylvania

events:
  - id: ev_0007
    schema: Event.1                         # OTIO-style per-object version
    type: movement                          # action | dialogue | movement | state_change
                                            # | perception | introduction | mention
    summary: "Harker arrives at Castle Dracula at night"
    participants:
      - {entity: ch_harker,  role: agent}
      - {entity: ch_dracula, role: agent}   # as the coachman — see note
    location: loc_castle
    anchor: {chapter: 2, scene: 1, para: [1, 4]}
    story_time:
      date: "1893-05-05"                    # from the journal heading
      time_of_day: night
      story_day: 3
      precision: date                       # date | day_part | relative_only
    relations:
      - {type: after, target: ev_0006}
    evidence: [{chapter: 2, quote: "the castle...against the moonlit sky"}]
    focalization: {pov: ch_harker, narration: journal_first_person}
    knowledge_scope: pov_only               # Harker doesn't KNOW the coachman is Dracula
    confidence: 0.95
    extracted_vs_inferred: extracted

  - id: ev_0021
    type: state_change
    subtype: injury                         # injury | possession_gain | possession_loss
                                            # | knowledge_gain | wardrobe | location_move
                                            # | relationship_change | death | transformation
    summary: "Harker cuts himself shaving"
    participants: [{entity: ch_harker, role: patient}]
    state: {attribute: injury, value: "small shaving cut, chin", until: null}
    anchor: {chapter: 2, scene: 3}
    story_time: {date: "1893-05-08", precision: date}
    evidence: [{chapter: 2, quote: "I had cut myself slightly in shaving"}]
```

Notes captured by the draft:
- **`knowledge_scope` / focalization** — what the POV character knows vs what is true (the coachman IS Dracula; Harker doesn't know). Spoiler-safe projections need this. ⏳ refine with agent B.
- **`state.until`** — states persist until explicitly ended; the projection engine carries them forward (script-supervisor continuity logic). ⏳ refine with agent C.
- **`extracted_vs_inferred`** on everything, evidence spans required — carried over from wave-1 (langextract grounding, chargraph's hallucinated-edge failure).

### Standard projections (computed, never stored as truth)

| Projection | Answers |
|---|---|
| `character_timeline(id)` | swimlane: every appearance/action/state change in either clock order |
| `location_index(id)` | AWOIAF's "chapters that take place in Winterfell", for free |
| `state_at(entity, anchor)` | continuity sheet: wounds, possessions, knowledge, wardrobe at chapter N |
| `bible_as_of(anchor)` | spoiler-gated story bible for shorts about early chapters |
| `copresence_graph(window)` | who shares scenes with whom → relationship evidence |
| `chronology()` vs `telling_order()` | fabula vs syuzhet views |

### Name candidates (owner picks — not chosen)

| Candidate | For | Against |
|---|---|---|
| **fabula** (`.fabula.yaml`) | The exact narratology term for "the events in world order" — the format IS a fabula record | slightly academic |
| **loom** | weaving threads/timelines; pairs with The Keeper's Lantern vibe | generic word, some tool collisions |
| **NEL** — Narrative Event Log | says exactly what it is | dry acronym |
| **tapestry** | same weaving metaphor, warmer | likely name collisions |
| **canon** | fan-culture native | collides with narrative-canon repo, overloaded term |

### Open design questions (for the review session)

1. **Granularity floor**: is every dialogue line an event, or only plot-significant ones? (Cost vs completeness — proposal: significance tiers, extract tier 1-2 always, tier 3 on demand.)
2. **Scene as first-class object** vs scenes existing only as anchor fields on events?
3. **Relationship evolution**: separate `relationship_change` events (proposed) vs a parallel relationships table?
4. YAML or JSON as the canonical serialization? (Proposal: JSON canonical + YAML accepted for human editing.)
5. How does the event log RELATE to the story-bible schema from research 3 — bible sections as projections of the log (elegant, one source of truth) vs bible as a sibling artifact (simpler passes)? **This is the biggest architectural fork.**
6. Uncertainty representation: confidence float vs discrete tiers?
7. ⏳ Whatever the three wave-2 agents surface that this draft is missing.

### Publishable-artifact note

Third independent confirmation: no incumbent exists for a grounded, dual-clock, machine-readable narrative timeline format. A published spec + extractor + validator (the format, a `codex-analysis` reference implementation, a Dracula sample dataset) is a standalone open-source artifact with no strong competitor. Standing-goal relevant.
