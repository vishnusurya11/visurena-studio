# C — The production office: work orders, the call sheet, the wrap report

Expert C (production-office manager / post supervisor). Round: command center, 2026-09-25.
Grounded on `stages.yaml`, `gates.yaml`, `architecture/README.md`, the future-departments
decision, `docs/command_center/DESIGN.md`, the episode skill, `studio/db.py` / `spend.py`,
and the WotW units `ep11` (delivered, public), `ep12` (in QC), `ep13` (plan deferred).

## 0. The brick

A studio runs departments on paper, not on people's memory. The paper is the **work order**:
one sheet per (unit, department) that says what came in, what must go out, where it stands,
and who signed. Everything else — the call sheet, the dailies notes, the redo request, the
wrap report — is a **query over work orders** or a **row attached to one**.

- **Base case:** one row `(book, department, unit)` with a turnover-in, a deliverables-out,
  a derived status and the signature that closed it.
- **Recursion:** a department's deliverable is the next department's turnover (registry
  `requires:`). A unit's steps are rows of the same shape one level down (`(unit, step)`);
  a season is a roll-up of unit rows; a step's retake rounds are rows one level further.
- **Closure:** every department today (analysis, screenplay, refs, episode, trailer) and every
  future one (publish, analytics, promo, feature, song, audiobook, game, book) fits the
  same seven columns. A department that needs an eighth column is mis-cut.

Status is **derived**, never typed. The events table and the verdict files already hold the
facts; the office's job is one view that a coordinator can read in ten seconds.

## 1. The standard department contract (one row per department)

Columns: unit key · **turnover IN** (must exist + the upstream signature) · **deliverables
OUT** (artefact, format) · **what makes it final** (QC/sign-off) · **the tracking row's
progress counter** (the "18/25" a coordinator quotes).

| department | unit | turnover IN | deliverables OUT | final when | progress counter |
|---|---|---|---|---|---|
| **analysis** | `book` | `source/*.epub` + `codex` row | `analysis/book.json`, `chapters/ch_NN.json`, `extraction/ch_NN.json`, `scenes.json`, `timeline.json`, `characters/<id>.json`, `locations/<id>.json`, `qc_report.json` | `analysis/06 verify` completed; `qc_report.json` verdict | chapters extracted / chapters (02_03 fan-out) |
| **screenplay** | `(book, target)` | `analysis/05` completed; `targets.yaml` row | `screenplay/<target>/plan.json`, `screenplay.json`, `.fountain`, `.pdf`, `elements.json`, `qc_report.json` | `screenplay/05 verify` completed; no blocking finding | beats drafted / beats (03 fan-out) |
| **refs** (the bible) | `(book, style)` | `analysis/05` completed; cast list | `refs/refs.json`, `refs/sheets/*.png`, `refs/pack.jsonl`, `cast/<id>/voice/*`, `refs/verdict.json` | `judge:look@1` signs `verdict.json` bound to the pack sha (`pass` or `flagged`) | entities bound / entities the unit needs |
| **episode** (production) | `(book, chapter)` | `analysis/06` + `refs/04` completed; bound rows stamped for this unit; `screenplay/<target>` if any | `plan.json` + `plan.verdict.json`, `audio/lines/*`, `placed.json`, `storyboard/shot_NN.png` + `panel_dq/content.json` + `eye_<sha8>.json`, `takes/r2v/T*.mp4` + `.dq/.content.json` + `eye_<sha8>.json`, `cut/master_iterN.mp4`, `reports/qc.json`, `review/eye_<sha8>.json`, `manifest.json` | `episode/12 deliver` completed: `manifest.json` names every verdict's sha8 and they all match the master's bytes | takes judged / shots; then `master_iterN` |
| **trailer** | `(book, "main")` | `screenplay/05` + `refs/04`; a `promo` order (future) | `trailer/main/story.json`, `music/metre.json`, clips, `master.mp4`, `qc.json`, `manifest.json`, `learnings.jsonl` | `trailer/10 deliver` completed | clips rendered / setups |
| **publish** (future) | `(master sha8, platform)` | a production `deliver` manifest; `review/eye_<sha8>.json`; `series.json` `synthetic` + policy | `publish/<sha8>/<platform>.json` (id, url, dates), versions bundle, `PublishManifest`, thumbnail, `uploads.jsonl` row, `catalog.json` entry | `publish/07 release` completed with the platform's live status read back; PUBLISH signature (owner or `auto_public` policy) | bundle items done / 5 (video, audio, text, art, metadata) |
| **promo** (future) | `release` | `publish/01 intake` (a release exists); analytics reading | `promo/<release>/campaign.json`, `order.json` rows, `keyart/*.png`, `cutdowns/*.mp4`, `posts.jsonl` | every order row delivered by its line and every post shipped through publish | orders delivered / orders |
| **analytics** (future) | `(master sha8, platform)` on a schedule | `publish/07` completed | `<platform>_stats.jsonl`, `reading.json`, casebook candidates | never "final": each run is a new row | runs / scheduled runs |

