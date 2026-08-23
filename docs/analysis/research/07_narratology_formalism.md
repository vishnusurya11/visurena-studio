# Research 7 — Narratology & formal representations of narrative time

*Wave-2 subagent report, 2026-08-22. The theory layer for the timeline format.*

**Bottom line:** No standard covers "character X at location Y doing Z at story-time T, narrated at discourse position D, witnessed by W" — but every primitive has been formalized somewhere. Closest artifacts: **NarrativeML** (Mani; TimeML + narrator/focalization/levels — spec only, no tooling), **NOnt** Narrative Ontology (RDF; explicit fabula/narration split), **ISO-TimeML** (the only ISO piece; time axis only). A new format is justified — **as a synthesis of ~14 known primitives, not an invention.**

## 1. What theory FORCES into the data model

- **Fabula vs syuzhet** (Formalists; Bal; Chatman story/discourse): every event carries two independent coordinates — story-time and discourse position — neither derivable from the other.
- **Genette's five categories**:
  1. **Order** — analepsis/prolepsis with *reach* and *extent*. → dual coordinates; discourse position may jump arbitrarily in story time. **Never store "is_flashback" — derive it.**
  2. **Duration** — ellipsis / summary / scene / stretch / pause. → durations on both clocks; **ellipsis = story intervals no text covers; pause = discourse spans with zero story duration.** Pacing = the ratio, computable.
  3. **Frequency** — singulative / repetitive (told n times, happened once) / iterative ("every Sunday" — told once, happened n times). → **many-to-many mention↔event mapping** + recurring event-sets as first-class records.
  4. **Mood/focalization** — who *perceives* (zero/internal/external), distinct from narrator. → per-segment focalizer field; epistemic scoping of events.
  5. **Voice** — who *tells*: narrator level (embedded narratives → **narrative-level index**), person, time of narration (epistolary novels have a **third clock**: narration time — Dracula!).
- **Realis/modality**: fiction is full of wished/planned/feared/dreamed/counterfactual events. LitBank annotates only *asserted realis*; Gervás (2024) shows modal events need own timelines. **No bare "event happened" records.**

Bridge paper: Piper, So & Bamman, "Narrative Theory for Computational Narrative Understanding" (EMNLP 2021).

## 2. Formal systems and what each contributes

| System | Contribution |
|---|---|
| **Story Intention Graphs / DramaBank** (Elson 2012) | Three-layer separation: text spans ↔ timeline propositions ↔ interpretation (goals/beliefs/affect, typed agency arcs) |
| **Plot units** (Lehnert 1981) | Per-character affect-state trajectories; plot = pattern over state changes, not raw actions |
| **Narrative event chains** (Chambers & Jurafsky 2008-09) | The character-centric chain as a first-class projection |
| **Fabula Model** (Swartjes & Theune 2006, after Trabasso) | Node types incl. **Perception** (belief caused by perceiving an event — the witness primitive, formalized 2006); typed causal edges: physical / motivation / psychological / enablement |
| **Event calculus** (Mueller) | **Events vs FLUENTS** (time-varying states) with Initiates/Terminates; HoldsAt(f,t) queryable. **Character-at-location is a fluent** — the correct mechanic for "where is X in ch 12" when ch 12 never says |
| **NOnt / OntoMedia / GOLEM / CIDOC-CRM** | Fabula/narration split as published Linked Data; OWL-Time; event-participant-place-timespan patterns; export surface |
| **NKRL** (Zarri) | **N-ary role-frame events** (agent/object/source/destination/location + modulators) — RDF triples flatten this badly |
| **ESO / Event StoryLine** | Pre-/post-situations of events; timeline vs causeline vs storyline distinction |
| **ProppLearner / Story Workbench** (Finlayson) | **Layered standoff architecture**: 18 annotation layers stacked over stable text coordinates, TimeML at the base |
| **NarrativeML** (Mani 2012/2022) | TimeML + narrator, FOCALIZER, narrative levels, pace, fictional entities — closest existing answer, never became a standard |
| **R² causal plot graphs** (2025) | LLM extraction needs per-edge strength/confidence + cycle-breaking + hallucination-aware refinement baked in |
| **Living the Novel** (2025) | Every node linked to a diegetic-time node → agents whose knowledge is a function of story time; timeline-coherence test penalizes spoiler leakage |
| **TimeChara** (2024) | Point-in-time character hallucination benchmark — knowledge horizons must be story-time-indexed |
| **Gervás & López Calle** (Text2Story 2024) | Requirements for complex chronology (Memento/Pulp Fiction): relative chronology, two timelines, **multiple worlds each with own timeline**, modal events |

## 3. Temporal machinery

