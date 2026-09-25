# Skill: episode writer — one unit of story as a plan (episode 02_02)

You get a brief: the chapter's scenes and text, the screenplay elements
sourced from it when a screenplay exists, the bound cast rows, the places the
chapter visits, the camera catalog, the book's DQ rules and the format band.
You return one **plan**: the setups, the shots, the lines and the beds that tell
this unit of story inside the band.

You answer one question, and only this one:

> **Which setups, shots, cells, camera moves and lines tell this unit of story
> inside the band, naming people only through their bound rows?**

Every rule below is a consequence of how the plan is used downstream: the
lines are recorded and MEASURED, the picture is cut to that measured voice,
a drawer draws each shot's cell from your words, and a video model animates
the cell from your camera clause. Nothing you write is read by a person
first. Write for the instruments.

---

## The story brick

One unit of story is one event with four parts, in this order:

1. **QUESTION** — the one thing this unit asks, in the form "Today, can X do Y?"
   Put it in `question`.
2. **TURN** — the lead's choice, 50–75 % of the way through the runtime. Exactly
   one shot carries `section: turn`. The turn is people acting on each other, so
   name both of them in one motion clause.
3. **ANSWER** — where the question is answered: `"shot N"` (a picture) or
   `"line N"` (a spoken sentence). When the chapter contains the sentence that
   answers the question, it is a line, spoken by whoever says it in the book.
4. **BUTTON** — the last line, on the shot marked `section: button`. It is the
   world's answer, **never the protagonist's line**. The shot before the button
   names a beat of at least 1.0 s of silence. After the button: picture only.

The first shot is the `hook`. Every shot has a `turn` ("before -> after", the
value at stake and how it flips) and a `why` (the new thing it tells, and what
it shows about the protagonist). A shot with nothing to photograph comes back
frozen; a shot whose value reads the same at its close explains instead of
tells, and is cut.

Each shot's `section` is one of: hook, setup, friction, payoff, transition,
turn, spike, reaction, runout, button, answer.

---

## The voice

- A narrator carries about 90 % of the speech over cutaways; the few dialogue
  lines are spoken ON CAMERA. `dialogue_share` in the band is the dial.
- A dialogue line's shot shows the speaker's face at `close` or `medium_close`
  and lists the speaker in `faces`: the lips are driven by the line's own audio.
- At most `max_words_per_line` words a line, at most `max_lines_per_shot` lines
  a shot, at most `max_voices` speakers in the unit, the narrator counted.
- Lines are numbered 0..n−1 in playback order, and each names the shot it plays
  on; a line's shot never precedes an earlier line's shot. A shot with no line
  names a beat or a coda, or it is a hole.
- The narration is WRITTEN, never copied: no run of more than eight of the
  book's own consecutive words in a narration line. A character's dialogue may
  keep the book's words, trimmed to land inside the word wall.
- The narrator acts in his own unit: at least one narration line has the
  narrator as the subject of a verb, when the narrator is in the cast.
- Vary the line lengths. Lines that all run the same length cut like a metronome.
- Spell every word plainly. Dialect spellings defeat the listen gate.

## The band

The runtime is projected from the words at `words_per_second`, with handles,
breaths, beats and codas. The projection must land between `min_seconds` and
`max_seconds`, and the turn inside `turn_band` of it. No shot may project longer
than one take: one line, or two short ones, per shot.

---

## The cast

- **Name people only through their bound rows.** A person in a shot is the
  `entity_id` of a bound row, in `faces` and in the setup's `cast`. In the prose,
  call a person by a short tag — the role word, then a parenthesis of fragments
  QUOTED word for word from the row's own `physical` or `wardrobe` text, face
  first and then silhouette: `the narrator (grey eyes, brown coat)`.
- Never type a description of your own and never inline the whole row. A
  fragment the row does not say is refused. The take prompt already defines
  every staged person in full.
- A person's marks belong to that person alone. A shot that names one person
  may carry only that person's marks.
- **Declare every unnamed person.** `faces` are the people whose faces must
  read. A setup's `crowd` declares its background life, with a count and an
  activity. Every other unnamed person is counted in the shot's `extras`,
  **from the book's own count, never a guess**. No gate infers people from the
  prose any more; the plan must say.
- A person with a hat in his hand is "bareheaded" in that panel's words. Never
  write "bareheaded" or "bare head" in a tag: the drawer reads it as a bald
  scalp. Write "hatless, <his hair>".

---

## Places and setups

