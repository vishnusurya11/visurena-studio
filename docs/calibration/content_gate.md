# The content gate, calibrated on what went public

The content gate asks a vision model to *list* what is in a picture — people,
copies, lettering, hour, landform, subjects — and judges the list in code
against the plan. It never asks the model a yes/no question.

After the 2026-09-22 audit it reads its rules from the plan and the book:

- who may be in a picture comes from the setup's crowd and the shot's
  `extras`;
- flatness is the place's `landform`;
- the banned subjects are the book's `analysis/dq_rules.json`;
- lettering is excused only on an insert or close whose subject is a printed
  thing.

## Panels, ep09 (before a single take was rendered)

19 of 23 were clean. All four failures were real:

| panel | what the gate said | what the picture is |
|---|---|---|
| 4 | 9 figures, 8 copies | a row of identical sappers along the parapet |
| 10 | 1 figure for 0 cast | the soldier with the flag, undeclared in the plan |
| 18 | 6 figures for 0 cast | the hussars, undeclared in the plan |
| 21 | 4 figures | three identical women beside a cart the plan seats two in |

Panels 10 and 18 were plan faults, and the plan now declares the people.
Panels 4 and 21 are picture faults, and they are redrawn.

## Takes, ep08 (published 2026-09-22)

16 of 20 were clean.

| take | verdict | truth |
|---|---|---|
| T07 | **4 figures, 4 copies of another** | **the four identical shopmen that went public at 100/100 on the take gate** — caught |
| T06 | clean | the newspaper headline reads "NEWSPAPER BOY", a cast label printed into the picture — **missed, and it is meant to be missed here**: an insert on a newspaper is allowed lettering, so this is OCR's job (audit Tier 4, item 30) |
| T10–T12 | text or lettering | a framed railway map with a printed legend, a framed notice, newspapers on the seats — real lettering, small and incidental |

T10–T12 are counted as true positives. The owner's rule is no lettering in
the picture, and AI lettering is gibberish on a close look however small it
is. The cure is upstream: name the frames on a carriage wall as unlettered
things (engravings of a landscape, a mirror), rather than leaving the model to
invent notices.

## What the gate cannot do

- It cannot tell a real headline from a leaked cast label. That needs OCR.
- It counts copies only when the reader notices them. On ep09 panel 21 it
  counted the three identical women as 4 figures and 0 copies, and the head
  count caught them instead. Face-embedding similarity (Tier 4, item 29) is
  the check that does not depend on the reader noticing.

## Stacked panels, scored by thirds (2026-09-24)

`panel_dq.stacked` used to score a gutter over the full width of a row: a
figure standing across the gutter broke both its share and its evenness, and
a stacked panel with a man in the middle could pass. It now scores each line
as the second-best of its three thirds, each third judged on its own share
and its own paleness and evenness (`_by_thirds`).

Re-measured over the 173 published panels on disk (ep05-ep09):

| set | panels | thirds score |
|---|---|---|
| stacked positives (ep07 S12, S13, S14) | 3 | 1.000, 1.000, 1.000 |
| clean | 170 | at most 0.023 (ep09 S03, S07) |

The wall `STACKED = 0.90` stands; the margin is the widest of any row in the
picture eye. Test: `tests/test_a_gutter_that_stops_at_a_figure_is_still_a_gutter.py`
(a synthetic two-picture panel with a dark figure across the middle third of
the gutter scores over the wall; a plain picture under 0.5).