- **ISO-TimeML**: EVENT classes (OCCURRENCE, STATE, I_STATE, I_ACTION, REPORTING, **PERCEPTION**, ASPECTUAL); **TIMEX3** (DATE/TIME/DURATION/**SET** for recurrence; `anchorTimeID` for "three days later"; `mod=APPROX`); TLINK = 13 values ↔ **Allen's interval relations**; **SLINK** (MODAL/EVIDENTIAL/NEGATIVE/CONDITIONAL — built-in realis machinery).
- **Allen's interval algebra** (1983): 13 exhaustive qualitative relations assert order without dates (fiction's native condition); **disjunction sets** express partial knowledge ("meanwhile" = {overlaps, during, starts, equals…}); **composition-table propagation detects contradictions** across a whole book's network. Metric complement: **STP/TCSP** (Dechter-Meiri-Pearl) — numeric [min,max] bounds on offsets. A robust story-time engine = qualitative constraints + optional metric bounds + calendar anchors.
- **Narrative containers** (Pustejovsky & Stubbs 2011): a default temporal bucket events fall into unless marked — in fiction, **scenes and chapters**. The single best trick for keeping the constraint graph sparse.
- **NarrativeTime** (LREC-COLING 2024): first timeline-based (not pairwise) dense scheme with bounded-vagueness encoding; densely annotated **fiction** corpus; lossless to TimeML. Reusable methodology.
- **TLEX**: extracts an exact global timeline from a TimeML graph — main timeline + **subordinated timelines** (hypotheticals, reported speech) + **indeterminacy flags**. Proof of the two-representation architecture: **raw constraints stored; solved global timeline derived and regenerable.**
- **Character-place grounding** research: the char-place relation needs a **spatial-relation type** (in/near/from/toward) + temporal scope, not a bare pair.

## 4. TEI

Offers: `<said who>` quotation attribution; `persName/placeName @ref` → canonical registries; `@notBefore/@notAfter` ISO-8601 uncertainty bounds; standoff `<interp>/<span>` layers; `<floatingText>` embedded narratives. **Nobody uses TEI as a narrative-timeline interchange format.** Contributions to ours: stable text-coordinate + standoff discipline, entity registries with `@ref`, the notBefore/notAfter idiom. Focalization annotation at scale is now feasible zero-shot with LLMs (arXiv 2409.11390).

## 5. The 14 primitives a new format needs (each with pedigree)

1. **Event instance** — typed (action/state-change/perception/reporting; TimeML classes) with **realis/modality flag** (actual/planned/wished/dreamed/counterfactual/disnarrated).
2. **Fluent** — character-at-location, possession, alive/dead, relationship, emotion — with **initiated-by/terminated-by** event links (event calculus; ESO).
3. **Participants with typed roles** — agent/patient/experiencer/**witness**; n-ary frames, not triples (NKRL, SIG, CIDOC).
4. **Canonical entity registry** — IDs, aliases, coreference to every surface mention (TEI @ref, BookNLP).
5. **Story-time anchor** — interval with optional calendar value, notBefore/notAfter bounds, granularity, APPROX mod; **default inheritance from container**.
6. **Ordering relations** — Allen relations (+ disjunction sets) + optional metric offsets, stored as **raw constraints**; solved global timeline + indeterminacy flags = derived view (TLEX).
7. **Narrative container** — scene/chapter as default temporal scope (Pustejovsky & Stubbs).
8. **Discourse anchor** — precise text coordinates per *mention*, **many-to-many mention↔event** (Genette frequency; SIG text layer). Anachrony and pace are derived, never stored.
9. **Recurring event-set** — first-class habitual/iterative record (TIMEX3 SET).
10. **Narration segment metadata** — narrator ID, focalizer ID, focalization type, person, **narrative level**, **world index**; embedded narratives/worlds get own timelines linked to the frame only where licensed.
11. **Per-character epistemic ledger** — witnessed (participant/focalized) or learned (reporting event), indexed by story time (Perception nodes; Living the Novel; TimeChara). Enables spoiler-safe, POV-correct generation.
12. **Typed causal/motivational edges** — physical/motivation/psychological/enablement + **edge strength** (Trabasso; R²).
13. **Dialogue/quotation attribution** — speaker + addressee per quoted span (TEI said; PDNC).
14. **Provenance + confidence per assertion** — source span, extractor, confidence (R² hallucination-aware refinement).

**Design stance:** layered standoff architecture (Story Workbench pattern) — text-anchor / entity / event-fluent / temporal-constraint / narration / interpretation layers — serialized as JSON, with **lossless export mappings to ISO-TimeML and NOnt/CIDOC-CRM** for interoperability. A well-specified open format here (spec + JSON Schema + validator + one annotated public-domain novel as reference corpus) is itself a publishable standalone artifact.
