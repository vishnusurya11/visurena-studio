# Grid prompt v1 vs v2: same-seed A/B on ep09 (2026-09-22)

Audit 2026-09-22, Tier 3 items 16 and 19. Qwen-Image-2.1 edit-multi, 25 steps,
CFG 1.0, the same seed per grid (40500 + sum of shot indices), the same staged
references. Grids are filed under
`library/20260827135508_the-war-of-the-worlds/episodes/ep09/storyboard/grids/`
as `ep09_grid_<setup>_<shape>_ab_<version>.{png,txt,json}`.

| grid | shots | v1 words | v2 words | v1 | v2 |
|---|---|---|---|---|---|
| garden 1x1 | 12 (medium, narrator + wife at tea) | 822 | 394 | **both leads cloned**: two narrators and two wives standing, nobody at tea | one of each, seated at the tea table (v2b: shawl and notebook present) |
| bridge 1x1 | 6 (medium, 1 declared extra) | 383 | 250 | the sentry, small, no rifle | the sentry, closer, with his rifle; about even |
| lawn 2x2 | 13, 14, 16, 17 | 1376 | 872 | **panel 2 (insert of the falling tower) is a copy of panel 1's wide** | panel 2 is its own picture of the burning church |

Versions of v2, same seeds:

- **v2**: bound by name only. The wife lost her rust shawl in both panels.
- **v2b**: the binding line carries each "Wearing:" sentence cut at its first
  colon or comma. The shawl was back, but her skirt had been cut away, and its
  sage-green moved onto her blouse (lawn panel 3).
- **v2c**: each garment is split on commas, after a colon cut, at most five.
  The clothes are right in all panels: cream blouse, sage skirt, shawl, and the
  boater with its band.

**Decision: v2 is the default.** v1 stays callable (`--prompt=v1`) so that an
old grid can be reproduced.

**Open in v2c:** lawn panel 4 (shot 17, planned medium close) came back as a
full figure, and no gate refuses it (below). The grid prompts are
still over the audit's budgets (1x1 at most 150 words, 2x2 at most 350). What
remains is the plan's own frame prose, which the prompt carries whole rather
than cutting.

CFG 1.0 means the NEGATIVE is never computed (audit item 18). v2 states its one
real negative, no lettering, affirmatively in the layout line.

## Does a gate catch lawn panel 4? No, and face height cannot

`panel_check.judge` on the v2c crops: shot 17 (medium close, full figure)
has a face 0.112 of the frame and **no flag**. Published medium-close panels
(ep05-ep09, with faces) run 0.101-0.3, median 0.204, and the owner accepted
ep06 shot 5 at 0.109 and ep07 shot 15 at 0.116. A face-height floor would
either pass 0.112 or accuse published work, so none is added. The instrument
this needs is a FRAMING answer from the panel content VLM, from a closed
vocabulary (head and shoulders / to the waist / full figure) judged against
the planned size in code. It is queued with the Tier 4 checks.

## Correction (2026-09-23): the A/B dressed the cast from chapter 6

`grids.py` read `character_row(book, name, 6)`: every ep09 grid, A/B
included, was bound to the chapter-6 wardrobe. The "clothes right" verdict on
v2c (shawl, cream blouse, sage skirt) was judged against the wrong chapter;
chapter 9 dresses the wife in a sage walking costume and a dust coat, and the
milkman, Snippy, the hussar and the landlord got no garments at all. The
structural result stands -- v1 cloned both leads and copied the insert, v2
did neither, at the same seeds -- but the garment-binding result is unproven
until re-measured on the right rows. The grid now reads the same chapter-
stamped refs.json row as the take. Found by the grid-stage audit agent.
