# Research 8 — Scene segmentation (for the 1st AD agent skill)

*Subagent report, 2026-08-23. Distilled; full sources in report. Feeds agents/skills/scene_breakdown.md.*

## The brick

**Cut where the camera could not keep rolling.** A scene = the maximal span one continuous
camera setup (one place-container, one continuous stretch of story time, one dramatic action)
could capture. Non-scene = what no camera could film at story speed (summary/iterative/pause).

## Converging definitions

- Film: new slugline when **location or time changes** — cast change alone NEVER forces a scene.
- Narratology (Genette/Gius, the academic standard): scene = story time ≈ discourse time, same
  place, one action, stable character constellation — all four *relative*. Prose also contains
  **non-scenes** (summary "the days passed", pause, iterative "he would often…") — film has no
  equivalent; every paragraph must belong to some segment.
- Gius' intuitive test: *could this be one movie scene? Boundaries are where a fade-out fits.*

## 1st AD breakdown fields (film practice)

Scene number · INT/EXT · location as written · DAY/NIGHT (finer collapsed) · one-line synopsis ·
length · cast **present and acting** (never merely mentioned) · **story day** (in-world day
counter — continuity's backbone). Flashbacks/dreams = separate flagged scenes; montage = ONE
scene; two-location phone call = one scene anchored at POV location.

## Documented failure modes (every study, esp. LLMs — the DON'T list's basis)

Whole-novel GPT-4/Claude/Gemini + guidelines FAILED (LaTeCH-CLfL 2025): split conversations at
speaker changes, over-segmented, got lazy on long context. Universal errors:
1. **Over-segmentation** — the #1 error everywhere. In doubt: MERGE (Gius §5 verbatim).
2. Any time-word/room-change treated as boundary — judge jumps *relative to ambient granularity*.
3. New-character introduction read as scene start.
4. Cutting at dialogue→description style shifts / inside dialogue exchanges or pronoun chains.
5. **Mention ≠ presence** (place/person referred to ≠ site of action).
6. Movement between connected sub-spaces of one container split wrongly.
Human boundary variance is ±3 sentences → **paragraph-precision quantization is standard**.
Scene granularity target: ~300–800 words; a chapter yields ~3–8 scenes, not 20.

## 19th-century hard cases (Gius/SANTA rules)

- Summary/travel/reflection passages → `nonscene` segments (own paragraph ranges).
- Short (≤2 ¶) transitional/reflective beats absorb into the adjacent scene.
- **Epistolary inserts & nested tales = diegetic level shift**: long embedded narrative → own
  scene(s) on ITS OWN timeline/locations, flagged {type: flashback|letter|dream|tale, narrator};
  frame resumes as a new scene after. Short letters stay in the frame scene as props.
  (A Study in Scarlet Part II = exactly this: third-person Utah flashback.)
- Narrator change alone, same world = NOT a scene change; narrator change + world shift = is.

## Decision procedure (per candidate boundary)

1. Did **action > characters > time > place** change (that priority)?
2. Does it redirect the plot, or is it absorbable under a container? 
3. Fade-out test. 4. Boundary at the paragraph where establishing material begins.
5. Final anti-fragmentation pass: merge undersized scenes; sanity-check scene count.

## Adopted schema additions (scene_breakdown.Scene)

`int_ext` (INT/EXT/UNKNOWN) · `time_of_day` (DAY/NIGHT/UNKNOWN) · `story_day` (int|null —
feeds step 04 directly) · `type` (scene|nonscene) · `frame` ({type, narrator, note}|null for
embedded) · `boundary_reason` (action/character/time/place/level — auditability).

Key sources: STSS@KONVENS 2021 + Gius guidelines (Zenodo 4457177) · Zehe EACL 2021 ·
Guhr LaTeCH-CLfL 2025 · LitSeg 2026 · SANTA 2 guidelines · StudioBinder breakdown/story-day
guides · Story Sense flashback format.
