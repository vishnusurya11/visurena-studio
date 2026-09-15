# THE gpt-image-2.5 SHEET PROMPT — rewritten template, two worked sheets, code changes, cost

Proposal only. Nothing in the repo was edited, nothing was rendered, nothing was spent, the GPU was not touched.

Evidence read for this report, all absolute:

- Builder: `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\studio\episode_seq_board.py`
- Runner: `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\scripts\episode\seq_boards.py`
- Draw + cut: `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\scripts\episode\storyboard.py`, `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\studio\episode_board.py`
- Gates: `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\studio\route_gate.py`, `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\studio\frame_match.py`
- Contract: `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\studio\episode_spec.py`
- All six sheet prompts and all six sheets in
  `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\library\20260822113400_a-study-in-scarlet\episodes\ep01\frames\`
  (`seq_criterion_0`, `seq_cab_0`, `seq_gateway_0`, `seq_corridor_0`, `seq_lab_0`, `seq_bench_0`, each `.png` + `.prompt.txt`),
  the 40 start cells `Q00_0 … Q22_0` and the five END cells `Q02_0E Q03_0E Q07_0E Q08_0E Q12_0E`, read as pictures.
- Plan: `…\episodes\ep01\plan.json` (cab and criterion setups dumped in full)
- Predecessors: `scratchpad\review9\brief.md`, `scratchpad\review8\end_frames.md`, `scratchpad\review7\storyboards.md`

---

## 0. WHAT THE PICTURES ACTUALLY SHOW (both faults, plus three the owner has not named yet)

**Fault 1 — an END panel is its own start panel.** On `seq_criterion_0.png`, panel 1 and panel 6 are the same
photograph: Watson at the left in three-quarter profile, head bowed to his own glass, the bowler hanging by the
knob of the stick; Stamford at the right with the glass at chest height; the gilt mirror behind. Measured 0.951.
The same on `seq_gateway_0.png`: panel 1 / panel 8 (Q07_0 / Q07_0E, 0.890) differ only by a hair of framing, and
panel 2 / panel 9 (Q08_0 / Q08_0E, 0.821) both have Watson on the steps **with the bowler still on his head**
although Q08_0E's own text says the hat has come off. On `seq_lab_0.png`, panel 1 and panel 9 (Q12_0 / Q12_0E)
are both the tall figure at the far window with the arm already raised.

The cause is one sentence written by `end_panels()` in `episode_seq_board.py`:

```
Panel 6: the last frame of panel 1, identical place, light and framing: Static shot; Stamford lifts his glass;
his eyes go to Watson's face and stay there a beat too long; Watson looks down at his own glass has just finished.
```

It gives the model (a) the word **identical**, (b) the word **Static**, (c) a *verb phrase* and no *picture*. A
text-to-image model can only draw nouns in positions. Told "identical … <verb> has just finished", it draws the
identical picture. Reinforced by the sheet-level sentence `end_order()` writes: "each **repeats** an earlier
panel's place, light and framing **exactly**". The one END cell that is not a copy, Q03_0E (0.339), is not a copy
because the drawer changed the *location* instead of the subject — it is drawn at a gated hospital courtyard,
not on the Piccadilly street of its own start panel — which is the only degree of freedom the sentence left open.

**Fault 2 — the cab panels contradict each other physically.** Read `Q03_0.png` and `Q03_1.png` as pictures:

- `Q03_0` is a lateral wide. Horse at the right leading, body at the left, driver up behind on the near-left,
  travel left → right, camera on the pavement across the street. That much reads.
- `Q03_1` is a low insert in which **one tall spoked wheel occupies the left third and the horse's body, chest,
  foreleg and hind leg occupy the right third, at the same station, with a receding wet street between them.**
  On a hansom the single axle is under the middle of the passenger box and the horse stands in the shafts a good
  two body-lengths ahead; the horse can never be abreast of the wheel with a strip of road between. There is also
  a second spoked wheel visible behind the first, so the drawn vehicle is a four-wheeler.
- The two panels are not even on the same axis. `Q03_0` is a lateral pass across the frame; `Q03_1` recedes down
  the street away from the camera. Cut together they are a 90° mismatch, which is the "direction of travel does
  not match" the owner saw.
- `Q03_0E` is a third vehicle-and-place again: the gated courtyard, cab dead centre, going nowhere.

The cause: `setup.described` states the hansom's parts ("two tall spoked wheels … the cabman on his high seat up
behind the hood") but never states *where the parts are relative to each other*, and the panel text for the insert
says "the horse's hind legs **ahead of** the wheel". "Ahead of" is exactly the relation image models are
documented to fail on (§3). Nothing in the prompt fixes which side of the street the camera stands on, so the
model is free to re-pick the axis panel by panel.

**Three more, found while looking, that the rewrite must also close:**

3. **The sheet is not in story order.** `split()` sorts "geography" panels first. On `seq_criterion_0`, panel 1
   is shot **2** and panel 2 is shot **0** — the sheet opens with the middle of the scene. And because only one
   criterion cell qualifies as geography, the sheet carries the sentence "Panel 1 is ONE strip of the same walk in
   order of distance travelled … the mirror grows from panel to panel", about a single panel. Two contradictory
   ordering instructions on one sheet. The research (§3) is unanimous that the model reads a panel list as a
   narrative sequence of beats; scrambling the order fights the one thing it is good at.
4. **The ladder sentence fires on the wrong panels.** `geo_panel()` decides a panel looks down the route by
   testing whether the frame text contains the substring `behind` / `shoulder` / `away`. Q02_0's text contains
   "the gilt mirror **behind** them", so a two-shot at a bar counter was told "The great gilt-framed mirror behind
   the counter is the height of a finger."
5. **The vehicle changes identity between setups.** The cab in `Q03_0` is an open-bodied two-wheeler; the cab in
   `Q07_0` / `Q07_0E` on the gateway sheet is a closed box on two wheels; `Q03_0E`'s is a third. Nothing binds
   them — `plate_cab.png` is attached to the cab sheet only, and it is itself a two-panel composite with no horse.
   The gateway sheet also drew **no stone arch and no iron gates** at all, although its `described` names both.
6. **Crowd life is thin or absent exactly where the owner wants it.** The cab wide and the cab END have good
   background figures (pavement walkers, three men under the gate) — those are the ones the owner liked. But the
   criterion two-shot and its END show a nearly empty bar although the location text says "drinkers two deep at
   the near end"; the whole corridor sheet, set in a working London teaching hospital, contains **not one other
   human being** in six panels. A location-level crowd clause gets averaged away across nine panels. Crowd has to
   be per panel, with a number and an activity.

---

## 1. THE REWRITTEN SHEET-PROMPT TEMPLATE

### 1.1 Shape

The prompt stops being one 5–7 kB paragraph and becomes **short labelled blocks separated by newlines**. Both
OpenAI guides say this explicitly for complex requests (§3). Order of blocks follows the guides'
scene → subject → details → constraints, with the two new blocks (DIFFERENT PICTURES, GEOMETRY) hoisted above the
panel list because they are sheet-wide laws, not panel details.

```
SHEET
DIFFERENT PICTURES
ORDER
REFERENCES
LOCATION
GEOMETRY
WARDROBE
BACKGROUND LIFE
PANELS
  Panel 1 …
  Panel 2 …
