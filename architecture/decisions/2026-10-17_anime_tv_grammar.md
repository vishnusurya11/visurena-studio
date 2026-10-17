# 2026-10-17 — The anime-TV grammar: framing and screenplay in the planner

Status: **BUILT 2026-10-17**. The grammar is the owner's ("I like the face improvements a lot
in wide shots, and reframe. Go ahead with changes", 2026-10-17); every number and rule
below that he did not name was decided on his behalf on the evidence, open to veto.
Evidence: `docs/audit/2026-10-16_model_research/04_screenplay.md`, `05_camera_framing.md`,
`03_h3_workflows.md`; `docs/audit/2026-10-16_model_tests/PART2_SUMMARY.md` with
`framing/results.json` (D1-D9) and `voice/results.json` (G1); the replay
`docs/audit/2026-10-17_anime_tv_grammar/replay.json`.
Tracker: `architecture/plan/2026-10-17_anime_tv_grammar.md`.

## The fault

Jekyll ep01 (23 shots) read as a narrated slideshow: 6 of 23 shots held a face a quarter
of the frame or more (the rest 3.5-15 %), 6 pushes and 1 locked shot, wides of 7.2 s,
inserts of 4-7 s carrying whole lines, a 16-word hook of scenery with no sound, holds spent
as 0.4 s crumbs, the bargain narrated though the chapter is 28 % speech.

The brick (05 §7): the frame holds a face large enough to read, and a CUT is the only
thing that changes size. H3 obeys a move's direction and ignores its amount, so a push is
no size control; a cut to a panel drawn at the new size is.

## The ruling

