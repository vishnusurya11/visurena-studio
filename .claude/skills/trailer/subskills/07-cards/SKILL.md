---
name: trailer-cards
description: Title and quotation cards - typography, timing, and the three silent failures.
---

# Text cards

`studio/trailer_assemble.py` (`ass_title`, `wrap_title`, `card_fits`). ONE thing
in the PIPELINE puts text on screen: `title_card_ass` (`:807`), one `ass` filter
at `:817` — so every rule below is the end title. TWO things in the MODULE can.
`title_card` (`:206`) still draws it with `drawtext` 600 lines earlier, under the
plainer name, no caller and no test, contradicting every row of the Typography
table at once: `fontcolor=white` not `&H00DAE6ED`, `height // 14` not `// 13`,
`line_spacing=12` and no Spacing, no fade, and `font=None` so fontconfig picks
the face — the silent substitution `:783` raises to prevent. **Delete a
superseded twin the day it is superseded**: dead and live are identical at the
grep, the plainer name wins, and that reversion is the whole table read backwards
with every card test still green.

## Three bugs that shipped, all silent

**1. The fade never fired.** `f"{{\fad(...)}}"` — `\f` is a Python escape, FORM
FEED. libass discards an unrecognised override block in silence, and the control
character even split the Dialogue line: every card hard-cut in at full white. So
does most of the vocabulary — `\fad \fsp \t \bord \alpha` are all control
characters. **Every ASS string is a raw string.** The test asserted
`"\fad("` in a non-raw string too, so it searched for the same form feed and
passed against a card that never faded — **a test written with the same bug as
the code cannot catch it.** No `0x20` or `isprintable` check exists in the module
or its tests. But one such assertion does NOT close the class, because it must
whitelist the character that still breaks it. `\N` is already loud — a bare
`"\N"` is a Python `SyntaxError: malformed \N character escape` (VERIFIED) — so
what survives is the lowercase typo, `"\n".join` for `r"\N".join` (`:787`): 0x0A
is exactly the codepoint the guard must permit, and it ENDS the Dialogue line
mid-title, so the rest of the wrap is text no `Dialogue:` event covers and the
card renders its FIRST LINE ONLY. Less ink, bigger margin, passed by the gate
that fails toward PASS (below). Format arithmetic, not a decoded frame. So the
guard is TWO assertions and the second is positional: nothing under 0x20 outside
the format's own breaks, AND exactly one line begins `Dialogue:`, it is the LAST,
and it carries every string `wrap_title` returned. **A character-class guard
cannot police the character it is obliged to permit — count it and place it.** A
card can fail by being too NARROW, so `card_fits` needs a floor too.

**2. The Jekyll title shipped clipped off both edges** — "GE CASE OF DR. JEKYLL
AND", the film's own name unreadable in a delivered file. `WrapStyle: 2` disables
libass wrapping, so a long title has no way to fail except by running off, and
nothing measured the card after rendering it. `card_fits()` refuses above 90% of
frame width or under an 8px margin; the old render measures 1323px of 1344,
margin 3px, and fails — but those 1323px are the 25 characters still INSIDE the
frame, not the title's 43: a clipped bbox is clamped by what clipped it and
yields no character ceiling. The gate can only refuse: its knobs are UNREACHABLE —
`title_card_ass` (`:807`) takes no `per_line` and no `tracking`, calls `ass_title` (`:812`) on both defaults, which
calls `wrap_title(title)` (`:787`) on its own, so `assemble.py:167` has no
argument to pass instead. **A default on a function the caller never calls
directly is not a knob, it is a constant.** Six values in, four forwarded: `:816`
spends `fps` on the lavfi rate and `:818` calls `frames_arg(seconds)` WITHOUT it,
so the card's length quantises on that default 24 while it renders at `fps` —
`extract` (`:197`) passes `frames_arg(seconds, fps)` and is the proof it was
meant to; latent only while `TrailerPlan.fps` stays 24 (`trailer_spec.py:249`).
**A wrapper that narrows its own signature is where knobs and measurements die**
— threading knobs DOWN never reaches one already held and dropped, so assert the
forward too. Thread all three through `title_card_ass`, then narrow
`per_line`, re-render, re-measure, and refuse only what survives the narrowest
wrap. Then MOVE it: every input is in `plan.json` before a pixel exists
(`assemble.py:101` width/height/fps, `:167` `plan["title"]`) — the gate grades a
`color=c=black` lavfi card and one PNG decode (`:816`, `:851`): no model, no
GPU, no credit, the same verdict at step 06 as at step 08. MEASURED in this
book's ledger, step 06 spends 0.4s across 22 rows and step 07 spends 19,324s
across 50; the gate fires after that as `SystemExit`, so the run does not
degrade — it ends. **A gate whose every input is settled before the spend must
fire before the spend**; run last it is not a gate but an autopsy.

