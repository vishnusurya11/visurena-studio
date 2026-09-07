---
name: trailer-refs
description: Reference sheets that bind identity - and the collision problem when a book never describes anyone.
---

# Reference sheets

`step_02_refs.py` binds the cast: `describe.py` reads a sheet back into a
trait card, `distinguish.py` moves a colliding one, `cast_card.py` writes it,
`portrait.py` finds the book's own words, `trailer_refs.py`/`build_refs.py`
rank and render. The sheets belong to the BOOK (`library/<book>/refs/`),
shared by trailer, song and episode: a character who looks one way in the
trailer and another in episode one is two people.

## Binding is the whole point

Every shot showing a character carries that character's reference on
`ref_image_1`; `ShotSpec.ref_slots` emits every character first and the place
LAST, so a two-hander puts the location on `ref_image_3`, not `ref_image_2`.
`ShotSpec.unbound_cast()` asks what the JOB will carry, never what the prompt
says, and a plan with any unbound shot is refused: the 2026-08-25 trailer
rendered twelve good sheets and then every keyframe text-to-image, and nothing
ever told the model Holmes existed. **Never put an audio reference in a shot
where the face matters** — identity similarity collapses 0.886 → 0.088.

## Locations are rendered, not bound

`location_records` renders and returns: no read-back, no `distance`, no
ladder, no `unbound`. The half of refs.json that rides the LAST ref slot has
no gate — and usually no words. `describe_location` prefers
`analysis/locations/<id>.profile.physical` and falls through to the scene
slug; all 24 of Scarlet's location documents have no `profile.physical`, so
each of the 13 plates was made from a proper noun and the palette — "Criterion
Bar", "Utah", "Scotland Yard" — of which three are one landscape and four one
Victorian interior, unmeasured. Nor is there provenance:
`build_refs.generate` returns any file already at the path WITHOUT rendering
and `location_records` never asks for a fresh one - nor does `render_sheet` on
the attempt that binds - so a plate outlives a changed palette while refs.json
records the prompt that made nothing. **Check the words before the pixels:** a plate described only by
a place NAME binds nothing, and two names of one place are one plate.

**Choose refs by story-wide ranking, not by sampling scenes.** Sampling gave
*Jekyll and Hyde* a set with **no Henry Jekyll** — second in the book, silent
in the twelve scenes drawn — and spent a sheet on Enfield, who ranks sixth.
The cast is capped hard: `refs_needed(book, 12)` takes a count and ignores
it, `build_refs` slices `[:7]`. An 8th-ranked character gets no card, no
learning row and no place in `unbound` — its absence is recorded nowhere.

## Character collision

The failure mode when a book never describes anyone: seven Jekyll sheets came
back as seven near-identical Victorian gentlemen. Seeds do not fix it — the
prompts were identical, because Stevenson describes none of them. `card_for`'s
authority order, highest first:

1. **What the book STATES** — `portrait.stated`, then `canon.known_look`.
   `card.update(stated or {})` runs last and overwrites every slot below it.
2. **The role's costume** (`ROLE_ITEMS`) — DEAD. `card_for` ranks it above the
   book (`for_role[0] if for_role else from_book`), but `roles` reads
   `analysis/characters/*.json`'s `role`, which is a story RANK: protagonist 2,
   major 8, minor 4, group 3, unnamed 6 — 23 of 23 in Scarlet, no occupations.
   So `for_role` is always empty while `_allowed`'s `reserved` always fires: "a
   custodian helmet" and "a clerical black tie" leave every character's pool (a
   man's headgear is 11 of 14, and 12 only for a `policeman`) and reach nobody.
   Scarlet's two Scotland Yard men shipped in a black silk top hat and a straw
   boater, dressed by the rotation. The branch's only test,
   `test_a_policeman_may_have_the_helmet`, passes `role="policeman"` by hand —
   a string no analysis document produces. **A reservation with no holder is a
   deletion**: derive the occupation from the dossier or drop the reserved
   phrases from the pools. Until then the one path to a helmet is `_move`, the
   unpoliced rung — and `card_for` never appends a role-set slot to `asserted`,
   so even a live role would be owed by nobody.