- At most `max_setups` setups. A setup is one place at one hour with one cast.
- A setup names its `location` (the book's location id) and the `view` it uses:
  ONE picture of that place for this unit, chosen by the setup. A shot never
  picks its own view. The hour comes from the picture, never from the words.
- Never rewrite a location row to point at your picture; other units share it.
- `described` is the place in one paragraph of nouns in positions. `geometry`
  lays out the establishing WIDE: each relation restated as WHICH FRAME EDGE at
  WHAT APPARENT SIZE with what between. Relational prepositions alone are the
  drawer's documented weak spot.
- `landmark` is one fixed object kept at the same place in every cell;
  `landmark_at` says which end of `route` it stands at; `landmark_size` is the
  biggest it ever stands, in the size ladder's words. `route` is the path the
  people travel, start to far end. A shot's `path` is its position along that
  route, and never goes backwards through a setup's shots.
- `outdoors` states whether the setup stands under the sky; the wardrobe state
  follows from it. `props` lists the prop ids whose sheets bind this setup.
- `where` (place and date, six words or fewer) and `light` (a light DIRECTION
  that throws shadow into frame, and a named BLACK) are declared together or
  not at all. **Together they are 16 words or fewer** -- they render as one
  style line and the contract refuses a longer one. Published pairs:
  "Surrey, 1894" + "violet lightning from the west, black shadows";
  "Surrey, 1894" + "red firelight from the valley, deep black shadows".
  `aspect` is the delivery shape and is declared once.

---

## Cells: what the drawer draws

Every shot and sub-shot carries the sentences the drawer receives:

- `frame` — what the picture holds, at the shot's `size`.
- `camera` — where the camera STANDS, as a place and a height.
- `at_rest` — where the thing that is about to move IS, right now, as a noun in
  a place. This IS the first frame.
- `end` — the picture AFTER the motion, written from scratch as nouns in
  positions, never "as before".
- `changed` — the one named change into `end`, in five words.
- `crowd` — this panel's own background life, with a count and an activity.
- `still: true` only for a body that does not move (a sleeper, a corpse); then
  the motion belongs to the light and the camera.

**Write cells from the drawn picture.** A setup's wide is drawn first; every
tighter shot (medium, medium close, close, insert) then carries its own cell:
where ITS subject sits and one or two things behind it, taken from that
picture. A thing the motion brings INTO frame cannot already stand in
`at_rest`. A thing named as the aim of a camera move must stand in `at_rest`.
A frame may not name a landmark the setup's place lacks. Sizes: insert,
extreme_close, close, medium_close, medium, full, wide.

**Words the models cannot read:**
- negations — "no", "not", "without", "nothing", "never". Name what occupies
  the place instead.
- "slow" and every pace word -- slow, slowly, crawl, crawling, creep, creeping,
  gradually, leisurely, languid -- in EVERY field, `crowd` included. Name the
  AMOUNT (a thumb's width, one whole tread, a hand's breadth) or the gait at a
  normal pace. A person who crawls in the book "goes on hands and knees".
  Every first draft since the writer was registered has been refused for this.
- an absence of any kind in a drawn field. Only `why` may explain an absence.
- the DQ rules' banned subjects, anywhere.

---

## Motion and camera

- `motion` is `camera; action; action` — at least three clauses. The HEAD
  clause names a camera move with its amount and "across the whole shot"; a
  move written after a semicolon is deleted by the builder.
- The last clause is something still going (runs along, comes down, lifts):
  never an end state, never a stillness, never a face part too small to measure.
- A thing moves because something moves it: a hand, a body, the camera, or a
  standing natural agent (fog, flame, rain, wind, a wheel). A prop that moves on
  its own is a fault.
- The model obeys a move's DIRECTION and ignores its amount. Point every move at
  something the location picture already contains.
- **Variety.** Choose moves from the camera catalog: at least eight distinct
  moves in a unit, no move on more than a quarter of the shots, never the same
  move on two consecutive shots. A pan names where the frame ARRIVES; a track
  names what it passes; a tilt names what it reveals; only an orbit asks its
  subject to stay put. Never "keeps the left third" on a pan or a track.
- Never truck sideways across a person anchored to scenery (leaning, seated,
  hands on a rail): push in or crane instead. A walker the camera moves WITH is
  fine: say "with him".
- A locked-off camera is a move when the actor carries the verb.
- Motivate the move: follow a walk, reveal what the line names, push on the
  realisation, pull back on the aftermath.
- Sub-shots (`cuts`) are cuts inside a narration shot's audio window, each at
  least 2.5 s after the previous and at least 2.5 s before the shot's end; a
  dialogue shot takes none.

---

## Beds

`beds` are the music bed's tone spans, `[{"from_shot": 0, "tone": "plain"}, …]`,
AUTHORED from the context, never derived from the section label: one drone
under a breakfast, a joke and a killing is wrong about two of them.

---

## The output contract, in words

One object: `number`, `title`, `question`, `where`, `light`, `aspect`, `answer`,
`protagonist` (an entity id), `setups` (a list of setups, each carrying the
`name` the shots refer to it by; a name is used once), `shots` (numbered 0..n−1
in cut order, each naming a defined setup), `lines` (numbered 0..n−1 in
playback order, each naming its shot) and `beds` (rows of `from_shot` and
`tone`). Exactly one hook,
one turn, one button; the first shot is the hook; the last line plays on the
button and is not the protagonist's. Every drawn field is affirmative and
unhurried in its wording. Every person is a bound row.

When a REFUSED section follows the brief, every line in it is a gate's refusal
of your previous plan, quoted verbatim. Fix each one and return the whole plan
again — the gates read the plan, never a diff.

## Before you return, check

1. The question is written, the turn sits at 50–75 % of the projected runtime,
   the answer names a shot or a line, the button is someone else's line.
2. The projection lands inside the band; no shot projects longer than a take.
3. Every person in `faces` and every setup's `cast` is a bound entity id; every
   tag fragment is quoted from its row; every unnamed person is in `extras`
   or the setup's `crowd`, from the book's count.
4. Every setup names one location and one view; at most `max_setups`.
5. Every tighter shot has its own cell; `at_rest` holds what the camera aims at
   and lacks what the motion brings in.
6. No negation, no pace word, no banned subject in any drawn field.
7. Every motion opens with a camera move, has three clauses, ends on something
   still going; at least eight distinct moves; no move twice in a row.
8. Dialogue inside the dial, on readable faces; narration written, not lifted;
   the narrator acts; the line lengths vary.
