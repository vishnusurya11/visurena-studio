# Trailer blueprint — the checklist an agent follows without thinking

The brick of automation: **a blueprint an agent follows blindly is a program
whose only free variables are typed fields.** The model fills a schema; a
gate with a fixed number decides; a failed gate takes the next rung of a
ladder that changes the FORM and keeps the FUNCTION; the last rung is a
fallback that always exists. Nothing asks a human. Everything is logged.

## Run it

```
uv run python trailer.py                 # every book whose screenplay completed
uv run python trailer.py <codex_id>      # one book
```
Then read `library/<book>/trailer/main/qc.json` and `learnings.jsonl`.
That is the whole interface. If you are an agent asked to "make the trailer",
you run the command, you report those two files, you stop.

## The control law

- **Ceiling 6 h wall-clock per book.** Not a target: a run that passes every
  gate first time finishes in ~4 h and leaves. Unused share rolls forward.
- **Every retry is an adapt, not a repeat.** The ladder changes the form
  (seed → alternate shot / next line / re-authored caption) and keeps the
  function (this beat, a hook, this register). Same seed twice is a bug.
- **The terminal rung is always reachable and never asks.** Voice → card;
  vocal → instrumental; lines → music-only; metre → onset grid; character →
  unbound; beat → dropped. A run cannot end without a master file unless a
  deterministic step crashes, and a crash is a bug to fix, not a gate.
- **A floor below which nothing ships:** master exists, title on the measured
  hit, every shot with a character reference-bound, integrated −14 ± 1.5 LUFS,
  true peak ≤ −1 dBTP. Everything above the floor is a number in `qc.json`.
- **Every rung taken writes a learning:** `{step, attempt, gate, measured,
  threshold, action, seconds}` → `learnings.jsonl` + a WARNING line in the
  step's JSONL log; the step's `completed` event carries "N rung(s) taken" in
  its detail (the events vocabulary is fixed: started/completed/failed/skipped).
  The retrospect reads `learnings.jsonl`, never memory.

## Time shares (minutes of the 360)

| step | share | what eats it |
|---|---|---|
| 01 story | 5 | one agent call |
| 02 refs | 40 | image renders, identity gate |
| 03 music | 30 | 4–8 seeds at ~2 min + tracking |
| 04 lines | 10 | Wikiquote + one labelling call |
| 05 voice | 15 | ≤ 4 speakers × ≤ 12 lines at ~10 s |
| 06 plan | 5 | code |
| 07 clips | 210 | ~11 min per setup, ~16–20 setups |
| 08 assemble | 10 | ffmpeg |
| 09 qc | 15 | track + scene-detect + ≤ 2 re-cuts |
| 10 deliver | 5 | Telegram |
| slack | 15 | rolls into whichever step is running late |

A step reads `budget.remaining(step)` before every render or call. When it
cannot afford the next rung it takes the terminal rung and logs why.

## The ten steps — input → output → gate → ladder → fallback

Each row is the whole contract. Schemas live in `studio/trailer_spec.py`.

**01 story** — in: `analysis/`, `screenplay/`. out: `story.json`
(`StorySpec`: lead, figure, turn, resolution, restricted_scenes, narrator,
register, thesis). gate: lead in ≥ 25% of candidate scenes; register ∈ enum;
thesis ≤ 7 syllables, no proper noun, present tense. ladder: agent call ×3
with the violation quoted back. fallback: register `procedural`, thesis
`null` (vocal path off), narrator by first-person pronoun ratio.