3. **`book_match`**, then **the rotation** (`options[offset % len(options)]`,
   banded by `age_band`) ONLY where the book is silent. Appending an invention
   to a real description contradicts it — Hyde is "a small young man" and was
   handed "a short greying beard". The older three-layer design — `epithets()`,
   `costume_for()`, `distinguishing_marks()` — lives in
   `trailer_refs.described_as`, which `build_refs` calls and `step_02_refs`
   never imports: not on this path.

Put the SUBJECT FIRST in the prompt, before the style block: with the style
leading, the palette dominates and the description barely registers.
**Honest limit** — it separates servants and uniformed characters, and NOT
three well-dressed gentlemen: Krea 2's period prior beats the text.

## The sheet is read back, and judged three times

Every sheet goes to the local VLM (`studio/describe.py`) and comes back as a
trait card. Three questions, in this order:

1. **Was anything seen at all?** A card under `describe.VERIFIABLE_FROM` (5)
   traits is not a weak witness, it is a UNIVERSAL MATCH: `differences` skips
   any trait either card reads "unclear", so an unseen card measures 0.0 from
   every face alive. One in `bound` blinds three gates: its own (`verifiable`
   fails first, so `bind_one.gate` returns PASS before `disobeyed` or
   `same_look`); every LATER character's (it wins the argmin, `shared` with it
   is empty, `movable([])` is empty, and the row reads `accepted_as_written
   ... shares ` with nothing after "shares"); and every take in step 07
   (`reference_of` re-reads the sheet only when `identity.traits` is ABSENT,
   never when it is unusable, and `gate_take` asks `verifiable` of the TAKE,
   not the reference). Scarlet 2026-09-06: reads timed out at 00:19 and 00:46,
   then five characters bound on an empty `shares ` at 00:51 behind an unseen
   Holmes - zero comparisons - and every clip of the LEAD scored `similarity
   0.0, known 8, differs []`, eight shipped unchecked; 06:19-07:29 did it
   again. **Only a card that was SEEN may become a reference.** Similarity is
   `shared/(shared+differs)`, so 0.0 with a high `known` and an EMPTY
   `differs` is an empty reference, not a wrong face - the signature.
2. **Did the render obey its card?** Only on the traits the channel expresses
   - hair colour, hair length, facial hair, headgear (`distinguish.RELIABLE`).
   Complexion, build and age are DEAD on it - run 4's seven sheets read
   "fair" and "average" against seven different card phrases, and age follows
   the hair colour - and dead in the MEASUREMENT too: Scarlet's seven bound
   sheets read `fair` 7/7 and `average` 7/7, so neither ever enters
   `differences`, and figure and age are constant across the six MEN. FOUR
   traits can separate anyone, three of them discounting to `NEAR` (0.5) for a
   notch, while `DISTINCT_AT` asks 3. Nor are the four equal: recompute the 21
   pairs without headgear and 15 collide instead of 7, without facial hair 16.
   And only ONE of the four carries a COLOUR: `hair_colour` has eight values,
   while `facial_hair` (4) and `headgear` (7) name the KIND of an object and
   `hair_length` (4) its length — so "a close-trimmed grey beard", "a full dark
   beard" and "a long untrimmed beard" are ONE reading. Ferrier's card says
   "about sixty ... beard flecked and dashed with white"; his stored
   `identity.traits` read `middle-aged / dark brown / long / beard`, describing
   "a full beard ... dark brown, wavy hair ... a tall, dark fur hat", and
   `disobeyed` is empty and CORRECT — chestnut matches brown within a notch,
   beard matches beard, age is not RELIABLE. **Grey is only readable on the
   head**: `BANDED`'s old band buys its age with hair the reader sees (grey,
   white, bald) and with three facial-hair phrases whose "grey" never arrives.
   And half the design is invisible to the gate: `describe.TRAITS` has no key
   for `garment` or `neckwear`, two of the four `cast_card.TIER_ONE` slots the
   cast is BUILT on - so a pair separated by its coat and its collar measures
   zero distance and spends a rung rewriting hair instead. **Identity here IS
   the hat and the beard**, two objects that leave the frame - a shot with no
   hat and no jawline carries no identity, whatever `ref_image_1` holds. A
   disobedient render (Lestrade, run 6: card said walrus moustache, render
   read clean-shaven) is NOT a collision; it goes again as written on a new
   seed, because rewriting the card would move the character off the book for
   a fault of the renderer. But `figure` is in no RELIABLE, ADDED or
   `SLOT_TRAITS` list, so a woman rendered as a man is never `disobeyed`: the
   wrong sex ADDS 1.0 to `distance` (lucy~watson, lucy~hope 4.0 against a cast
   median of 3.0) and binds SOONER than a faithful sheet - the one trait whose
   disobedience this gate rewards. Check it by hand. And the gate is narrower
   than RELIABLE: `owed` counts only the traits of slots the BOOK asserted, so
   what the ROTATION invented is owed by nobody, and `added` covers only
   `neutral` slots, which exist only for a face `canon` knows. Scarlet's seven
   cards owe 14 traits of 28 - Holmes 4, Ferrier 3, Lucy 3, Gregson 2, Watson
   1, Hope 1, **Lestrade 0**, whose render may draw any face at all. On the
   book this subskill exists for - one that describes nobody, cast nobody
   knows - `asserted` and `neutral` are empty for everyone, `owed` and `added`
   are both [], and **`disobeyed` is IDENTICALLY EMPTY: gate 2 cannot fire
   once.** Built offline, seven silent cards (six distinct hair phrases, six
   distinct hats) handed one prior reading - man, middle-aged, dark brown,
   short, clean-shaven, bowler - come back from `adopt` as ONE card, "dark
   hair swept back / clean-shaven / a brown bowler hat", seven times,
   `disobeyed` [] seven times. That is Jekyll's seven Victorian gentlemen,
   regenerated on a CPU with no render. The narrowing was bought - run 7
   unbound the LEAD over an invented sandy hair: **an invented slot is not
   owed as its PHRASE, but it is owed as a DISTINCTION - the render may
   refuse the sandy hair, it may not draw a reading a bound card already
   holds**, and that failure is a reroll, not an unbind.