The threshold agrees with the layout at ONE width and nowhere else. `TITLE_SAFE`
0.90 × 1344 = 1209.6px against the Style's own box in the same function,
1344 − (60+13) − 60 = **1211px** — 1.4px apart, so on the one canvas ever run the
only ink that can trip the gate has already overflowed the margins libass was
handed. But the gate is a FRACTION of the frame and the box is the frame less 133
LITERAL px, and 0.90W = W − 133 only at W = **1330** — 1330 % 32 = 18 while
`CANVAS_MULTIPLE` is 32, so no legal canvas is EVER 1330 wide and the two can
never agree again. Below 1330 the gate is LOOSER by 133 − 0.10W: 56px of
overspill passes at 768 wide, 98px at 352. Above it the gate is TIGHTER and
refuses the very wrap this file prescribes below — a line filled to the derived
`per_line` measures 1773.8px at 1920x544 against a 1728.0px gate and 1877.1px at
2016x512 against 1814.4px, both fixed points named below. So a constant from
outside the layout is not enough: the dependency must point ONE way, gate first
and layout derived — `per_line = (TITLE_SAFE * width) // advance`, `MarginL/R =
(1 − TITLE_SAFE)/2 × width` rather than a literal 60, and the disagreement is
zero on every canvas by construction. **Two constants on one edge, one a fraction
and one a pixel, agree at exactly one width — and the canvas is the free variable
that finds it.** 344 learnings rows, twelve gate names, not one a card fit.
Nor would such a note be kept — `:175` prints it to stdout and that
file imports no `Learning`, though its caller does (`step_08_assemble.py:30`,
`ctx.learn` at `:87`); the ledger holds no step 08 row at all. **A printed
measurement is one the next run cannot inherit.**

Its probe instant is a coincidence too: `card_fits` samples at `at=0.5` (`:849`)
while `ass_title` fades in over `fade_ms=500` (`:768`) — neither threaded through
`title_card_ass`. `ink_bounds` thresholds at an absolute 40 (`:833`), not a
fraction of the card's own peak, so under partial alpha the antialiased edge drops
out: ink SHRINKS, margin GROWS, and **this gate alone fails toward PASS**; deeper
in, `:844` raises `no visible text at all` — a crash out of the one function whose
job is to refuse, unhandled at `assemble.py:172`. Probe the mid-hold, `seconds /
2` = 3.35s of the 6.7s card.

**3. A card is chosen, word-capped, ranked, de-duplicated — and rendered by
nothing.** `SlateLine.card` is `speaker is None` (`trailer_stage_spec.py:147`)
and it is step 05's TERMINAL ladder rung (`step_05_voice.py:30`): a line whose
speaker has no cast card, or whose voice climb exhausts, returns `card_line()`
with `rel_path=None`; `step_06_plan.windows` gives it no window (`:247`),
`line_windows` no audio (`:522`). MEASURED, Scarlet: voice.json index 3 is
`card: true, rel_path: null`, plan.json `lines` is `[0,1,2,4]`, four
`speaker_card` rows `terminal: true`. "No dialogues" is partly arithmetic:
`speech_refusal` counts `l.speaker`, so that line passed step 04's speech gate
and step 05 deleted it after. **A terminal rung must name the artifact it
writes.** Until a renderer exists `card` is a deletion, not a degrade, and
`CARD_WORDS` (8), `no_second_card` and `thesis_card` are rules for a screen
nothing draws on; keep the doctrine for whoever builds it — 0-2 cards beyond the
title, quotation only, the author's own sentence, never a claim.

## Typography

| | value |
|---|---|
| face | Bookman Old Style — genuinely Victorian (ATF 1901), low enough stroke contrast to survive H.264 |
| tracking | Spacing 13px = **0.220 em** at fontsize 59, not the 0.37 first used — all-caps convention is ~0.1em, film titles 0.2-0.3; literal px over derived size, so the em is a per-canvas ratio |
| colour | warm off-white `&H00DAE6ED`, not `#FFFFFF` |
| centring | `MarginL = MarginR + tracking` — libass counts the final glyph's trailing letter-space, so a centred tracked line sits tracking/2 left |