**02 refs** — in: `story.json`, cast cards (the book's own verbatim portrait
sentences first - `refs/portraits.json` - then the dossier, then the pool;
a slot the book states outranks the rotation). out: `refs/<char>.png`,
`refs.json` (a TRAIT CARD per character: age, hair colour/length, facial
hair, headgear, complexion, build, read by the local VLM `describe.py`;
plus `closest`/`differs` against the cast bound so far). gate: the sheet
differs from every bound character in ≥ `DISTINCT_AT` (3) seen traits -
the `refuse_collision` rule applied to pixels. A card seeing < 4 traits is
accepted `unverifiable`. The VLM is asked to DESCRIBE in a closed
vocabulary, never yes/no. A render is judged for FIDELITY first: a card
whose reading disobeys the BOOK'S words on a channel-reliable trait (hair
colour/length, facial hair, headgear - `distinguish.RELIABLE`; complexion,
build and age are dead on this channel, run 4: 7/7 sheets read fair/average)
fails `faithful`, not the collision gate. Only the slots the book filled
(`card["asserted"]`, plus a woman's beardlessness) are owed; a slot the
rotation invented to separate the cast is the render's to decide, and once
bound the card's text is rewritten to what was drawn (`distinguish.adopt`)
so take prompts agree with the sheet (run 7: Holmes unbound over invented
sandy hair under a bowler). ladder: the first render, then
`distinguish` ×3 - a collision rewrites exactly the traits that matched, to
phrases no other character holds, and drops the book's sentence when it
asserted the moved trait; a disobedient render goes again AS WRITTEN on a
new seed. fallback: character `unbound` → every setup needing it is
excluded at 06.

**03 music** — in: `story.json` (register, thesis), `tone.json`. out:
`music/cue-<seed>.flac`, `music/metre.json` (`Metre` per seed: beats,
downbeats, bpm, bar, bars_in_mode, events, slots, fitness), `music/chosen`.
gate: best fitness ≥ floor AND slots ≥ 1 AND bars_in_mode ≥ 0.65. ladder:
4 seeds → 4 more → re-author caption same register (swap pulse carrier) ×2.
fallback: best-of-all, `grid: onsets`, flagged `rubato`. Vocal path only if
thesis present AND register ∈ {elegy, gothic, romance, coming-of-age,
tragedy} AND stem gaps ≥ 2; else instrumental, no retry.

**04 lines** — in: pools (screenplay, character quotes, source quoted
speech, narration), `analysis/iconicity.json`. out: `lines/slate.json`
(`LineSlate`: ordered lines with speaker, function, kept, words). gate:
≥ 1 hook AND ≥ 1 threat-or-stakes; no line names the figure's identity.
ladder: label the next 10 ranked lines ×2. fallback: empty slate → music-
only, flagged. Wikiquote offline → last cached revid → `iconicity: thin`.
fit: each line is chosen for the slot it occupies, never `atempo`d; on the
rubato path a line may overrun its trough by one ducker release
(`DUCK_OVERRUN` 1.0 s) for at most `MAX_DUCKS` (2) lines — the bed ducks
under it for as long as it runs (08). On the metre grid the return downbeat
is never crossed.

**05 voice** — in: `slate.json`, cast cards. out: `voice/voices/`,
`voice/lines/*.wav|json` (measured seconds, similarity). gate: similarity
≥ 0.75. ladder: seed ×3 → next line with the same function. fallback: card.
Unattributed line → card without trying.

**06 plan** — in: `metre.json`, `story.json`, `slate.json`, voice seconds,
screenplay shots. out: `plan.json` (`TrailerPlan`: cut list in beats, setups
bound to refs, lines in slots). Setups = one per cut, capped at the takes 07's
remaining share affords (`remaining("07") // 11 min`, one take held in reserve
so a reroll costs no beat); `shots_for` scatters them, ≤ 3 shots per take,
≥ 3 between returns. gate: no unbound setup; lead ≥ 25% of beats;
every register present; every L0 event cut on; no shot < MIN_SHOT or > cap
except the hold and the title. ladder: unbound → alternate setup in the same
beat → location-only shot. fallback: drop the beat, re-walk.

**07 clips** — in: `plan.json`, refs. out: `clips/<setup>.mp4`,
`clips.json` (trait card per take, `similarity`, `differs`, `known`,
seconds). A take runs `max(CLIP_SECONDS, longest shot of the beat +
HEAD_TRIM)` (`build_clips.take_seconds`): the hold outruns MAX_SHOT by
design, and a take that cannot hold it starts the cut inside the reference
leak (run 6). gate: three frames after the head leak, laid side by side in ONE
contact sheet (the VQA node reads only image[0] of a batch) and described by
the VLM into one card, differ from the reference card in < `DISTINCT_AT` (3)
traits; a card seeing < 4 traits is accepted `unverifiable` and flagged.
ladder: seed ×1 → whole-take close-up ×1 (a seed moves the reading about
half a trait: B12 read 4.0 then 3.5 in run 6), each rung priced at
`RENDER_SECONDS × (beats left + 1)` so a retry may cost this beat but never
a later beat's first render (`ladder_for`; run 6 rerolled B12 twice and
dropped eight beats); terminal: the BEST take capped at 0.6 s (the cut
sources longer shots of that beat from a neighbour). A beat is dropped only
when no take exists: `budget.can_afford(11 min)` false
before its first render, or the render failed. Every take is kept under
`clips/takes/`.

**08 assemble** — in: everything above. out: `TRAILER-*.mp4`. gate: none —
deterministic; an exception is a bug and the run fails loudly here only.

**09 qc** — in: the master, `plan.json`, `metre.json`. out: `qc.json`
(cuts_on_beat, cuts_on_downbeat, cuts_on_L0, on_cap_fraction,
title_on_downbeat, line_over_bed_lu, loudness, true peak, floor: pass).
gate: floor pass; targets ≥ 80% / ≥ 30% / 100% / ≤ 10% / true / ≥ 5 LU.
ladder: re-cut ×2 with scene-detect threshold lowered and walk stretch
adjusted (free). fallback: ship with every miss listed under `flags`.

**10 deliver** — in: master, `qc.json`, `learnings.jsonl`. out:
`manifest.json`, Telegram message with the file and the flags. The file
sent is the master when it is ≤ 50 MiB (the Bot API cap) and otherwise a
CRF-20 copy at `work/telegram.mp4` (`deliverable`; run 6b's master was 45 KB
over and died with a bare TLS EOF ×3). ladder: send ×3. fallback: file
stays in the library; manifest records `undelivered`.

## What the model is allowed to decide

Exactly four structured calls per run, each `llm.structured(tier, prompt,
Schema)` with a `FakeModel` in tests: (1) register + thesis + narrator,
(2) line function labels, (3) the music caption from `tone.json`,
(4) voice instructs from cast cards. Every one is gated by code and
retried with the violation quoted. Nothing else is judgment. Shot prompts
come from the screenplay's authored shots; captions and instructs are
templates filled from typed fields with one free-text sentence each.

## What the retrospect reads

`learnings.jsonl` across every book, grouped by `(step, gate)`. A gate
that fails on most books is mis-set or the step upstream is wrong; a rung
that is always taken should become the first rung. That is how the skill
improves: numbers from runs, edited by a person or an agent, tested before
merge. The run itself never edits the skill.