3. **Does it read as someone already bound?** Fewer than `DISTINCT_AT` seen
   traits apart is a collision, and `distinguish` moves exactly the shared
   slots - off ONE card, the closest, the only one the rung is handed, onto a
   phrase no character held at the START (`taken` snapshots the opening cards
   and is never updated as rungs move them), so a move is free to land on a
   bound card's CURRENT reading. g_lestrade, 2026-09-05 03:16-03:27: headgear
   moved off Watson read as Holmes's on the next rung, facial hair off Watson
   as Holmes's on the one after - watson, holmes, watson, holmes, four
   attempts, 10.7 min, unbound (again 2026-09-04 17:33). **A move must clear
   every bound card's reading in that slot, not the closest card's** - a
   three-rung ladder cannot outlast a two-body swap. **And a move is
   unpoliced.** `_move` walks the raw `cast_card.POOLS[slot]`, while every
   rule that made the opening card a PERSON — `ROLE_ITEMS`,
   `FEMALE_ONLY`, `BANDED` — lives in `card_for`/`_allowed`, which no rung
   calls. Called directly: off a neighbour's `cap`, a woman's first headgear
   rung is "a black silk top hat"; with the felt hat and the bare head spent,
   a man's is "a custodian helmet", reserved because it "is not a
   distinguishing feature, it is a different character"; off dark/medium a
   hair rung lands on "close-cropped grey hair" and the next on "a bald crown
   with grey at the temples" whatever the band — run 6's white-haired Holmes,
   one rung away, after `BANDED` was written to retire him. Nothing refuses
   it downstream: `disobeyed` never owes a moved slot; `same_look` asks only
   that the new face is not the neighbour's; no test asserts a sex, a role or a
   band survives a rung. Latent — Scarlet never climbed. **A rung may move
   only inside the pool the card was drawn from**, `_allowed(slot,
   BANDED[band][slot], gender, role)`, not the pool the module owns. A hair phrase carries a colour AND a length,
   so both move it. `unsaid` drops the book's sentence when a moved slot is
   one the book ASSERTS - but `movable` refuses to move an asserted slot at
   all, so the guard cannot fire for the case it was written for; it is a
   fossil of the cards that predated `asserted`, and it matches by a DIFFERENT
   rule (`book_match` with no slot, skipping `names_object`). The contradiction
   it names is live on the other writer: `followed` calls `adopt`, never
   `unsaid`, and `render_card` still appends
   the book's whole sentence. Measured: "hair like a raven's wing" names the
   object but overlaps no pool phrase, so the slot is NOT asserted, `adopt`
   rewrites it to "receding sandy hair", and the raven's wing stays in the
   prompt - two things told, and the model obeys whichever it likes.
   Aliasing is not a difference, and **the pool writes finer than the
   card reads**: 14 headgear phrases land on 7 readings (`cap` swallows four,
   `other hat` five), 12 facial-hair phrases on 4 (`beard` five, `moustache`
   four). Lucy's bonnet and Gregson's boater, two objects spent to separate
   two people, both read `other hat` in the shipped refs.json - as Ferrier's
   adopted felt hat does - and all three pairs measure exactly 3.0, clearing
   `DISTINCT_AT` by nothing. `_drawn` then returns `max(POOLS[slot], key=score)`, which ties to the
   bucket's FIRST phrase - and unlike `card_for` it is handed no `taken`.
   **It has shipped.** `cast_cards` gives Scarlet's seven SEVEN distinct hair
   phrases; refs.json carries FOUR. `render_card(adopt(card,
   identity.traits))` reproduces all seven shipped `physical` strings exactly:
   Watson off "fair hair parted in
   the middle" and Hope off "long black hair" onto Holmes's "dark hair swept
   back"; Lestrade off "thinning red hair" onto Ferrier's "wavy chestnut
   hair"; Ferrier off "a flat tweed cap" onto "a wide-brimmed felt hat", a hat
   no render drew - the reader's own prose says "a tall, dark fur hat". That
   `physical` is the `character=` line of every H3 take
   (`build_clips.take_values`), so three characters now enter every clip
   prompt with one head of hair. `distance` cannot see it: the sheets are
   still 7 different faces and the collapse is in TEXT. **`adopt` is the LAST
   writer of a card phrase and the only cast-blind one, and it can only move a
   card toward what the model already drew** - one way, toward the prior the
   cast card exists to escape. **Two people may not share a BUCKET, not a
   phrase - and every writer of a phrase must be handed `taken`, `_drawn`
   included.**