STYLE
CONSTRAINTS
```

### 1.2 The template, every sentence, and why it is there

---

**`SHEET`**

> A film storyboard sheet: a {cols} by {rows} grid of {n} equal vertical 9:16 panels filling the whole canvas,
> thin white gutters between them and no other border.
> Panels read left to right, top to bottom: panel 1 is top-left, panel {cols} is top-right, panel {n} is
> bottom-right.

*Why.* Unchanged from today and it works — `cell_boxes()` finds the drawn gutters on all six sheets on disk and
`gutters_ok` is true in every `seq_*.dq.json`. Do not touch what is measuring clean. The reading-order sentence is
what makes "Panel k" addressable at all.

---

**`DIFFERENT PICTURES`** — new, and the top-priority sentence on the sheet.

> Every panel on this sheet is a DIFFERENT photograph. No two panels may share camera position, subject size and
> background at the same time. Laid side by side, a viewer must be able to say in one word how each panel differs
> from every other panel. Never draw the same picture twice on this sheet, and never draw a panel that a viewer
> would mistake for another panel at a glance.

*Why.* The owner's rule, stated unconditionally and at the top, in the model's own idiom (a *rule about the set*,
not about one panel). Today this sentence exists only as `"STRICT: every panel is a DIFFERENT picture; no two
panels share a framing."` prepended on the **second** attempt in `draw_setup()`, and only when the sheet has no
geography cells — so it never fired on any of the six sheets on disk, because `duplicates()` compares only cells
from *different shots* and an END cell that copies its own start has the same shot index and was never compared.
The instruction must be unconditional; the gate that enforces it must compare every pair (§4.2).
"At a glance" is deliberate: it matches the human contact-sheet check and the 0.60 machine threshold.

---

**`ORDER`** — replaces `geo_order()` + `close_order()` + `end_order()`.

> The panels are in story order: panel 1 happens first, panel {n} happens last, and the camera never goes back to
> an earlier moment.
> *(only when the setup has a route and at least two panels look along it)*
> The people travel {setup.route}. Panels {i}, {j}, {k} look along that path, and each of them is farther along it
> than the one before, so {setup.landmark} is larger in each of them than in the one before. No panel shows the
> far end of the route before the panel that names it.

*Why.* One ordering law instead of two contradictory ones. Story order is already route order: `route_ok()` in
`episode_seq_board.py` guarantees a setup's `path` values never go backwards through shots and sub-shots, so the
geography-first sort buys nothing and costs the narrative reading the model is best at. The ladder keeps working
because it is now stated as an explicit list of panel numbers, computed from `size in GEO_SIZES and path is not
None and route_view`, not from a substring search for the word "behind" — which is what put a distance ladder on a
bar counter.

---

**`REFERENCES`** — `describe_refs()`, extended.

> Image 1 is the empty location: every panel is set in this exact place, with its architecture, furniture,
> windows and light.
> Image 2 is John Watson: {physical}. Keep exactly this face, hair, build and these clothes in every panel that
> shows John Watson.
> … (one line per cast member)
> *(new, when the setup names a prop vehicle)*
> Image {k} is the cab: this exact vehicle — the same body, hood, wheels, side-lamp, harness and bay horse — in
> every panel of every sheet that shows a cab. It is the same cab all afternoon.

*Why.* "Assign explicit roles to references, label them by index and description" is the one thing every source
agrees on (§3), and the current code already does it for plate and cast. The new line is the fix for fault 5: the
cab is currently bound by *words* on the cab sheet and by nothing at all on the gateway sheet, and three different
vehicles were drawn. gpt-image-2.5 accepts up to 16 reference images; we use 3–5. There is room.
`previous` (the last sheet of the same setup) stays **off**, per reviewer 3 item 7 — it copied framings.

---

**`LOCATION`** — `setup.described`, unchanged in role, but the vehicle/architecture clauses move out of it into
GEOMETRY.

---

**`GEOMETRY`** — new. The block that fixes the cab.

Three sentence kinds, all of them re-expressing a relation as *a position in the frame at an apparent size*,
because that is the form the model obeys and "ahead of / behind / in front of" is the form it does not (§3).

**(a) The machine.** State the parts as an ordered chain along one axis, with distances in units of the object
itself:

> This vehicle is a hansom cab and it is built like this: ONE pair of tall spoked wheels, one wheel on each side,
> their axle passing under the middle of the passenger box. The bay horse stands in the shafts AHEAD of the box:
> the horse's hind hooves are two horse-lengths clear of the wheel, never level with it, and between the wheel and
> the horse there is only the black underside of the two shafts. The driver sits high at the BACK of the roof,
> behind and above the passengers, and the reins run forward over the roof to the horse. The passengers sit facing
> forward, toward the horse, with the folding hood closing behind and above their heads and the small
> rain-streaked front glass and the leather apron ahead of their knees.

**(b) The camera line.** One sentence that fixes the 180° line for the whole sheet, stated as which frame edge
each object lives at:

> In every exterior panel on this sheet the camera stands on the pavement on the near side of the street and never
> crosses it. The cab travels from the LEFT edge of frame toward the RIGHT edge, horse leading. Therefore in every
> panel the horse is to the RIGHT of the wheels and the driver is to the LEFT of them, and all water thrown by the
> wheels flies backward, to the left.

**(c) The architecture.** Same discipline for buildings — count the openings and put them at named edges:

> The gateway is one round stone arch with its iron gates standing open, set in a soot-dark brick wall; through
> the arch and beyond it, worn stone steps rise to one small side-door. The arch is the only opening in the wall
> in frame. The steps are behind the arch, never beside it.

*Why.* `plate_cab.png` and `setup.described` list the hansom's parts and the model assembled them wrongly, twice,
in three different arrangements. The literature (§3) is specific: relational prepositions and
viewpoint-dependent distance are the documented weak spot, while framing, relative scale and directional cues
("subject centred with negative space at the left", "logo top-right") are what these models reliably honour. So
every geometric fact gets rewritten as *which edge, at what apparent size, with what between*. The camera-line
sentence is the cheapest single fix on this page: it makes a direction mismatch between two panels impossible to
draw without violating an explicit left/right statement.

---

**`WARDROBE`** — new standalone block, the contract in the brief, promoted out of the per-image sentences.

> These do not change in any panel of this sheet.
> WATSON: fawn-brown tweed overcoat, white cravat with a stud. His RIGHT hand is bare and sunburnt and is closed
> on the silver ball knob of the black walking stick; in this sheet's framings that hand is on the {side} of
> frame. He wears NO gloves in any panel. Outdoors the brown bowler is ON HIS HEAD; indoors it is OUT of his hair
> and held flat against his chest in his other hand.
> STAMFORD: black frock coat over a grey waistcoat, white shirt, dark cravat; round clean-shaven face, dark hair
> parted at the side. Outdoors the black bowler is on his head; indoors it is in his hand.
> HOLMES: bareheaded, bottle-green velvet jacket over a white shirt with the cuffs turned back and a checked
> muffler; a small white plaster on his RIGHT forefinger, visible in any panel that shows that hand.

