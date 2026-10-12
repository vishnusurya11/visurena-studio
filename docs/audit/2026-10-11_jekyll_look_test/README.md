# Jekyll and Hyde: style look test (2026-10-11)

Book: `library/20260827135504_the-strange-case-of-dr-jekyll-and-mr-hyde`. Local ComfyUI, $0.
The sheet: `style_sheet.jpg` (rows are styles, columns are subjects). Cells: `A/`, `B/`, `C/`.

**Subjects.** Jekyll, Hyde and Utterson use the heads that `fc1543a` wrote to `analysis/heads.json`
(Jekyll: iron-grey, clean-shaven, silk top hat; Hyde: small, pale, black hair and side-whiskers, low
felt hat; Utterson: lean, dust-fair, clean-shaven, bowler). Each figure stands alone, full figure, on a
foggy gaslit street. The door is the ch1 passage: a two-storey gable with no window, a blistered door
with no bell or knocker. Every subject has one seed (`crc32("jekyll_look/<subject>")`) shared by all
three styles. The prompts are in `cast.json` and `street.json`, and the leads are in `render.py`.

| Style | Recipe | Output | Time per picture (warm; cold first load) |
|---|---|---|---|
| A. Photoreal gothic | `image_krea2_turbo_t2i`, no LoRA, 2 MP, refine off. Lead = the book's own refs words (refs.json palette line) plus "fog, gaslight, deep shadow" | 1448² | **15 s** (20 s) |
| B. WotW painterly | `image_krea2_cinematic_2x_neutraltile_visurena` with STYLE_LEAD, 1024² base and the 2x tile pass | 2048² | **40 s** (45 s) |
| C. Dark ink gothic | `image_krea2_turbo_t2i`, `enable_lora: true` (krea2_darkbrush 0.8), lead "etched pen-and-ink ... penny-dreadful engraving" | 1448² | **15 s** (20 s) |

All 12 cells took 4.8 min of GPU (`times.jsonl`).

## Faults read off the sheet

- **A.** The three men are clearly distinct: grey and fifty in a top hat, young with black hair in a felt hat, and lean in a bowler. Hyde reads as a young man rather than a sinister one: his side-whiskers are absent, the "displeasing smile" did not render, and nothing shows his small stature. Utterson's hair came out grey, not dust-fair. The door's gable has windows, though the text says it has none. There is no lettering and no duplicate figure.
- **B.** **Hyde renders as a chibi caricature** (huge head, anime eyes), which breaks the horror tone. "Dwarfish" read as a body-proportion cue. Jekyll and Utterson are fine and distinct. The door has windows, and the road has modern yellow kerb lines. There is no lettering.
- **C.** **Lettering in all 4 cells**: an artist's signature scrawl in a bottom corner. **There is a ghost figure** in the fog left of Utterson, and a small ghost shape left of Hyde. **Jekyll lost his age**: he has dark hair and looks about forty. Because of that, **Jekyll and Utterson look alike** (same long dark hair, same build). Hyde wears a top hat instead of a felt hat. The door has windows. The white paper ground makes these night scenes read as day.

## Recommendation: A, photoreal gothic

A best serves a gothic horror book. Horror here lives in the light (fog, gaslight, chiaroscuro), and A delivers it without stylisation fighting the tone. It keeps the cast apart, including the Jekyll/Hyde contrast the story turns on. It is the cheapest (15 s), and it is already the book's declared look: `refs.json` was written photoreal, so A follows "book look, not house look". B's angular CGI turned the most important character into a cartoon. C is the most atmospheric single frame, but it fails on lettering, ghosts and identity: it collapsed Jekyll's age, and with it the Jekyll/Utterson distinction. Every one of those faults would reach H3 through the refs.

To fix in A before refs: make Hyde's "wrongness" explicit (a stooped, coiled posture, a sneer, visible side-whiskers, standing a head shorter beside a scale cue). Word the windowless gable as a layout ("the upper storey a flat blank wall") rather than as an absence.