### When nothing may move, the collision BINDS - and that is the last gate

`movable` returns [] whenever every shared RELIABLE trait sits on a slot the
book asserted or invention left neutral; `bind_one.gate` then binds the sheet,
logs `accepted_as_written`, and climbs no rung. `cast_card.IDENTITY` is BOTH
identity slots (`facial_hair`, `hair`) and a `known` face's identity slots are
never invented, only left neutral - so on a cast the audience knows, `movable`
collapses to headgear, the slot the rotation separates best and therefore the
one rarely in `shared`. The accept is not the corner case the design priced;
it is the DEFAULT. Scarlet's final pass, 2026-09-07 01:44-01:46: watson~holmes
2.0, lestrade~holmes 2.0, ferrier~hope 1.0, lucy~lestrade 2.5,
gregson~lestrade 1.5 - five of the six characters that had anyone to be
compared to bound BELOW `DISTINCT_AT`, all on attempt 1 at 0.0 s, `unbound`
empty, `distinguish` fired zero times. Four came of canon.json leaving hair or
facial_hair blank; Ferrier's portrait asserted both. And `closest` is an
argmin, so a character is judged against ONE neighbour and clearing it says
nothing about the third: holmes~gregson 2.0 and lestrade~ferrier 2.5 collided
in that same refs.json, named in no row - 7 of the 21 pairs sit inside
`DISTINCT_AT`.

**Count the collisions in refs.json before step 03**: pairwise `distance` over
the stored `identity.traits` costs no GPU and is COMPLETE where the argmin is
not. It is the last look, too - step 07 reads every take against
`refs[char].identity.traits` (`reference_of`), so a take that draws Holmes
scores HIGH against Watson's accepted sheet. The rung left is not another
sheet, it is the PLAN: two characters that bound as written must not share a
frame or cut adjacent.

### The clock unbinds what the collision would have bound