**The contract** (`studio/episode_spec.py`): `Episode.grammar` (`""` legacy, `anime_tv`),
set by CODE from the brief's band, never by the writer; `Episode.motif` (the book's
recurring image: series.json, else ep01's plan); `Episode.tease`; sections `act_out` (at
most one) and `tease` (the one last shot, after the button's); the line kind `inner` (at
most 8 words, a cast member's, over his own face, no lips); the dialogue outer wall 35 %
(`DIALOGUE_CEILING_MAX`). Every field defaults, so every plan on disk loads.

**The gates** (`studio/framing_grammar.py`, `studio/screenplay_grammar.py`,
`studio/episode_capacity.py`, one call `studio/grammar_battery.py`, the battery's
`GRAMMAR` row): HARD on a plan declaring `grammar: anime_tv` until something is drawn
from it; advice on every legacy plan (the G-MOVES / `source` switch precedent).

| gate | rule | measured on |
|---|---|---|
| G-FACES | >= 55 % of the cut at close / medium_close with a face | 05 §2.2; D3 4.9 -> 11.3 %, D5 35 -> 40 % |
| G-WIDE | <= 2 wides, each <= 4 s (the opener 5 s) | D1/D6: a wide's men read 3.6-4.8 % however framed |
| G-MEDIUM | a medium <= 7 s (a full shot 5 s, advisory) | 05 §2.3 |
| G-INSERT | an insert is an impact of 1-3 s; a long line splits across insert + reaction | D2: the boots insert worked, but the voice held it 10.1 s |
| G-PUSH | <= 2 pushes; no amount on any camera head | H3 governed 0 of 16 amounts; D4 pushed on its own |
| G-LOCKED | >= 50 % locked off | 05 §2.6 (60 % proposed); a bare hold froze 81 %, so the actor or the air carries the verb |
| G-TWO | a two-person reaction is a locked MEDIUM two-shot | D3 |
| G-PAYOFF | a payoff shot carrying dialogue is a locked CLOSE | D5 |
| G-OTS | over-the-shoulder never tighter than medium_close | D4: 19.8 dB frame 0, 2 of 2 seeds |
| G-UNSUPPORTED | silhouette, Dutch / canted, eye close-up asked in words: refused | D1, D6, D7, D5-ECU: 0 of 4; until a panel route exists |
| G-SHOTS | <= 30 shots | the capacity model below |
| G-COLD | first line <= 10 words; a sound on shot 0 at <= 0.25 s | 04 P1 |
| G-ACT | one act_out, starting at 35-55 % of the picture, beat + coda >= 1.2 s, a bed tone change on it or the next shot, before the turn | 04 P2 |
| G-CAPTION | a narration line whose content words its frame + motion already show (> 0.80) -- except the narrator acting (the memoir's witness) | 04 P4; CAPTION_WALL was advisory |
| G-REACT | after every exchange of two speakers, a silent face (or one inner line) | 04 P5 |
| G-MA | >= 3 holds of beat + coda >= 1.2 s | 04 P6; ep01: 11 of 18 holds were 0.4-0.5 s |
| G-INNER | an inner line plays over its speaker's own face; ADVISORY note until the owner has heard it | G1 |
| G-TEASE, G-MOTIF, G-FULL | advisory | 04 P7, P8 |

The dialogue CEILING now follows the chapter for every plan (`plan_gates.dial_ceiling`):
the chapter's speech + 8 points, inside 20-35 %; the floor already did. G-MOVES under the
grammar: a locked or over-the-shoulder shot leaves the share and the twice-running rule
(the owner's 2026-09-19 complaint was orbits; a held frame is not one); 8 distinct moves
still hold. G-VARIETY's closes a person is 12 on a grammar plan (55 % faces put two leads
past 6). A grammar plan never packs two shots into one take (`episode_takes.budget_for`).

**Free cures** (`studio/plan_cures.py`, the repair round): an amount is stripped from a
head; a third push is held locked with its actor clauses; an OTS close becomes a medium
close with its head a third. Every other grammar row is the writer's.

**The writer** (`agents/skills/episode_writer.md`, "The anime-TV grammar"): every rule,
every number in the band's `grammar_rules`, the inner kind, act_out, tease, motif; the
head clause never carries an amount.

**The inner voice** (`studio/inner_voice.py`): recorded by the speaker's OWN engine with
the hushed delivery (G1: Qwen3-TTS VoiceDesign hushed was another man, ECAPA 0.23/0.67);
assemble lays it through G1's close-mic chain (highpass 110 Hz, lowpass 6.5 kHz, a 35/70
ms reflection), the hushed -5 dB being the mix's delivery offset.

## The capacity model and the shot cap

`episode_capacity`: the shares the runner already runs on (`run_budget.EPISODE_SHARES`,
priced on WotW ep25's 26 shots) split into per-shot steps (grids, panels, takes, judges,
ladders: 175 of 300 min) and fixed ones (125 min), plus a retake margin from
03_h3_workflows.md (a render ~110 s, a quarter of the takes retaken twice): 7.65 min a
shot. 23 shots project 5.0 h (Jekyll ep01's clock: 4.99 h); 28 -> 5.65 h; 30 -> 5.91 h;
31 -> 6.03 h. **The cap is 30.** Open: the shares that price the reserve do not yet scale
with the shot count (`Budget.owed_after`), so a 30-shot episode's rungs close earlier than
its firsts need -- re-price after the first grammar episode's measured clock.

## Calibration (the replay, 41 plans: WotW ep01-27, Scarlet ep01-14, Jekyll ep01)

The owner-approved set is WotW ep01-03 (liked) and Scarlet ep05 / ep07 (judged right).

- **Mechanical walls with zero fires on the approved set: hard.** G-CAPTION (8 plans; its
  one approved fire, WotW ep03 line 15 "I left the staring crowd behind me and slid down
  the hot sand", is the narrator acting and is now exempt), G-OTS (4 plans), G-TWO (7),
  G-UNSUPPORTED (3, after 'at a slant' left the list: its one hit was a table surface),
  G-SHOTS (1: WotW ep21, 32 shots, measured 9.2 h).
- **Grammar-definitional gates fire on almost every legacy plan, the approved ones
  included** (G-FACES 38 of 41, G-WIDE 38, G-PUSH 37, G-LOCKED 37, G-COLD 39, G-ACT 40,
  G-INSERT 39, G-MEDIUM 31, G-REACT 17, G-MA 12, G-PAYOFF 8). Those fires ARE the old
  grammar the owner approved replacing, not misfires, so they are hard on a grammar plan
  and stay advice on a legacy one -- the replay checked the mechanics (each fire read
  against its plan), not the rule.
- **The proof:** Jekyll ep01 re-planned under the grammar (`library/<jekyll>/episodes/
  ep01/plan_v3.py` -> `plan_v3.json`, beside the live plan) passes the whole battery
  (`plan_check.py ... --plan=plan_v3.json`: VERDICT clean) with 0 grammar faults.

## Owner calls, defaulted (for veto)

- **The title card stays at the END.** The G2 bumper (the card at 7.25 s, after the hook)
  is not adopted: the book video already puts each chapter's card first, and the Short
  keeps the owner's design (SKILL.md). The tension with "an obvious outro prompts the
  swipe" (04 §2.8) is recorded, not acted on.
- **The inner voice is advisory** until the owner has heard
  `docs/audit/2026-10-16_model_tests/voice/G1_inner_voice_AB_sequence.mp3` and a rendered
  inner line in an episode.

## Not built

- A panel route for silhouettes, Dutch angles and eye close-ups (a panel drawn without the
  room picture, or an edit of the drawn panel): until then they are refused in words.
- Assembly-side impact frames and speed lines (05 §2.5): a separate decision.
- Retention data against these gates (the publishable benchmark 04 §7 names).