*Why.* Three reasons. (1) A wardrobe rule buried inside "Image 2 is John Watson: …" is read as a description of
the reference image, not as a law over the sheet; the guides recommend a separate preservation list and
"repeating the preserve list to reduce drift" (§3). (2) The hat rule is a *conditional* ("on his head outdoors and
in his left hand indoors") and the model half-obeyed it: Q08_0E kept the bowler on although its own text said the
hat had come off. Splitting it into two flat statements removes the conditional. (3) Frame-side vs anatomical
side: the repo has drifted between "the hand on the right of frame" and "his bare sunburnt right hand", and both
appear in the same prompt on disk. The block now states the anatomical fact once (it is his right hand) and the
per-sheet frame side once, and the per-panel writer inherits both instead of re-deciding.

---

**`BACKGROUND LIFE`** — new. The owner's "background folks … having people regular work sells that thing".

> Sheet-level: This is a public place in a working city and it is never empty. The people behind the action are
> different people in different postures in every panel; they are never the same group copied from panel to panel.
> They are busy with their own business and none of them looks at the camera or at the two men in front.

and then, **in every panel that is not an insert**, one clause of the panel's own:

> Behind them, {count} {who}, {what they are doing}, out of focus.
> — criterion: "eight or nine men in top hats and bowlers standing two deep at the counter, a white-aproned
>   barman drawing a cork, a waiter crossing left to right with a tray"
> — street: "four pedestrians under umbrellas on the far pavement, a boy with a broom at the crossing, a second
>   cab waiting at the kerb beyond"
> — corridor: "a porter in a leather apron carrying a covered tray away down the corridor, two students in black
>   coats standing at a doorway"
> — laboratory: "one student in shirtsleeves at a far bench with his back turned, working"

*Why.* The evidence is that a location-level crowd sentence does not survive nine panels: `seq_criterion_0`'s
`described` says "drinkers two deep at the near end", and panels 2, 3 and 5 have them while panels 1 and 6 — the
two-shot and its END — are effectively an empty bar; `seq_corridor_0` has six panels and zero extras. The
per-panel clause is the only form that reaches every panel. The "different people in different postures" sentence
is the crowd half of DIFFERENT PICTURES: copied extras are the cheapest way for the model to make two panels look
like one picture.

---

**`PANELS`** — the two panel templates, start and END.

**Start panel:**

> Panel {k} — {SIZE}, camera {where the camera stands, relative to the route and to the action}.
> In frame: {nouns, each at a named position, largest first}.
> {landmark ladder clause, only when this panel looks along the route}
> {background life clause, unless this is an insert}
> This is the instant BEFORE the action: {the named action} has not started. {What is still at rest, said
> positively — where the object that is about to move is right now.}

Two changes from today. First, **the camera is placed, not just the subject** — "camera low on the cobbles at the
kerb, level with the hub, on the near side of the street", not "Insert low beside the moving hansom". The
guides are explicit that framing/viewpoint language is obeyed while implicit spatial assumption is not (§3), and
an unplaced camera is exactly how `Q03_1` ended up on a different axis from `Q03_0`. Second, **"the instant
before" must be followed by where the moving thing currently IS.** Today's `panel_text()` writes "The instant
before: Static shot; Stamford lifts his glass; …" — a verb phrase, which the model drew as the completed action:
`Q02_0` has the glass already up, `Q12_0` has Holmes already sprung upright, `Q17_2` has the cloud already spread.
The fix is a noun: "Stamford's glass is still standing on the mahogany and his hand is not yet on it."
Note also that `Static shot;` is deleted from every panel — it is a *video* instruction that leaked into a still
prompt, and it is what put a blue Bunsen flame on Watson's cravat stud (reviewer 3, change 4): the motion text is
for MiniMax, not for the drawer. The sheet gets only the still.

**END panel:**

> Panel {k} — THE END OF PANEL {j}. The same place, the same camera position, the same lens, the same light and
> the same wardrobe as panel {j}, one action later.
> In frame: {the CHANGED picture, written from scratch as nouns in positions — never "as panel j but…"}.
> Changed since panel {j}: {the one named change, in five words}.
> Unchanged since panel {j}: {place, camera, lens, light, wardrobe, and the named fixed objects}.
> Panel {k} is a different photograph from panel {j}: a viewer seeing them side by side must be able to say what
> happened in between.

Every clause earns its place:

| clause | why |
|---|---|
| "THE END OF PANEL {j}" | names the relation without the word *identical*, which is what produced the copies |
| "the same place, camera, lens, light and wardrobe … one action later" | the preservation list the guides say to state explicitly and repeat, minus the word "framing", which the model read as "the same picture" |
| "In frame: {picture}" written out in full | the load-bearing change. The END panel gets its own complete noun-and-position description, the same length as a start panel, so the model has something to draw that is not the start panel. Today it gets a verb phrase and copies |
| "Changed since panel {j}: …" | one change, named, so the DQ and the human have the same sentence to check; and so a second attempt can quote it back |
| "Unchanged since panel {j}: …" | stops the Q03_0E failure mode — given only "make it different", the model changed the *location*. Naming the street, shopfronts and sky as unchanged removes that degree of freedom |
| "a viewer must be able to say what happened in between" | the human contact-sheet check and the machine gate, in one sentence, in the prompt |

An END panel **always sits immediately after its own start panel** on the sheet (§1.3), never in a block at the
end. Two reasons: the model reads the list as a narrative, so `[start][END][next start][next END]` is the true
sequence; and reviewer 3 measured that an END panel parked at the end of the *reference strip* was read by
MiniMax as a further shot, so T02 and T07 cut back to the wide. Adjacency is the same fix on both surfaces.

---

**`STYLE`** — `STILL`, unchanged. It is working: the six sheets are one register.

**`CONSTRAINTS`**

> No text, no numbers, no captions, no labels, no watermark, no panel borders except the thin white gutters.
> No panel repeats another panel.
> No gloves on any hand.

*Why.* The OpenAI cookbook states that gpt-image obeys negative constraints when they are explicit and few
("no watermark", "do not add new elements") — this is the **opposite** of the MiniMax rule in the brief, and the
spec must say so out loud so the two prompt families do not get cross-contaminated: **negations are allowed and
useful in the sheet prompt; they remain banned in every MiniMax ref2v prompt.** `BANNED_PROPS = ("glove",)` in
`episode_spec.py` already lints the plan for the word; the sheet now also says it to the drawer.

### 1.3 Panel ordering — the whole rule, in five lines

1. Panels are the setup's segments in **story order** (shot index, then sub-shot index). No geography-first sort.
2. Every segment whose plan entry has `end` set is followed **immediately** by its END panel.
3. A start panel and its END panel are **never split across two sheets**.
4. A sheet holds **6 panels** (3×2 at 2048×2048) unless a setup packs exactly to 9 (3×3 at 2048×3072); a 3×1 is
   used only for a 3-panel remainder that contains no face (§5).
5. No more than **4 END panels on one sheet**, so the sheet is never mostly a copying exercise.

---

## 2. WORKED EXAMPLES — the two sheets, written out in full

### 2.1 The criterion sheet — one 3×3, 9 panels, 4 END panels

Cells: `Q00_0, Q00_0E, Q01_0, Q01_0E, Q01_1, Q02_0, Q02_0E, Q02_1, Q02_1E`.
Note the two START redraws this sheet also carries: `Q02_0` must be drawn with **the glass still on the counter**
(today it is already raised, which is why its END had nothing left to do).

```
SHEET
A film storyboard sheet: a 3 by 3 grid of 9 equal vertical 9:16 panels filling the whole canvas, thin white
gutters between them and no other border. Panels read left to right, top to bottom: panel 1 is top-left, panel 3
is top-right, panel 9 is bottom-right.

DIFFERENT PICTURES
Every panel on this sheet is a DIFFERENT photograph. No two panels may share camera position, subject size and
background at the same time. Laid side by side, a viewer must be able to say in one word how each panel differs
from every other panel. Never draw the same picture twice on this sheet, and never draw a panel that a viewer
would mistake for another panel at a glance.

ORDER
The panels are in story order: panel 1 happens first, panel 9 happens last, and the camera never goes back to an
earlier moment. The two men move along the counter, from the crowded doors at its near end to its quieter far end
under the mirror. Panels 1, 3 and 6 look along the counter, and each of them is farther along it than the one
before, so the great gilt-framed mirror behind the counter is larger in panel 3 than in panel 1 and larger again
in panel 6.

REFERENCES
Image 1 is the empty location: every panel is set in this exact room, with its architecture, furniture, windows
and light.
Image 2 is John Watson: a man in his late twenties, as thin as a lath, as brown as a nut, dark hair swept back, a
thin waxed moustache. Keep exactly this face, hair, build and these clothes in every panel that shows John Watson.
Image 3 is Stamford: a stout young man in his mid-twenties, round clean-shaven face, dark hair parted at the side,
small bright eyes. Keep exactly this face, hair, build and these clothes in every panel that shows Stamford.

LOCATION
The Criterion Bar, Piccadilly, 1881, early evening: a long mahogany counter with a brass foot-rail under a great
gilt-framed mirror, gasoliers burning yellow through tobacco haze, marble pillars, bottles ranked on glass
shelves, a tiled floor; warm gaslight, the dark street only beyond the doors.

GEOMETRY
The counter is one straight run of mahogany crossing the frame; the great gilt-framed mirror is fixed to the wall
BEHIND the counter, above the ranked bottles. It is a mirror and it shows the backs of the men standing at the
counter and the gasoliers above them. There is no window behind the counter and no street is visible in it. In
every panel on this sheet the camera stands on the drinkers' side of the counter and never goes behind it, so the
bottles and the mirror are always beyond the men and the brass foot-rail is always nearest the camera at the
bottom of frame.

WARDROBE
These do not change in any panel of this sheet.
WATSON: fawn-brown tweed overcoat, white cravat with a stud. His RIGHT hand is bare and sunburnt and is closed on
the silver ball knob of the black walking stick. He wears NO gloves in any panel. This is indoors, so the brown
bowler is OUT of his hair at all times: it hangs from the knob of the stick or is held flat against his chest in
his other hand.
STAMFORD: black frock coat over a grey waistcoat, white shirt, dark cravat, round clean-shaven face, dark hair
parted at the side. This is indoors, so his black bowler is in his hand or on the counter, never on his head.

BACKGROUND LIFE
This is a public bar on a working evening and it is never empty. The people behind the action are different people
in different postures in every panel; they are never the same group copied from panel to panel. They are busy with
their own drinks and their own talk, and none of them looks at the camera or at the two men in front.

PANELS
Panel 1 — MEDIUM CLOSE-UP, camera at the crowded near end of the counter, at standing eye height, looking along
the mahogany. In frame: Stamford filling the right two-thirds, turned toward the camera, his right hand lifted and
still in the air a few inches above a fawn tweed shoulder; Watson's tweed back and the back of his dark head at the
left edge, nearest the camera and out of focus; the gilt mirror small behind them, the height of a thumbnail,
holding the reflected backs of the drinkers. Behind them, eight or nine men in top hats and bowlers standing two
deep at the counter, a white-aproned barman drawing a cork, a waiter crossing left to right with a tray, all out
of focus. This is the instant BEFORE the action: Stamford has not yet spoken and the man in front of him has not
yet turned. Stamford's mouth is closed, his hand is still above the shoulder and has not touched it, and his
eyebrows are level.

Panel 2 — THE END OF PANEL 1. The same place, the same camera position, the same lens, the same light and the
same wardrobe as panel 1, one action later. In frame: Stamford still filling the right two-thirds, his hand now
DOWN at his side and empty, his eyebrows lifted high and the smile gone flat; and where the tweed back was, Watson
has turned and his gaunt sunburnt face is now in three-quarter profile at the left edge, the moustache and the
hollow cheek readable. Behind them the same bar, the same barman now with the cork free, the drinkers in new
postures. Changed since panel 1: Stamford's hand has dropped and Watson has turned his face into frame. Unchanged
since panel 1: the room, the camera, the lens, the gaslight, the mirror's size and place, both men's clothes.
Panel 2 is a different photograph from panel 1: a viewer seeing them side by side must be able to say what
happened in between.

Panel 3 — CLOSE, camera a few steps farther along the counter, at eye height, turned to face Watson. In frame:
Watson filling the frame, bareheaded, dark hair swept back, gaunt sunburnt face, thin waxed moustache, mouth
closed, his eyes level on the man at the left edge; the brown bowler held flat against his chest in the hand on
the right of frame; Stamford's black shoulder cutting the left edge, out of focus. The great gilt-framed mirror
behind the counter is the height of a finger. Behind them, four hatted drinkers at the rail and a barman's white
sleeve reaching up to a shelf, all soft. This is the instant BEFORE the action: the tired smile has not come yet.
His throat is still, his jaw is set, and the bowler is flat against his chest with both edges of its brim level.

Panel 4 — THE END OF PANEL 3. The same place, the same camera position, the same lens, the same light and the same
wardrobe as panel 3, one action later. In frame: Watson's head and shoulders have squared round to face Stamford
fully, so he is now nearly frontal to the camera rather than turned to the left edge; his throat has moved and his
chin is a little lifted; the bowler has come away from his chest and is now held low, down at the bottom edge of
frame, its crown toward the camera; Stamford's black shoulder is larger at the left edge, a pace nearer. Behind
them the same bar with the drinkers in new postures. Changed since panel 3: his body has turned square to Stamford
and the hat has dropped to the bottom of frame. Unchanged since panel 3: the room, the camera, the lens, the
gaslight, the mirror's size and place, both men's clothes. Panel 4 is a different photograph from panel 3: a
viewer seeing them side by side must be able to say what happened in between.

Panel 5 — INSERT, camera low at the brass foot-rail, a hand's breadth above the mahogany, close enough that the
counter's grain fills the bottom of frame. In frame: Watson's bare sunburnt right hand closed on the silver ball
knob of the black walking stick at the centre, the frayed tweed cuff above it; one wine glass standing on the
mahogany at the right edge, untouched, with an inch of dark red in it; the brass rail a bright horizontal line
below. No face in frame, no other hand in frame. This is the instant BEFORE the action: the fingers are fully
closed on the knob and the glass has not been touched.

Panel 6 — MEDIUM TWO-SHOT, camera at the quieter far end of the counter, at standing eye height, square to the
mahogany with both men beyond it. In frame: Watson at the left, bareheaded, in three-quarter profile facing right;
Stamford at the right, facing him; between and below them two wine glasses STANDING ON THE COUNTER, both hands
away from them; Watson's bare sunburnt right hand on the silver knob of the stick at the counter's rail nearest
the camera, the brown bowler hanging from the knob; the great gilt-framed mirror filling the wall behind them, the
height of a hand, showing both their backs and the gasoliers. Behind them, three or four drinkers thinning out
toward this end, one man reading a folded paper at the rail, the barman polishing a glass. This is the instant
BEFORE the action: Stamford's glass is still standing on the mahogany and his hand is not yet on it; both men's
faces are level and neither has looked down.

Panel 7 — THE END OF PANEL 6. The same place, the same camera position, the same lens, the same light and the same
wardrobe as panel 6, one action later. In frame: Stamford's glass has left the counter and is now AT HIS LIPS, his
hand round its bowl, his eyes on Watson over the rim; the space on the mahogany where that glass stood is empty
and wet-ringed; Watson's head has dropped, his face is angled down into his own glass, his eyes lowered, the
brim of the hanging bowler now level with his bowed chin. Behind them the same far end of the bar, the man with
the paper now turning a page. Changed since panel 6: one glass has travelled from the counter to Stamford's mouth
and Watson's head has bowed. Unchanged since panel 6: the room, the camera, the lens, the gaslight, the mirror,
the second glass on the counter, both men's clothes. Panel 7 is a different photograph from panel 6: a viewer
seeing them side by side must be able to say what happened in between.

Panel 8 — CLOSE, camera at the same far end of the counter, at eye height, turned to face Stamford. In frame:
Stamford filling the frame, his raised glass at the bottom of frame with its rim across his chin, his eyes above
it fixed off frame to the left in an odd measuring look, mouth closed; gaslight on the right side of his face; the
gilt mirror behind his shoulder, out of focus. Behind him, two drinkers' dark shapes and a lit gasolier. This is
the instant BEFORE the action: the glass is still up at his chin, his hand still round it, and his other hand is
down out of frame.

Panel 9 — THE END OF PANEL 8. The same place, the same camera position, the same lens, the same light and the same
wardrobe as panel 8, one action later. In frame: the glass is GONE from frame, set down below the bottom edge; his
raised hand is now at his mouth with the back of two fingers against his lower lip, wiping it; his eyes are still
fixed off frame to the left, unchanged; his chin and jaw, which the glass hid, are now visible. Behind him the
same two drinkers in new postures and the same gasolier. Changed since panel 8: the glass is down and out of
frame and the hand is at the lip. Unchanged since panel 8: the room, the camera, the lens, the gaslight, the
mirror behind his shoulder, his clothes, the direction of his eyes. Panel 9 is a different photograph from panel
8: a viewer seeing them side by side must be able to say what happened in between.

STYLE
Photoreal cinematic 35 mm film stills, 1881 London, natural film grain, muted soot-black and gaslight-amber
palette.

CONSTRAINTS
No text, no numbers, no captions, no labels, no watermark, no panel borders except the thin white gutters.
No panel repeats another panel. No gloves on any hand.
```

References attached, in order: `plate_criterion.png`, `char-john_watson_criterion.png`, `char-stamford.png`.

### 2.2 The cab sheet A — one 3×2, 6 panels, 2 END panels

Cells: `Q03_0, Q03_0E, Q03_1, Q04_0, Q04_0E, Q04_1`.
Two START redraws this sheet carries: `Q03_0` drawn with the cab **entering at the left edge** (today it is
centred, which is why the render could only tread water), and `Q04_0` drawn with the **hood behind the head and
no window in it** (today there is a rain-streaked pane behind Watson, a brougham's rear window, contradicting the
front-glass insert `Q05_1` on sheet B).

```
SHEET
A film storyboard sheet: a 3 by 2 grid of 6 equal vertical 9:16 panels filling the whole canvas, thin white
gutters between them and no other border. Panels read left to right, top to bottom: panel 1 is top-left, panel 3
is top-right, panel 6 is bottom-right.

DIFFERENT PICTURES
Every panel on this sheet is a DIFFERENT photograph. No two panels may share camera position, subject size and
background at the same time. Laid side by side, a viewer must be able to say in one word how each panel differs
from every other panel. Never draw the same picture twice on this sheet, and never draw a panel that a viewer
would mistake for another panel at a glance.

ORDER
The panels are in story order: panel 1 happens first, panel 6 happens last, and the camera never goes back to an
earlier moment. Panels 1, 2 and 3 are outside the cab on one street; panels 4, 5 and 6 are inside it, on the same
journey, a little later.

REFERENCES
Image 1 is the empty location: the wet cobbled street and its shopfronts, the exact place, architecture and light
of every exterior panel.
Image 2 is the cab: this exact vehicle — the same black body, folding hood, tall spoked wheels, brass side-lamp,
harness and bay horse — in every panel of this sheet that shows a cab. It is the same cab all afternoon.
Image 3 is John Watson: a man in his late twenties, as thin as a lath, as brown as a nut, dark hair swept back, a
thin waxed moustache. Keep exactly this face, hair, build and these clothes in every panel that shows John Watson.
Image 4 is Stamford: a stout young man in his mid-twenties, round clean-shaven face, dark hair parted at the side,
small bright eyes. Keep exactly this face, hair, build and these clothes in every panel that shows Stamford.

LOCATION
A wet cobbled street just off Piccadilly, London, 1881, under a grey afternoon sky: shopfronts with lit windows,
gas lamps on iron posts already burning, standing water between the cobbles, the rain just stopped.

GEOMETRY
This vehicle is a hansom cab and it is built like this. ONE pair of tall spoked wheels, one wheel on each side of
the body, their axle passing UNDER THE MIDDLE of the passenger box: the wheels are beside the passengers, not
behind them. The bay horse stands in the shafts AHEAD of the box, and the horse's hind hooves are two
horse-lengths clear of the wheel, never level with it; between the wheel and the horse there is only wet cobble
and the black underside of the two long shafts. The driver sits high at the BACK of the roof, behind and above the
passengers' heads, and the reins run forward over the roof to the horse. The brass side-lamp is mounted on the
body at the front corner, at the passengers' shoulder height. The two passengers sit side by side facing FORWARD,
toward the horse, with the folding hood closing behind and above their heads — the hood is solid and there is no
window in it — and with the small rain-streaked front glass and the leather apron ahead of their knees, the
horse's back and the reins visible beyond that glass.
In every exterior panel on this sheet the camera stands on the pavement on the near side of the street and never
crosses the street. The cab travels from the LEFT edge of frame toward the RIGHT edge, horse leading. Therefore in
every exterior panel the horse is to the RIGHT of the wheels, the driver is to the LEFT of them, and the water
thrown by the wheels flies backward, to the left.

WARDROBE
These do not change in any panel of this sheet.
WATSON: fawn-brown tweed overcoat, white cravat with a stud. His RIGHT hand is bare and sunburnt and is closed on
the silver ball knob of the black walking stick. He wears NO gloves in any panel. This is outdoors and in an open
cab, so the brown bowler is ON HIS HEAD in every panel.
STAMFORD: black frock coat over a grey waistcoat, white shirt, dark cravat, round clean-shaven face, dark hair
parted at the side; his black bowler is ON HIS HEAD in every panel.

BACKGROUND LIFE
This is a working London street and it is never empty. The people behind the action are different people in
different postures in every panel; they are never the same group copied from panel to panel. They are busy with
their own errands and none of them looks at the camera or at the cab.

PANELS
Panel 1 — WIDE EXTERIOR, camera on the near pavement, at chest height, square to the street, the far shopfronts
filling the background across the whole frame. In frame: the hansom just ENTERING at the LEFT EDGE, so that only
the horse's head and forequarters and the leading edge of the near wheel are yet inside the frame and the rest of
the cab is still cut off by the left edge; the bay horse at a trot, its head high; the driver's top-hatted
shoulders above the hood behind it; two hatted passengers small under the hood; the brass side-lamp lit. The whole
RIGHT two-thirds of the frame is empty wet street, standing water and the kerb with a lamp post, with nothing on
it. Behind, on the far pavement, four pedestrians under umbrellas, a boy with a broom at the crossing, a second
cab waiting at the kerb beyond, all out of focus. This is the instant BEFORE the action: the cab has not yet
crossed the street. The puddle in the middle of the frame is still flat and unbroken, and the road ahead of the
horse is clear.

Panel 2 — THE END OF PANEL 1. The same street, the same camera position on the near pavement, the same lens, the
same light, the same shopfronts and the same lamp posts as panel 1, one action later. In frame: the hansom is now
LEAVING at the RIGHT EDGE — the horse has already gone out of frame past the right edge and only its tail and
hind hooves are still in, the passenger box and the near wheel are at the right third, the driver's back is the
last of him in view, and the LEFT two-thirds of the frame is now empty wet street with the kerb where the cab
entered standing bare. The puddle at the centre is broken, with a falling sheet of thrown water behind the wheel,
to the left of it. Behind, on the far pavement, the same shopfronts and lamp posts, different pedestrians in
different postures, an old woman with a basket where the boy with the broom was. Changed since panel 1: the cab
has travelled the whole width of the frame, from the left edge to the right edge. Unchanged since panel 1: the
camera, the street, the shopfronts, the lamp posts, the kerb, the sky and the light. Panel 2 is a different
photograph from panel 1: a viewer seeing them side by side must be able to say what happened in between.

Panel 3 — INSERT, camera set down LOW on the cobbles at the near kerb, level with the wheel hub, looking straight
across the street at the passing cab, on the same near side as panels 1 and 2. In frame, filling the LEFT
two-thirds: ONE tall spoked wheel, close and turning, its iron tyre throwing a curved sheet of water backward to
the left, the black body and the lit brass side-lamp above and behind it. Far away at the TOP RIGHT of frame,
small and out of focus, the horse's hind hooves and tail, two cab-lengths farther down the street. Between the
wheel and the horse there is nothing but wet cobble and the dark underside of the two shafts running from the
body forward and out of frame. There is exactly ONE wheel in frame. No part of the horse is level with the wheel
and no part of the horse is as large as the wheel. Behind, on the far pavement, three blurred walkers and a lit
shop window. This is the instant BEFORE the action: the sheet of water is just leaving the tyre and has not yet
fallen.

Panel 4 — CLOSE, camera inside the cab on the passengers' bench, low and turned back toward Watson's face, so the
hood is above and behind his head. In frame: Watson filling the frame, brown bowler on, gaunt sunburnt face, thin
waxed moustache, mouth closed, his eyes forward on the small rain-streaked front glass; the dark folding hood
closing BEHIND and ABOVE his head, solid, with no window in it; over his shoulder ahead of him the small
rain-streaked front glass with the bay horse's back and the reins beyond it; Stamford's black shoulder and the
edge of his round clean-shaven face at the right edge, out of focus; flat grey afternoon light. This is the
instant BEFORE the action: he is square in his seat, both shoulders level, the bowler set straight on his head,
and he has not yet been jolted.

Panel 5 — THE END OF PANEL 4. The same seat, the same camera position, the same lens, the same light and the same
wardrobe as panel 4, one action later. In frame: a jolt has thrown Watson to his right, so his near shoulder is
now hard against the side of the hood and his head is tilted well off vertical, the brown bowler knocked askew on
his head with its brim across one eyebrow; his eyes have dropped from the front glass to the floor of the cab;
Stamford's black shoulder at the right edge is nearer, pushed against him. Behind and above, the same solid hood
with no window; ahead, the same front glass with the horse's back beyond. Changed since panel 4: the jolt has
thrown his shoulder into the hood and knocked the bowler askew. Unchanged since panel 4: the cab, the camera, the
lens, the grey light, the hood, the front glass, both men's clothes. Panel 5 is a different photograph from panel
4: a viewer seeing them side by side must be able to say what happened in between.

Panel 6 — INSERT, camera inside the cab looking down at knee height between the two passengers. In frame:
Watson's bare sunburnt right hand gripping the silver ball knob of the black walking stick, the stick planted
upright between his knees with its ferrule on the wet cab floor, the frayed tweed cuff above the hand, wet
floorboards and the edge of the leather apron below. No face in frame, no other hand in frame. This is the instant
BEFORE the action: the knuckles are flat and unblanched, the ferrule is set square on the boards, and the hand
has not yet tightened.

STYLE
Photoreal cinematic 35 mm film stills, 1881 London, natural film grain, muted soot-black and gaslight-amber
palette.

CONSTRAINTS
No text, no numbers, no captions, no labels, no watermark, no panel borders except the thin white gutters.
No panel repeats another panel. No gloves on any hand.
```

References attached, in order: `plate_street.png` (the empty wet street, **not** today's two-panel
`plate_cab.png` composite), `plate_cab.png` **redrawn as one side-on picture of the whole vehicle with the bay
horse in the shafts** (reviewer 3, change 3 — the current plate is the only horseless picture the pipeline still
sees), `char-john_watson.png`, `char-stamford.png`.

**Cab sheet B** (the second 3×2, same header blocks, `LOCATION` switched to the cab interior):
`Q05_0, Q05_0E, Q05_1, Q06_0, Q06_1, Q06_1E`.

---

## 3. RESEARCH — what gpt-image obeys for multi-panel consistency and physical geometry

Model in use: `MODEL = "gpt-image-2.5-sunburst"` (`studio\episode_board.py`), called through
`client.images.edit(...)` with reference handles (`scripts\episode\storyboard.py`).

**Primary — OpenAI.**

- *Image prompting guide* — https://developers.openai.com/api/docs/guides/image-prompting
  - Comic strips: "define the narrative as a sequence of clear visual beats, one per panel. Keep descriptions
    concrete and action-focused." Its worked example is exactly `Panel 1: … Panel 4: …`, one distinct moment each.
    → **The panel list is read as a story. Story order is the order the model is built to follow; the
    geography-first sort in `split()` fights it.**
  - For complex requests, organise the prompt as **scene, subject, details, constraints, using labelled
    sections** rather than one paragraph. → the block layout in §1.1.
  - **Assign explicit roles to references** ("subject, style, clothing, background") and explain how the inputs
    combine. → the REFERENCES block, and the new "Image N is the cab" line.
  - Consistency across a sequence comes from **repeating the appearance constraints**, not from the model
    remembering. → the WARDROBE block, repeated on every sheet.
  - Spatial intent: specify "body framing, relative scale, gaze, and interaction with objects" — e.g. "full body
    visible, feet included", "hands naturally gripping the handlebars" — rather than relying on implicit
    positioning. → the GEOMETRY rule that every relation is restated as *which edge, at what apparent size*.
- *gpt-image-1.5 prompting guide (cookbook)* —
  https://developers.openai.com/cookbook/examples/multimodal/image-gen-1.5-prompting_guide
  - Ordering: "background/scene → subject → key details → constraints", with "short labelled segments or line
    breaks instead of one long paragraph".
  - **Negative constraints are obeyed when stated explicitly** — "no watermark", "preserve identity/geometry/
    layout", "do not add new elements" — and the preserve list should be **repeated to reduce drift**.
    → the CONSTRAINTS block and the per-END-panel "Unchanged since panel j:" clause. Note this is the exact
    opposite of the MiniMax rule; the spec states both so they do not cross-contaminate.
  - Placement is controlled by **directional cues** ("logo top-right", "subject centred with negative space on
    the left"). → the camera-line sentence "the horse is to the RIGHT of the wheels, the driver is to the LEFT".
  - Label inputs "by index and description" and state the interaction explicitly.
  - "Iterate instead of overloading": avoid asking for several variations inside one prompt.
    → the argument for 6 panels per sheet rather than 9.

**Vendor / practitioner, on grids and sheets.**

- fal, *GPT Image 2 prompting guide* — https://fal.ai/learn/tools/prompting-gpt-image-2
  - Five-section template with line breaks: **Scene / Subject / Important details / Use case / Constraints**.
    "The model responds to structure."
  - **Up to 16 reference images per call**, labelled "Image 1: [role], Image 2: [role]" and referenced by number.
    → we currently attach 3–4; there is room for the vehicle plate.
  - For edits: "Change only X", "Keep everything else the same", **repeating the preservation list every
    iteration**; and "separate change requests from preservation lists" — which is precisely the
    `Changed since … / Unchanged since …` pair in the END panel template.
- CrePal, *How to use GPT Image 2 for storyboards and comics* —
  https://crepal.ai/blog/aiimage/image-how-to-use-gpt-image-2-for-storyboards-and-comics/
  - **6–8 panels per batch perform reliably; beyond that requires manual review. Drift occurs beyond 8–10
    panels, and multiple characters increase the inconsistency probability.**
    → the single strongest argument for moving from 3×3 to 3×2. Our sheets carry three characters.
  - Differentiation comes from **varying camera angle and position** and describing "what shouldn't shift, not
    just what should"; restate character descriptors in **every** panel rather than assuming carry-over.
  - Location consistency: "repeat setting descriptors across panel prompts".
  - Use 1:1 canvases for 3×3 grids to keep panels proportional (we use 2048×3072 for 3×3 because the cells must
    be 9:16, which is the right call for our downstream 768×1344 conform).
- Felo, *GPT Image 2.5 prompting guide* — https://felo.ai/blog/gpt-image-2-5-prompting-guide/ — multi-panel work
  holds "with a reference image and a **repeated consistency clause**"; describe the defining physical traits once
  at the top and reference them per panel.
- Promptessor, *GPT Image 2.5 prompting guide* — https://promptessor.com/blog/gpt-image-2-5-prompting-guide
  - References need **explicit roles**; "use image 2 as reference" is not specific enough for production.
  - **Camera specifications are "appearance cues, not guarantees of physically exact optical simulation"** — use
    them to describe visible framing and depth, not to expect optical accuracy.
    → this is why the GEOMETRY block does not say "35 mm from 4 m at the horse's hip"; it says which object is at
    which edge at what size.
  - Documented failure mode: **drift during multi-turn editing** — "you ask to replace a chair and the camera
    angle shifts"; 2.5 improves it but "the prompt still needs to make the preservation target explicit".
    → an END panel is structurally the same request as an edit ("change one thing, keep the rest"), and it fails
    the same way unless the preservation target is spelled out.
- Big Prompt Hub, *AI short-drama continuity workflow* — https://www.bigprompthub.com/ai-short-drama-prompt-workflow-2026/
  and Prompt Architects, *Storyboarding shot-by-shot* — https://prompt-architects.com/blog/562-storyboarding-with-ai-images-shot-by-shot
  — "every panel description should restate the visual invariants: character appearance stays the same, but the
  scene, pose and camera angle change"; a wider and a tighter version of the same street do not break continuity
  "as long as the underlying location description stays recognisably the same place".

**Literature, on why "ahead of" fails.**

- *RL-RIG: A Generative Spatial Reasoner via Intrinsic Reflection* — https://arxiv.org/pdf/2602.19974 —
  image generators "struggle with a spatial reasoning dilemma, lacking the ability to accurately capture
  fine-grained spatial relationships from the prompt and correctly generate scenes with structural integrity";
  the worked failure the paper opens with is a generator that **missed "a two-wheeled vehicle in front of a
  black car"** — the same relation, on the same class of object, as `Q03_1`.
- *GeoWorld-VLM: Geometry from World Models for Vision-Language Models* — https://arxiv.org/pdf/2605.16713 —
  "task supervision or static visual feature alignment alone may be insufficient for relations that require
  geometric structure, such as **vertical placement, left–right ordering, and viewpoint-dependent distance
  judgment**." All three are exactly what the cab insert got wrong.

**The net rule this research produces, and the whole reason the rewrite is shaped as it is:**
gpt-image-2.5 reliably obeys *narrative order*, *labelled structure*, *explicit reference roles*, *repeated
invariant lists*, *explicit negatives*, and *frame-relative placement with apparent size*. It does **not**
reliably obey *relational prepositions*, *implied camera continuity*, or *verb phrases describing change*. So
every rule in §1 is the conversion of something in the second list into something in the first list.

---

## 4. THE EXACT CHANGES TO THE CODE

### 4.1 `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\studio\episode_seq_board.py`

**A. Contract first (a one-line dependency in `studio\episode_spec.py`).** Add to both `Shot` and `SubShot`:

```python
end: str | None = None
"""The picture AFTER this segment's motion, as nouns in positions.  The END
panel is drawn iff this is set."""
changed: str = ""
"""The one named change between the start picture and `end`, in five words."""
```
and a plan lint (beside `banned_prop`): a segment whose `motion` contains a travel or state-change verb
(*crosses, exits, climbs, steps, walks, turns, lifts, lowers, sets down, comes off, springs up, falls, spreads,
darkens, closes, drops*) and has no `end` fails the plan. This is the spec-first half; without it `end_panels`
is guessing again.

**B. Delete `end_panels(segs, spare)`.** Replace with:

```python
def end_panels(segs: list[dict]) -> list[dict]:
    """One END cell for every segment the PLAN gives an `end` to.  Never invents one,
    never fills spare cells (2026-09-11: four of five invented END cells were copies)."""
    return [dict(s, end=True, of=i + 1, frame=s["end"], changed=s["changed"], motion="")
            for i, s in enumerate(segs) if s.get("end")]
```

**C. Delete `split()`, `geo_order()`, `close_order()`, `end_order()`.** They implement the geography-first sort
and the three ordering sentences that contradict each other. Replace with:

```python
def interleave(segs: list[dict], ends: list[dict]) -> list[dict]:
    """Story order, each END cell immediately after its own start cell."""
    out = []
    for i, s in enumerate(segs):
        out.append(s)
        out += [e for e in ends if e["of"] == i + 1]
    return out


def route_panels(cells: list[dict]) -> list[int]:
    """1-based panel numbers that look ALONG the route: a geography size, a
    route position, and the plan's own `route_view` flag -- never a substring
    search for 'behind' (2026-09-11: 'the mirror behind them' put a distance
    ladder on a bar counter)."""
    return [k for k, c in enumerate(cells, start=1)
            if not c.get("end") and c["size"] in GEO_SIZES and c.get("path") is not None
            and c.get("route_view")]


def order_block(cells: list[dict], setup: Setup) -> str: ...
```
(`route_view: bool = False` is the third new plan field; it is a property of the shot, not of its prose.)

**D. `sheets()` rewritten.** Exact-fit packing that never splits a start/END pair, caps END panels per sheet, and
**fails loudly** rather than padding:

```python
GRIDS = ((3, 2, (2048, 2048)), (3, 3, (2048, 3072)), (3, 1, (1536, 1024)))
"""Preference order, not size order.  3x2 is first: 682x1024 cells (the same
as 3x3), the cheapest cell at $0.0217, and inside the 6-8 panel band the model
holds (research 2026-09-11).  3x1 is last: 512x1024 cells need a 1.5x upscale
to 768x1344, so no face may ride on one."""
MAX_ENDS_PER_SHEET = 4


class PackError(ValueError):
    """The setup does not pack to full sheets: says which segment needs an `end`."""


def pairs(cells: list[dict]) -> list[list[dict]]:
    """[start] or [start, its END] -- the unit that may not be split."""


def sheets(segs: list[dict]) -> list[tuple[list[dict], tuple]]:
    """Story order, pairs kept whole, each sheet exactly 6 (or 9, or 3 with no face)."""
```

The old `(cells, n_geo, grid)` triple loses `n_geo` — nothing downstream needs it once `route_panels()` computes
the ladder from the cells themselves.

**E. `panel_text()` split into two functions.**

```python
def start_panel(k: int, seg: dict, ladder: str, crowd: str) -> str:
    """Panel {k} -- {SIZE}, camera {camera}. In frame: {frame}. {ladder} {crowd}
    This is the instant BEFORE the action: {motion-as-not-yet}. {at_rest}"""


def end_panel(k: int, seg: dict, crowd: str) -> str:
    """Panel {k} -- THE END OF PANEL {j}. ... In frame: {end}.
    Changed since panel {j}: {changed}. Unchanged since panel {j}: {unchanged}.
    Panel {k} is a different photograph from panel {j}: ..."""
```
Both drop `Static shot;` and every other motion-verb clause: the sheet prompt gets the still, `motion` belongs to
the MiniMax prompt. `seg["camera"]`, `seg["at_rest"]` and `seg["unchanged"]` are derived, not new plan fields:
`camera` is parsed off the front of `frame` today ("Insert low beside the moving hansom") and should be its own
plan key; `at_rest` and `unchanged` are written by the plan author beside `end`.

**F. New block builders**, each a 10–20 line pure function with its own test:
`different_pictures()`, `wardrobe_block(cast, physical, indoors)`, `crowd_block(setup)`,
`geometry_block(setup)`, `constraints_block()`.
`Setup` gains `geometry: str = ""`, `crowd: str = ""`, `props: list[str] = []` (the prop plates to attach).

**G. `prompt()` emits labelled blocks joined by `"\n\n"`,** in the §1.1 order, instead of one paragraph.

**H. `duplicates()` — one floor, every pair.**

```python
COPY = 0.60
"""frame_match similarity.  Calibrated on the cells on disk (review 8): 99 pairs of
different shots max 0.58, 18 pairs of one shot's sub-cells max 0.47, 30 same-text
redraws max 0.53; copies score 0.82-0.95.  One number covers every pair, so an END
cell that repeats its own start can no longer slip through a same-shot exemption."""


def duplicates(cells: list, segs: list[dict], floor: float = COPY) -> list[tuple[str, str]]:
    """EVERY pair of cells on the sheet whose pictures match above `floor` --
    including a cell and its own END cell, which the old shot-index test skipped."""
```
Verdicts this reproduces on the cells already on disk: `Q02_0/Q02_0E` 0.951 FAIL, `Q07_0/Q07_0E` 0.890 FAIL,
`Q08_0/Q08_0E` 0.821 FAIL, `Q12_0/Q12_0E` 0.620 FAIL, `Q03_0/Q03_0E` 0.339 pass. All five agree with the eye.
0.50–0.60 is a warn band that goes to the human contact sheet rather than to an automatic redraw.

**I. Keep unchanged:** `cast_sheet`, `route_ok`, `segments` (plus the three new keys), `chunks`, `label`,
`cell_name`, `grid`, `door_size`, `LADDER`, `where`. They are measuring clean.

### 4.2 `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\scripts\episode\seq_boards.py`

1. **`groups = sq.sheets(segs)`** now returns `(cells, (cols, rows, canvas))`; `draw_setup` unpacks two, not
   three, and drops the `geography` variable it passes to `sq.prompt`.
2. **`refs_base`** gains the prop plates:
   ```python
   refs_base = [frames_dir / f"plate_{name}.png"]
   refs_base += [frames_dir / f"plate_{p}.png" for p in setup.props]   # the cab, the same vehicle everywhere
   refs_base += [sq.cast_sheet(book, who, name) for who in setup.cast]
   ```
   and `setup.props` for both `cab` and `gateway` is `["cab"]`, which is the fix for the three different vehicles.
   `plate_cab.png` must be redrawn first as ONE side-on picture of the whole hansom with the bay horse in the
   shafts (it is currently a two-panel composite with no horse, and it is the only horseless picture the takes
   still see).
3. **The ladder gate reads the right cells.** Today:
   ```python
   heights = [route_gate.door_height(c) for c in cells[:geography]]
   ```
   which assumes the geography cells are the leading ones. With story order they are scattered, so:
   ```python
   route = sq.route_panels(group)                                  # 1-based panel numbers
   heights = [route_gate.door_height(cells[i - 1]) for i in route]
   regress = route_gate.regressions(heights)
   paths = [group[i - 1].get("path") or 0.0 for i in route]
   regress = [i for i in regress if any(abs(paths[i] - paths[j]) >= 0.1
                                        for j in range(i) if heights[j] is not None)]
   ```
   The same-place-shrink exemption already in the file is kept verbatim.
4. **The STRICT retry names the offender.** Today it is one of two fixed strings. Replace with a message built
   from the failure:
   ```python
   if dupes:
       text = ("STRICT: panels {a} and {b} are the same picture and must not be. "
               "Panel {b} must differ from panel {a} at a glance: {changed}. " + text)
   if regress:
       text = ("STRICT: one walk, one direction; {landmark} is larger in every route panel than in the "
               "route panel before it, without exception. " + text)
   ```
5. **Second failure drops, never keeps.** Today a sheet that fails twice is written anyway and `passed` goes
   false. Add: if the second attempt still shows a START/END duplicate, delete that END cell from disk, record
   `{"dropped_end": "Q02_0E", "reason": "copy 0.94 after strict"}` in the report, and let the segment render with
   no end pin. A silently kept copy is worse than no END cell, because it becomes a pin and freezes the take.
6. **`report["passed"]`** gains `and not report["sheets"][-1]["duplicates"]` applied per sheet rather than only to
   the last entry (today `report["sheets"]` interleaves the strict and non-strict attempts, so `[-1]` can be a
   strict retry of one sheet while an earlier sheet still holds dupes).
7. **`--sheet=<k>` argument** beside `--setup=`, so one bad sheet can be redrawn for $0.13 without redrawing the
   setup. `draw()` is already cached on the output path, so the only change is the filename it is asked for.
8. **Tests** (no paid call, no repo asset, per the project rules): `interleave` puts an END next to its start;
   `pairs` never splits; `sheets` raises `PackError` naming the segment when a setup does not fill; `duplicates`
   flags an identical pair at 1.0 and passes a shifted block at < 0.6; `route_panels` ignores a close-up whose
   text contains the word "behind"; `end_panel` never contains the strings "identical", "Static" or "has just
   finished"; `start_panel` always contains "instant BEFORE".

---

## 5. SHEETS AND COST FOR THE REDRAW

Segments per setup (from `segments()` on `plan.json`) and the END cells from `scratchpad\review8\end_frames.md`:

| setup | segments | END cells | total cells | sheets | canvas | cost |
|---|---|---|---|---|---|---|
| criterion | 5 | 4 (0.0, 1.0, 2.0, 2.1) | 9 | 1 × 3×3 | 2048×3072 | $0.20 |
| cab | 8 | 4 (3.0, 4.0, 5.0, 6.1) | 12 | 2 × 3×2 | 2048×2048 | $0.26 |
| gateway | 7 | 5 (7.0, 8.0, 8.1, 21.0, 21.1) | 12 | 2 × 3×2 | 2048×2048 | $0.26 |
| corridor | 6 | 6 (9.0, 9.1, 10.0, 10.1, 11.0, 11.1) | 12 | 2 × 3×2 | 2048×2048 | $0.26 |
| lab | 8 | 4 (12.0, 12.1, 13.0, 13.1) | 12 | 2 × 3×2 | 2048×2048 | $0.26 |
| bench | 6 | 6 (17.0, 17.1, 17.2, 18.0, 19.0, 19.1) | 12 | 2 × 3×2 | 2048×2048 | $0.26 |
| **total** | **40** | **29** | **69** | **11 sheets** | | **$1.50** |

Corridor and bench exceed the 4-END-per-sheet cap only in total, not per sheet: each splits 3 + 3 across its two
sheets. The gateway split is also a fix in itself — sheet A is the arrival (7.0 → 8.1) and sheet B the departure
(20.0 → 22.0), which stops one sheet carrying two opposite route directions, as it does today.

**Strict redraws.** Today all six sheets "passed" on the first attempt because the gate was blind to START/END
copies; with the 0.60 all-pairs gate, four of the six sheets on disk would have failed. Budget one redraw on a
third of the sheets:

| | sheets | cost |
|---|---|---|
| first pass | 11 | $1.50 |
| expected strict redraws (4 × 3×2) | 4 | $0.52 |
| **expected total** | **15** | **$2.02** |
| ceiling (every sheet redrawn once) | 22 | $3.00 |

**What it replaces.** The six sheets on disk cost 3 × $0.20 (cab, gateway, lab at 3×3) + 3 × $0.13 (criterion,
corridor, bench at 3×2) = **$0.99**. Expected delta **+$1.03**, ceiling **+$2.01**.

**Why 3×2 and not 3×3, on every axis at once:**

| grid | canvas | price | cells | $/cell | cell px | upscale to 768×1344 | in the model's reliable band? |
|---|---|---|---|---|---|---|---|
| 3×1 | 1536×1024 | $0.08 | 3 | $0.0267 | 512×1024 | **1.50×** | yes but dearest per cell |
| 3×2 | 2048×2048 | $0.13 | 6 | **$0.0217** | 682×1024 | 1.31× | **yes (6–8 panels)** |
| 3×3 | 2048×3072 | $0.20 | 9 | $0.0222 | 682×1024 | 1.31× | at the edge (drift ≥ 8–10) |

3×2 is simultaneously the cheapest per cell, tied for the largest cell, and the only grid squarely inside the
6–8-panel band where the sources report multi-panel consistency holds with three characters in play. 3×1 is
reserved for a 3-cell remainder with no face in it, because a 512-px-wide cell needs a 1.5× upscale to reach
H3's 768×1344 and a face does not survive that. The single 3×3 is kept only for criterion, where the setup packs
to exactly 9 with every pair adjacent and splitting it would cost $0.21 and break a pair.

Every call is already logged by `spend.record(...)` inside `scripts\episode\storyboard.py:draw`, and `draw()`
returns early if the output file exists, so a re-run costs nothing for sheets already on disk. The redraw
therefore has to begin by moving the six current sheets and the 45 cells aside — recommended:
`…\episodes\ep01\frames\seq_v4\` beside the existing `seq_v1`, `seq_v2`, `seq_v3` folders.

---

## 6. THE ORDER TO DO IT IN

1. `studio\episode_spec.py`: `end`, `changed`, `route_view`, `camera`, `at_rest`, `unchanged` on `Shot`/`SubShot`;
   `geometry`, `crowd`, `props` on `Setup`; the travel-verb-needs-an-`end` lint. Tests first. No spend.
2. `plan.json`: write the 29 `end` pictures (review 8 §2 has 25 of them drafted), the geometry blocks for cab,
   gateway, corridor, criterion, lab and bench, the per-panel crowd clauses, and the four START rewrites
   (`Q02_0` glass down, `Q12_0` Holmes bent, `Q17_2` thread only, `Q03_0` cab entering at the left edge). No spend.
3. `studio\episode_seq_board.py` and `scripts\episode\seq_boards.py` per §4. Tests first. No spend.
4. Redraw `plate_cab.png` as one side-on hansom with the bay horse — **one** paid call, $0.08 at 1536×1024, and
   it has no face so the small cell does not matter.
5. Move `frames\seq_*` and `frames\Q*` to `frames\seq_v4\`, then draw the criterion sheet **alone** ($0.20) and
   look at it before authorising the other ten. If panels 1/2 and 6/7 read as different photographs and the bar
   is full of people, the template works and the remaining $1.30 is worth committing.

---

## 7. THE PUBLISHABLE ARTIFACT IN HERE

The general thing this proposal contains is not Sherlock Holmes. It is a **sheet-prompt compiler**: a plan of
shots with `end` / `changed` / `unchanged` / `route_view` fields compiles to a labelled multi-panel image prompt,
and a calibrated single-threshold perceptual gate (0.60 cosine on a 48×84 grey signature, all pairs) decides
whether the sheet came back with N distinct pictures or N−k. Both halves are model-agnostic and both are
measured against real generations rather than asserted. That is a standalone package — `storyboard-sheet`, or a
ComfyUI node pair (*Sheet Prompt* / *Panel Distinctness Gate*) — with a README that shows the Q02_0 / Q02_0E
0.951 failure and the fix. Nothing in it depends on this repo.