Same shape every time. The registry already carries three of the seven columns
(`unit`, `requires`, step list); the office adds the deliverables list and the counter.
**Ask each department for its `deliverables:` block in `stages.yaml`** (path glob + the
verdict that makes it final) so the row is generated, not hand-written.

## 2. The status vocabulary (derived from `events` + files, never typed)

| status | a coordinator's meaning | derivation rule |
|---|---|---|
| **not started** | nobody has touched it | no event for `(codex, stage, unit)` and turnover incomplete |
| **in prep** | upstream is working on what we need | turnover incomplete, and at least one `requires:` stage has a `started` event |
| **ready** | turnover complete, waiting for a slot | every `requires:` step `completed`; no event of ours yet |
| **in progress** | a runner holds it now | last event for any step is `started` with no matching `completed`/`failed` |
| **in review** | made; the judges are on it | the department's last making step `completed`; a verdict file the next step needs is absent or its sha8 is stale |
| **approved** | every gate signed pass; nothing flagged | every verdict for the current sha8 is `pass`; `deliver` not yet run |
| **approved, flagged** | signed at a terminal rung; the owner has not looked | any current verdict is `flagged`; audit sheet written; no owner note on it |
| **delivered** | the deliverable left the department | `deliver` (or the last step) `completed`; downstream turnover satisfied |
| **on hold** | stopped on purpose | `RENDER_HOLD` at root, or a `HOLD` file in the unit folder with a reason |
| **needs attention** | a person must act | last event `failed`, `escalated` or `deferred`; or a flagged terminal older than 24h with no owner note; or an open redo row |
| **redo** | the owner asked for a piece again | an open row in `redo.jsonl` names this unit; cleared when a newer verdict for that step is signed |

Precedence when several rules match: on hold > needs attention > redo > in progress >
in review > approved(,flagged) > delivered > ready > in prep > not started.
`in review` maps onto `events.event = 'escalated'` only in the pre-judge world; under
`gates.yaml` `auto` it is the window between a making step and its judge's signature.

## 3. Units of work

Same row shape; only the unit-key grammar and the department differ.

| unit | key | department | roll-up? |
|---|---|---|---|
| chapter | `ch04` (or `ch04-05`) | episode (also audiobook) | no — it is the row |
| episode | = its chapter unit; `epNN` on disk | episode | no |
| season | ordered unit list in `series.json` | none — a **view** | yes: status = worst child; counter = children delivered / children |
| trailer | `main` | trailer | no |
| short | `(book, scene_12)` | shorts | no |
| song | `(book, cue_03)` | song | no |
| release | one master or a season launch | promo | yes: over its order rows |

A roll-up row is computed, never stored: a season is "11/27 delivered, 1 in review, 1
needs attention, 14 not started". Every unit folder is its own filing cabinet
(`episodes/ep12/`), which is right; the office only needs the index.

### The call sheet — one GPU, one day

The scheduler (`studio.py`, migration commit 7) is the 1st AD. Its sheet, regenerated on
every event, has five blocks and nothing else:

```
CALL SHEET  2026-09-25  wrap of day: 23:59 local        GPU: 4090, one lease
NOW        episode ep12  step 11 qc      started 07:53  expect ~20 min   holds the GPU
NEXT       1. episode ep12  step 12 deliver         free       (after NOW)
           2. episode ep13  step 02 plan  RETRY     text only  runs beside the GPU
           3. episode ep14  step 01 bind            ready
WAITING ON ep13 steps 03-12  <- ep13/02 plan (deferred: battery CONTRACT line order)
           publish ep12@youtube  <- episode/12 deliver + review/eye_<sha8>
ON HOLD    (none)            RENDER_HOLD: absent
ATTENTION  ep13  plan deferred, 5 passes, "a line's shot never precedes an earlier line's shot"
           ep12  EYE_PANELS flagged 531 rows (landmark x527) - owner has not looked
           ep12  plan.verdict.json has no signed_by
```