`Climb.ask` gates every retry on the step budget and this ladder's terminal is
`unbound`, so a character whose FIRST sheet failed its gate and whose step has
less than one rung of clock left is DROPPED: `gate=budget action=unbound`,
attempt 1. Five of Scarlet's twelve step-02 `unbound` rows are that, not a face
— john_ferrier 2026-09-05 05:28 with 276.3 s left against a 290 s rung, thirteen
seconds short; gregson 05:35 at -141.1; ferrier, lucy and gregson 09-04 23:57 at
-272.4/-287.5/-302.5 under the old 90 s price. The sheet had already been
rendered and read; `climb` returns `Outcome(None)` and
`bind_one` throws the result away. That INVERTS this step's own policy: a
collision nothing can move is accepted and ships flagged (82 rows), while the
same defect plus a slow clock deletes the character — step 06's `unbound` marks
its beats bad, `substitute` puts somebody else in those shots, and if it was
the lead the plan fails `LEAD_SHARE_FLOOR`. **A sheet that exists on disk is
never unbound by the clock**: the budget terminal binds it flagged, as
`accepted_as_written` does. A colliding face costs a resemblance; a missing one
costs a character.

### The bind is a fixed point: a second pass renders nothing

`render_sheet` asks for a fresh file only from attempt 2 (`fresh = not (rung
is LADDER.rungs[0] and i == 0)`) and `generate` returns any file already at
the path. Every Scarlet bind lands on attempt 1, so all seven PNGs on disk are
dated 2026-09-04 21:55-23:30 while step 02 has logged rows through 2026-09-07
01:46 — ELEVEN more passes, nine of them the same five `accepted_as_written`
rows with the same `shares` lists, onto sheets nothing re-rendered. Their rows sit 15-30 s apart - one read
each - against 190-370 s for a sheet attempt, and cost no GPU, so nothing
escalates. The card is rebuilt from the current code every pass and the sheet
is not: a fix to a pool, a band or `portrait.py` cannot reach a face. **A bad cast is not repaired by re-running
step 02; the PNGs on disk are the state.** Delete `refs/characters/*.png`
first, or the pass is a five-minute no-op that ships the same collisions;
every change here since 09-05 is unverified on pixels.

### A woman has no spare bit, and two women are one woman

`card_for` forces `clean-shaven` on every woman and appends `facial_hair` to
`asserted`, so her movable set is at most hair and headgear — and `_allowed`
leaves her ONE garment, ONE neckwear and TWO headgear phrases that both read
`other hat`. Two women with no portrait, built straight through `cards_for`:
same facial hair, same dress, same lace collar, same headgear READING,
`distance` 2.5, `movable == ["headgear"]` — and no legal move in that slot
changes the reading, so the rung is a guaranteed no-op. Scarlet had one woman
and still bound her to Lestrade; the first book with two binds them as one
person, with no `disobeyed` row and nothing in `unbound`. The uncalled
textual gate does not save it either: `refuse_collision` run on that cast
PASSES, counting 4 text differences over slots the reader has no word for.
**The pool is the gate: where a slot's legal phrases all read the same, no
rung, no reread and no seed separates anyone** — the repair is more female
phrases, and a woman's hat that does not read `other hat`, never a rung.

### A read that outlives its timeout, and an engine that ignores the interrupt

A read past `describe.TIMEOUT` (600 s) is interrupted, logged
`accepted_on_timeout`, and the sheet binds unseen (`patiently`) - this is where
question 1's universal matches come from. Run 18: a read on a VRAM-full engine
ignored the interrupt and held the queue head, so every later read sat
`comfy.QUEUE_SECONDS` (7200 s) behind it before its own 600 s - five learnings
130 min apart, 11 h in step 02, budget -590 min at step 03. `comfy.stuck` now
verifies the interrupt and one `describe.Patience` per round remembers the
verdict: stuck, every later read returns unseen at once, 630 s for the round.
**That bounds a STUCK engine and nothing else.** When the interrupt DOES take,
`held_up` is False and a merely BUSY engine costs the same 7800 s, because
`wait_record` waits QUEUE_SECONDS for the job to leave the PENDING queue and
only THEN starts its 600 s clock. Scarlet's six reads of 2026-09-06/07,
14:43:58 through 01:34:30, sat 7806 s apart to under a second, every one an
all-unclear card: 130 min of a 6 h ceiling for a rung priced at 290 s. Tuning
TIMEOUT cannot move it; only abandoning a read still in the queue can.

