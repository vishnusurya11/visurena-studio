# Research 6 — How practitioners actually represent narrative timelines

*Wave-2 subagent report, 2026-08-22.*

## 1. Aeon Timeline — the richest existing data model for fiction time

The de facto professional tool for exactly our problem. Core model:

- **Event** = title, start date, duration, end date (mathematically linked), notes, tags, template-defined properties.
- **Entity** = person, location, object, story arc, organisation… Entities have birth/start and death/end dates *or link to events as their birth/death*, from which the tool **auto-computes character age at every event** (a feature users cite constantly).
- **Relationship** = many-to-many event↔entity edge, and every relationship carries a **Role**: a person is related to an event as **Participant** or **Observer/Witness**; a location's role is "occurred at." Roles are template-defined per entity type. The Relationship View is a matrix (events × entities) writers use to audit "who was on stage in which scene."
- **Groups/swimlanes** by entity relationship; one event can appear in multiple lanes.

**Dates & uncertainty** (goldmine):
- Mixed precision on one timeline (one event to the second, another "2021 only"); precision is an explicit property.
- **Uncertain dates = FOUR dates**: earliest start, latest start, earliest end, latest end — rendered `~` with a fuzzy gradient. A shipped, practitioner-tested uncertainty model.
- **Ongoing** items: no end, "X – Present."
- **Relative date styles**: "Day 0/1/2…" as a first-class date system with an optional zero-date mapping — native **story-day numbering**.

**Custom fantasy calendars**: renamed months/weekdays, custom eras, leap rules, custom hours/day. Pain point: calendars lock once events exist — our format can fix this (calendar as versioned data).

**Dependencies/constraints**: Event B = end of Event A + offset ("she arrives 10 days after the letter"). Multiple dependencies resolve to the latest; violations are flagged. **Relative ordering as data — exactly what a novel gives us.**

**Narrative vs story time**: Aeon 3 keeps an independent **narrative tree** (acts/chapters/folders holding events in *told* order), decoupled from dates. One event object, two orderings — the industry's fabula/syuzhet answer. Scrivener sync anchors narrative events to actual manuscript scenes (dual anchoring in the wild).

**File format: closed.** v3 `.aeon` = JSON+binary, denormalized, "readable by third parties, hardly written," no public spec. **The market leader has no open interchange format — a genuinely open narrative-timeline schema is a gap.**

## 2. Plottr, Campfire, World Anvil

- **Plottr**: grid of chapters/beats × **plotlines** × scene cards. **No dates at all** in the core model — pure narrative order with plotline swimlanes. `.pltr` is JSON. Lesson: the **plotline/thread dimension** is so essential a major tool made it the primary axis instead of time.
- **Campfire**: multiple parallel timelines viewable simultaneously (per-POV threads, book-vs-book); rows as acts or per-character lanes; separate **Calendar Module** the Timeline consumes.
- **World Anvil**: old Timelines "not great at showing concurrent events" — which is *why* they built **Chronicles**: four parallel lanes explicitly for "what's going on at the same time elsewhere," world-level eras, zoom to hours, and **events pinned to map coordinates**. Blunt lesson: simultaneity ("meanwhile") was the users' top demand; space+time joint anchoring second.

## 3. Fan chronology practice