Rules: GPU steps are serialised (one NOW); text-model steps (`analysis`, `screenplay`,
`episode/02`) are a **second unit** and run beside the GPU; NEXT is ordered by
`series.json` order, then cheapest step first. The registry needs a `gpu: true` mark per
step so the sheet knows what competes for the lease.

## 4. Approvals, audits, redo

Gates are signed by judges; the owner audits afterwards. The office therefore tracks
**signatures, findings and redo requests** — three tables, two of which exist as files.

| table | what a row is | exists as | office needs |
|---|---|---|---|
| `verdicts` | one judge signature: unit, gate, judge, sha8, pass/flagged, fault count, artefact, date | `plan.verdict.json`, `eye_<sha8>.json`, `review/eye_*.json`, `refs/verdict.json` | a view that lists them per unit with **currency** (does the sha8 match the artefact now on disk); dedupe the fault list to `kind x where` counts |
| `notes` (dailies notes) | one owner finding: unit, artefact, class or `pass`, words, date | `casebook/owner.jsonl` via `scripts/audit/note.py` | also a row for "looked, no finding" so the sheet can say *audited on 09-25* |
| `redo` | one request: id, unit, step, artefact sha8, class, words, requested (date), status open/done, closed_by (new verdict sha8) | **missing** | `library/<book>/redo.jsonl`, append-only |

**How a redo enters the system:** `scripts/audit/redo.py <codex> <unit> <artefact> <class>
"<words>"` appends the row (and the same words to the casebook as a note). The runner's
currency check treats an artefact named by an open redo row as **stale**, so the next run
of that step redraws/retakes it through its normal ladder; the row closes itself when a
newer verdict for that step is signed. No hand edit of a verdict, no button that flips a
status. A redo against a delivered master reopens the unit to `redo` and blocks publish.

A second redo on the same artefact class inside a unit is a **bench case**, not a third
render: the row is tagged `escalate: judge` and the wrap report lists it.

## 5. The daily production report (sent at wrap)

One text block through `notify()` at wrap, or on `uv run python studio.py --wrap`:

| line | number | source |
|---|---|---|
| Units advanced | steps `completed` today, grouped by unit | `events` |
| Delivered | masters with `deliver` completed today | `events` + `manifest.json` |
| Published | `uploads.jsonl` rows with `privacy: public` today | `library/<book>/uploads.jsonl` |
| GPU hours | sum of started→completed for steps marked `gpu: true` | `events` (today: `timing.jsonl` per unit, which must fold into `events`) |
| Paid spend | `usage.cost_usd` sum + credit ledger (when shorts exists) | `studio/spend.py` |
| Failures | `failed` events, each with its unit/step/detail | `events` |
| Flagged terminals | new `audit/rows.jsonl` rows, count per gate | `library/<book>/audit/rows.jsonl` |
| Redo | opened / closed today | `redo.jsonl` |
| On hold / attention | the call sheet's last two blocks, verbatim | derived |
| First call tomorrow | the NEXT block's first line | derived |

Sample: `WRAP 09-25 — advanced: ep12 (08→11), ep13 (01, 02 deferred). delivered 0.
published 1 (ep11 → public 01:20). GPU 6.4 h. paid $0.00. failures 0. flagged: ep12
EYE_PANELS 1, EYE_TAKES 1. redo 0/0. attention 3. first call: ep12/12 deliver.`

## 6. What real studios track that this studio should NOT

- **Crew and cast scheduling** (availability, call times, turnaround, meal penalties,
  union rules): no crew; the only resource is one GPU lease and a text tier.
- **Script revision colours**: the plan sha8 is the revision; `PATCHED_BY_HAND` is the note.
- **Locations, permits, insurance, releases**: none.
- **Asset version trees** beyond `master_iterN` / `attempts/` / `superseded/`: the disk
  convention is enough; no VFX-style versioning DB.
- **Budget actuals vs estimates per line item**: two numbers (paid USD, GPU hours) per
  unit; nothing per shot.
- **Kanban boards with draggable status, @mention threads, roles/permissions, per-event
  notifications**: one owner, status derived, one wrap ping plus one attention ping.
- **ETA forecasting**: an average of `timing` per step is the whole model.
- **Approve/Reject buttons on parked nodes** (DESIGN.md §5): obsolete since
  `2026-09-24-automate-the-taste-gates`; nothing parks. The buttons become `note` and `redo`.