## The book's own portrait comes first

`analysis/profile.physical` says "limited physical description" for Holmes,
Gregson and Lestrade, so run 6 INVENTED them: a white-haired, bearded Holmes
at forty. Doyle wrote the portraits; the analysis lost them. `portrait.py`
reads them back from `source/chapters/`: a candidate paragraph carries a look
word (`LOOK`) and names the character, or sits beside one that does, within
`SPAN` (3) chapters of the first appearance, at most `CAP` (12); the reasoning
model quotes VERBATIM sentences and fills six slots from those sentences only;
`verify` refuses any sentence not in the book, once with the violation quoted
back, then the portrait is silent and falls through to the dossier. Cached in
`refs/portraits.json`.

In the chapter of first appearance everything before the first naming is a
candidate too: Ferrier is "the traveller", gaunt and haggard, for fifty
paragraphs before a rescuer asks his name. Doyle describes, then names. Three
rules the extraction taught (Scarlet, 2026-09-04):

- An alias BY RELATION ("my companion", "his daughter") names whoever the
  speaker is with, not the character: Watson's portrait came back as Holmes's
  six feet and hawk nose. `RELATIONAL` aliases are not names.
- The analysis lists "Dr. Watson" and never "Watson"; Stamford says "Watson,
  you are as thin as a lath". A capitalised surname is a name.
- What the book states outranks the rotation (`portrait.stated` →
  `card_for(stated=)`): "flaxen-haired" beside the pool's "dark hair swept
  back" tells the model two things. A phrase the vocabulary reads whole is the
  slot as written ("long chestnut hair"); one read in part snaps onto the pool
  phrase that reads the same and shares the most words ("flaxen-haired" →
  "receding sandy hair"); one it cannot read states nothing ("frightened
  face"), because the fidelity gate reads every slot. A list ("fair face;
  cheek more ruddy") states its first readable phrase; a comma is the book's,
  not a list. Over `WORDS` (6) a phrase snaps onto the pool: a card is a list
  of short attributes. Build has no reading, kept as written.

## The sheet prompt ends in raw prose, and half of it is not a face

`card_for` keeps the whole description as `card['book']`, `render_card` appends
it verbatim, and `character_prompt` puts the SUBJECT FIRST — so on Ferrier 174
words of narrative lead the prompt and the framing ("head-and-shoulders ...
plain neutral mid-grey backdrop") arrives after them. Scarlet's seven bound
carry 555 words of book prose into their sheets: Ferrier's rifle, his "large
bundle tied up in a grey shawl" and "The man was dying"; Lucy's mustang and
"the unemotional Indians ... with their pelties"; a whole quoted line of
Stamford's dialogue in Watson's; and Gregson's entire portrait, a man "with a
notebook in his hand, who rushed forward and wrung my companion's hand". By
this module's founding rule a model draws OBJECTS, so a rifle, a mustang, a
notebook and a second pair of hands are what it draws — the plate side measured
it: "no people, no figures" returned a bar full of drinkers. And nothing counts
the faces afterwards: `describe_frames` takes `whom`, `describe` — the one step
02 calls — does not, and asserts "the one person in this image", so a sheet
that rendered two binds whichever the reader picked as `identity.traits`, the
reference every step-07 take is scored against.

`visual_description()` is NOT the repair, whatever it does on the shot path.
Measured on those seven it keeps 248 of the 555 words and keeps the wrong ones:
Ferrier's ONLY sentence naming his hair and beard is refused because `NARRATION`
matches "while" 250 characters into it, while "he leaned upon his weapon for
support" is kept; Lucy's "her cheek more ruddy" is dropped and her riding kept;
Gregson's notebook and second pair of hands survive whole. It earns its keep
only against a dossier that describes nothing — joseph_stangerson's 54 words
saying the dossier gives no description of him, plus "a deep stab wound in the
left side", go to 0. **The card's slots ARE the prompt; the book's sentence is
EVIDENCE for them, not a prompt.** `portrait.stated` has already taken every
slot it can read out of that sentence; what `render_card` appends after it is
the residue no gate will ever check.