- **Tolkien, Tale of Years**: annalistic — Age → year → terse entries; "c." for circa; granularity **densifies where the story densifies** (The Great Years switch from year to month/day resolution); the date line is the join key across parallel threads; Appendix D reconciles multiple in-world calendars. Tolkien privately kept a **character × day position matrix** while drafting.
- **ASOIAF community chronology** (PrivateMajor's day-by-day spreadsheet): anchor a few absolutely-dated events, then chain **relative internal evidence** ("a fortnight later," travel durations, moons) into day offsets; every chapter dated **with cited textual evidence** and explicit slack ("may be off by a week or two"). The visual descendant plots POV characters as continuous **space-time worldlines** — the community independently reinvented per-entity swimlanes.
- **Wiki conventions** (Wookieepedia BBY/ABY, Memory Alpha): epoch-relative dating from a zero-point event; explicit **evidence hierarchy** (official statements over inferred placement); "place by narrative order and footnote the inference"; separate release-order vs in-universe-order pages (the wiki world's fabula/syuzhet).

## 4. Film/TV production — professional character-state-over-time

- **Script supervisor continuity breakdown**, per scene: scene no., INT/EXT + location, **story day/night ("D1", "N3")**, time of day, one-line action, characters present, props, wardrobe/hair/makeup notes, matching notes. Continuity notes record **entity-state deltas at scene granularity** ("sweater now blue") — character state over time, done professionally for a century.
- **Breakdown sheet** = per-scene entity manifest (cast, props, wardrobe, stunts). **Stripboard** = same scenes resequenced into shooting order — proof one scene list must support multiple orderings. **Day out of Days (DOOD)** = actor × day matrix with status codes, *generated from event participation* — the derivability test for our format: can it compute a DOOD?

## 5. Interactive fiction / games

- **Ink/Twine**: story state as variables, visit counts, typed LIST state machines gating content.
- **Quality-based narrative / storylets** (Fallen London): content units carry **declarative preconditions over numeric qualities + effects that mutate them** — narrative as (state precondition → event → state delta). The cleanest formalization of state-change tracking in the field.
- **Bethesda quest stages**: sparse ordinal indices (10, 20, 30…) for insertable ordered milestones per storyline.

## 6. Data / visualization / editorial formats

- **TimelineJS JSON** (most-copied timeline JSON): `{title, events[], eras[], scale}`; **structured partial dates** `{year, month?, day?…}` + **`display_date` free-text override** (what's shown ≠ what's sorted); `group` = swimlanes; `era` = axis spans.
- **OpenTimelineIO**: Timeline → Stack → Tracks → Clips/Gaps/Transitions; every clip has a **source_range into its media reference** — the exact analogue of an event pointing at a chapter/paragraph span; Markers with ranges; **open schema'd `metadata` dict on every object**; versioned schema names; deliberately human-readable JSON. The strongest engineering template.
- **EDL (CMX3600)**: one event per line with **source-in/out AND record-in/out** — dual anchoring formalized in 1970s broadcast engineering.
- **WebVTT**: cues = (start→end, payload) + metadata tracks — a "narrative VTT" (cues addressed to text offsets) is a natural serialization target.
- **MusicXML**: time = measures + per-score `divisions`; `<backup>`/`<forward>` express **simultaneous voices within one measure**. Translation: chapter = measure, paragraph offset = division, character threads = voices.

## 7. Feature checklist for the new format (each traced to the practice that proves it)

| # | Feature | Proven by |
|---|---|---|
| 1 | Events with start/duration/end, **mixed precision** | Aeon; TimelineJS partial dates |
| 2 | **Custom calendars as data**, editable after events exist | Aeon (incl. its lock-in pain point); Campfire; World Anvil; Tolkien App. D |
| 3 | **Story-day numbering as first-class date style** with optional zero-date | Aeon relative styles; script-supervisor D1/N3; BBY/ABY |
| 4 | **Uncertainty = ranges (4-date model) + confidence + cited evidence + display-text override** | Aeon fuzzy dates; TimelineJS display_date; ASOIAF evidence-per-chapter; Memory Alpha footnote policy |
| 5 | **Relative-order constraints** ("3 days after X"), resolvable or flagged | Aeon dependencies; ASOIAF offset chains |
| 6 | **Parallel threads/swimlanes, simultaneity first-class** | World Anvil Chronicles (built BECAUSE of "meanwhile"); Plottr plotlines; Tale of Years date-joins |
| 7 | **Typed entity-event roles — minimally participant vs witness/observer + location-of** | Aeon roles; breakdown sheets |
| 8 | **Entity lifespans + derived ages** (birth/death as dates or event links) | Aeon |
| 9 | **State-change deltas per event** (wardrobe, injury, possession, knowledge) → state derivable at any point | continuity notes; storylet qualities; Ink LISTs |
| 10 | **Dual anchoring: story-time AND text position, independent** | Aeon narrative view; EDL in/out pairs; OTIO source_range; MusicXML |
| 11 | **Narrative container tree** (acts/chapters/scenes in told order) | Aeon folders; Plottr; stripboards |
| 12 | **Eras/act grouping on the axis** | TimelineJS; World Anvil; Tale of Years Ages |
| 13 | **Variable granularity** — densify where the story densifies | Tale of Years' Great Years |
| 14 | **Space+time joint anchoring** (per-location history derivable) | WA Chronicles map pins; ASOIAF worldlines |
| 15 | **Derived per-entity matrices** — the **DOOD test**: character × chapter presence/state must be computable | Day out of Days; Aeon Relationship View |
| 16 | **Ongoing/open-ended events** | Aeon |
| 17 | **Sparse ordinal indices** for insertable milestones per thread | Bethesda quest stages |
| 18 | **Engineering hygiene**: readable JSON, per-object metadata dict, versioned schemas, stable IDs, OPEN spec | OTIO; Aeon's closed format as cautionary tale |

## The two deepest cross-cutting lessons

1. **Every mature practice separates the event record from its orderings** — chronological, narrative/told, shooting/release — each ordering a *view* over one event store. Aeon, EDL, wikis, stripboards all independently converged on this.
2. **Uncertainty and evidence are data, not annotations.** Every community that maintains timelines for decades (Tolkien scholars, ASOIAF spreadsheeters, Memory Alpha) records *why* a date is believed, with explicit precision/confidence.