## 7. Where the current design fails a coordinator's eye

1. **No unit row.** `events` is per step; `timing.jsonl` is per unit but its `stage` names
   (`lines`, `respot`, `panel_dq`, `grids`) are not registry step names (`record`,
   `timeline`, `panels`, `board`). Nothing says "ep12: in review, 24/24 takes, retake
   rounds 1, QC failed once". The counter has to be recomputed from file globs.
2. **A signature a coordinator cannot file.** `ep12/plan.verdict.json` has no `signed_by`
   and reads "Re-signed by Claude on the owner's instruction"; `gates.yaml` says
   `judge:plan@1` signs PLAN. Either it is a judge verdict or it is an OVERRIDE row.
3. **Unreadable flags.** `ep12/storyboard/eye_c7e3eb93.json` carries 531 faults, 527 of
   them `landmark at shot_0N` for every noun in the landmark list ("cathedral drawn where
   the place names none"). A judge that fires on every noun is a bench case; a coordinator's
   row needs `kind x where` counts and the top three.
4. **Rows that mean nothing.** `ep12/learnings.jsonl`: gate `budget`, measured `-2992.8`
   against `102`, `keep_best`. Nobody can act on it.
5. **Progress lives in folders.** takes judged vs shots = `takes/r2v/T*.mp4` against
   `plan.json`; retake count = `attempts/` file count; "three retake rounds" survives only
   in `youtube.json` prose.
6. **Published state is outside the ledger.** `uploads.jsonl` at book level; `publish` is
   not a stage, so `events` never sees a release.
7. **The owner's audit leaves no trace.** `casebook/` holds `labels.jsonl` only; no
   `owner.jsonl`, so nothing can say "ep11 audited on 09-25" or "never audited".
8. **Hold is global only.** `RENDER_HOLD` stops everything; there is no per-unit hold.
9. **GPU hours are not in the DB.** `usage` holds tokens; seconds sit in `timing.jsonl`.
10. **Deferred is an event without a row.** ep13's `plan.deferred.json` (battery: line
    order) is on disk; the sheet needs it as *needs attention* with the reason.

## 8. Worked example — the board as a coordinator would see it (2026-09-25)

| unit | dept | status | progress | last step | verdicts (current sha8) | attention | audited |
|---|---|---|---|---|---|---|---|
| ep11 | episode | **delivered** → publish **delivered** | 23/23 takes; master_iter2; 3 retake rounds (16 attempts) | publish release → public 01:20 | qc PASS on d8833608; pre-judge unit: no PLAN/EYE/MASTER files | none | no owner note on file |
| ep12 | episode | **in review** (approved, flagged pending MASTER) | 24/24 takes; master_iter2; 10 attempts; 1 QC line row failed | 11 qc on b803fe0d | PLAN APPROVE (no signed_by); EYE_PANELS flagged 531; EYE_TAKES flagged; MASTER **absent** (`review/` has speaker_check only) | plan signature; panel-eye noise; MASTER not signed | not audited |
| ep13 | episode | **needs attention** (plan deferred) | 0/? shots; bind done; places 0.2 s (nothing drawn) | 02 plan → `plan.deferred.json`, 5 passes | none | battery CONTRACT: "a line's shot never precedes an earlier line's shot" | n/a |
| season | view | 11/27 delivered · 1 in review · 1 attention · 14 not started | | | | | |

Call sheet NOW/NEXT for the day: ep12 → 11 recut/eye → 12 deliver → publish; ep13's plan
retry runs on the text tier beside the GPU; ep14 bind is ready.

## 9. Three doubts for the debate

1. **Derived status vs a stored `work_orders` table.** Derivation keeps one truth, but the
   view needs file globs across `library/`, and a UI polling every 2 s over 27 unit folders
   will be slow. Materialise the row on every event (cheap, one writer) — or accept a
   slower page?
2. **Where does a redo live** — `library/<book>/redo.jsonl` (book-neutral, beside the
   casebook) or a `redo` event in `events` (the ledger is the truth)? I lean file + event
   mirror; the debate should pick one writer.
3. **Is "in review" honest under auto judges?** With every gate `auto`, the window between
   a making step and its signature is seconds; the coordinator's real "in review" is the
   *owner's* audit, which nothing records. Either add the "looked, no finding" note row and
   call that `in review → audited`, or drop the status and keep `approved, flagged`.