Fontsize is the ONLY metric derived from the frame (`height // 13`, `:799`); the
rest is literal px, and `:792-793` writes `PlayResX/Y` as the OUTPUT size, not
the design frame ASS scales from. 59 and 0.220 em are the only values ever
rendered — but `check_canvas` (`trailer_spec.py:263`) is not what holds them: `plan_from_spans`
(`step_06_plan.py:563`) builds `TrailerPlan` with no `width` and no `height`, so
1344x768 is a pydantic DEFAULT. MEASURED against `adapt_canvas`, 1920x544 and
2016x512 are fixed points too — the area cap moves HEIGHT on the ultra-wides —
so "every landscape canvas is 768 tall" is false and the fixed-point set is
INFINITE — the cap trades height for width without limit, down to a legal 32-tall
canvas where `height // 13` is **2**, so any COUNT of legal canvases is an
artefact of where the enumeration stopped. **The constant is held by a default,
not by the check.**

Nor does 22 bound the width even at 1344x768: it counts CHARACTERS on a
proportional face. MEASURED in Bookman at 59 with Spacing 13, the corpus's
widest wrapped line, `MOBY DICK OR THE WHALE`, is 1125px against the 1209.6px
gate — 85px of slack — while 22 M's measure 1461px and refuse. `56px INSIDE
TITLE_SAFE` graded the portrait BOX, not its ink: at 768x1344 the ink refuses 28
of 30 corpus titles, 25 of 30 at 768x768, 13 of 30 at 1024x768. Bookman's mean
cap advance is 0.713 em over A-Z, so derive it: `per_line = (width - MarginL -
MarginR) // (0.713 * fontsize + tracking)` — 21 at 1344x768, 7 at 768x1344. An
AVERAGE narrows the wrap, it does not replace the frame. **The quantity that
scales is derived from the axis nothing moves; the quantity that must scale is a
literal on the axis left free.**

libass substitutes a missing face **without warning**, and the check sits at the
wrong layer: `ass_title` asserts `TITLE_FONT_FILE.exists()` while `title_card_ass`
passes libass only the NAME, so the assert says nothing about which face rendered.
Check a pixel failure in PIXELS: `ink_bounds` already decodes the probe frame, and
one fixed probe string's ink width identifies the face. And `TITLE_FONT_FILE` is a
hard-coded Windows system-font path (`:726`), so every non-Windows agent raises
`title font missing` before drawing a pixel — against "any agent, any model".

Never end a wrapped line on an honorific — "DR" / "JEKYLL" reads as a typo.
`dangling` (`:747`) does not do that: its two overflow branches (`:748-750`,
`:751-753`) are byte-identical, so the flag is computed and discarded. The rule
lives only in the post-loop fixup (`:759-763`), which pulls a trailing "MR."
down and never re-checks `per_line` — one of TWO paths past the cap; MEASURED,
it returns a 23-character middle line for `Case of Mr. Bartholomew Quintus Rex`.
The other is the break itself: both guards (`:748`, `:751`) require a NON-EMPTY
`current`, so the first word of a line is appended unconditionally and a word
longer than the cap is never split — `wrap_title("Antidisestablishmentarianism")`
returns one 28-character line. **A cap
enforced only when there is already something to break is not a cap, it is a
preference for where to break** — apply it to the token too, and re-wrap after
the fixup; a flag with identical branches is a comment pretending to be logic. 0
of 30 corpus titles hold a word over 22, but 15 of 30 hold one over 7, so a
derived cap makes this the ordinary path.

`card_fits`, `ink_bounds` and `wrap_title` have NO test; the four at
`tests/test_trailer_edit.py:158` assert on the ASS STRING and none decodes a
frame. Nothing has measured the table above either: of BUILD's 65 rows only 35
touches the card, and it is TIMING (below), not typography — the vocabulary has
no second hit in BUILD or the ledger. Face, em, off-white and centring are
TASTE: defensible, unmeasured. **Say which are measured and which are taste, or the next
agent defends a preference as a finding.** The centring row is one line from
measurable: `ink_bounds` returns BOTH edges, `card_fits` keeps only `min(x0,
width - x1)` (`:856`), and a centring error is ANTISYMMETRIC, so `abs(x0 -
(width - x1))` — the only number that names it — is discarded. **A gate that
reduces two measurements to their minimum cannot test the claim that made them
differ.**

## Timing

The card does the OPPOSITE of "cut in on a hit": the bed stops dead on the last
cut, the card FADES up on room tone (`\fad(500,800)`), the hit lands
`PRE_TITLE_SILENCE` 2.2s later, and it holds `FINAL_HOLD` 4.5s past that
(`trailer_cut.py:48`, BUILD row 35). Run 10 faded the cue instead and struck the
card at -46 LUFS.
