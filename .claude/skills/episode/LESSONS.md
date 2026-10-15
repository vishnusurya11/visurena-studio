# Lessons

Each rule in SKILL.md, with the measurement that made it. When a new failure
teaches something, add it here with its evidence, then put the rule in
SKILL.md.

## Process

- **The GPU sat at 6 % while the CPU measured the takes (2026-10-14).** Step 09 ran
  render all -> take_dq all -> content all -> eye -> retake -> again; every stage waited
  for the one before it, and a cure a CPU row had already proved (four frozen takes, a
  shuffling walker) waited for the VL read and the eye before anything rendered it. The
  owner: "it shouldn't wait, the GPU needs running". Two lanes now: renders back to back,
  each take's CPU check as it lands, a dq-borne cure queued behind the first renders as
  round 1. Replayed on that episode's own clock: 5455 s -> 4232 s (22 %), GPU idle
  1464 -> 302 s (`take_schedule_replay.py`). The earlier "keep the GPU fed" memory said the
  same and the code still serialised: a rule about time lives in the scheduler, not in a note.

- **A gate refusal must never choose a story fact (Jekyll ep01, 2026-10-13).** A
  third-person book had no narrator. G-SPEAKER refused `narrator` five rounds
  running and printed the cast as its menu; the writer took `henry_jekyll` -- the
  wrong man, the wrong person, an octave high -- and ep02 inherited him. Nobody
  decided it. Now the narrator is the BOOK's (`refs/narrator.json`, decided once
  before ep01; a third-person book takes the dedicated `narrator` voice row), step
  02 stops when it is unset, and no narration refusal lists the cast.
- **WotW filled every gap a new book exposed (Jekyll ep01, 2026-10-13).** The
  owner disliked all of it. The root under most causes: WotW's data and constants
  stood in where a fresh book had none -- a narrator never chosen, a 3.0 words/s
  guess (the voice measured 2.46, the plan projected 146 s and ran 173 s), a plan
  judge that rewards coverage over drama. A new book projects at the studio's
  measured 2.45. `docs/audit/2026-10-13_jekyll_ep01_review/DIAGNOSIS.md`.
- **Density, not the narration ratio, was the difference (Jekyll ep01).** 83 %
  narration matched WotW ep01's 82 %; what differed was 362 words against 266-307
  and 9.4 s of beats and codas against 18-20 s. G-PACE: <= 310 words, >= 15 s of
  pauses; over budget a line goes, never a breath.
- **A told tale lost its words to two good rules (Jekyll ep01).** The chapter is
  mostly Enfield telling a story; the dialogue dial (5-20 %) and the 8-word
  quote wall turned it into "Enfield said it was like watching some Juggernaut"
  in another man's mouth. A `tale` is the teller's own voice-over, the book's
  words kept, outside both rules.
- **Every empty shot needs an event (Jekyll ep01).** 7 of 27 shots were wind,
  leaves, pigeons and smoke (47 s); WotW's faceless shots are the flash, the
  cylinder, the lid turning. G-ACTION, measured 0-2 on every shipped plan.
- **Three rules forced a push on every exchange (Jekyll ep01).** No-repeat in
  G-MOVES, the ladder's frozen -> push, and the take builder's only example. 6 of
  8 dialogue shots pushed in. A held exchange is one unit now; a frozen dialogue
  take gets the actor's verb; G-TALK allows one travel (a pan is not a travel:
  WotW ep01 pans on all four spoken shots and was liked).
- **Replay the shipped plans before a gate lands (2026-10-13).** Two first drafts
  of the dialogue rules would have newly refused liked WotW plans: G-TALK counted
  pans, and the share divided by the shorter list (ep04 high_angle 0.25 -> 0.32).
  The CPU replay of all 41 shipped WotW and Scarlet plans found both.

- **A unit published outside the runner must settle from its publish record
  (2026-10-11).** Every WotW and Scarlet episode was on the channel, yet the board
  showed WotW ep01/02/05 queued (a runner could have rebuilt them), ep18 stale (its
  run lost the lease after step 11; the upload happened anyway) and Scarlet
  ep01/02/10-14 blocked on refs/04. Nothing settled a unit whose 13 step outputs and
  manifest predate the runner, and the backfill skipped them as ambiguous. The tick
  now settles an episode from youtube.json + an upload row with a video id
  (`tick.settle_published`), and a row written done carries no `blocked_on`.
- **The board read flags as open work; they are history (2026-10-11).** `flags`
  counts audit rows and never goes down, so 13 published WotW episodes sat in Needs
  you as `flagged` ("27 units, 23 done, 16 need you"), against the 2026-10-01 ruling
  that judge-signed terminals clear at publish. A flag needs the owner only while the
  unit is unpublished and unacknowledged (`views.flags_open`, one function for the
  inbox, the department and the dots). PLAN `APPROVE` with faults is not advisory:
  every such plan.verdict.json carries `flagged: true` (a kept-best terminal), so
  its chip stays `⚑n`.

- **A terminal is not a pass (ep12, 2026-09-26).** Every judged gate on ep12
  ended `keep_best` or `flag`, one at attempt 0 with the budget 2993 s overdrawn,
  one repeating a single fault 531 times -- and it was published as "the gates
  passed". The episode also had no sound effects (an empty cue list since
  2026-09-13), flat shouts (the reading clip was the emotion reference), a plan
  that dropped the chapter's title event, and five frozen shots the block-max
  meter could not see. `docs/audit/2026-09-26_ep12_root_cause.md`.

- **Gate the plan through the take-prompt battery before audio or pictures.**
  ep06 paid for three picture stages by skipping it. ep09 skipped it too, and
  seven over-long prompts and four banned props surfaced only at the takes
  stage (2026-09-22).
- **Build only what the episode needs.** References are made just in time, per
  episode. There are no bulk renders across the book.
- **The owner directs; do it with the tools.** When he says upload, it goes
  public. Never hand him a form or a task.
- **Do not stop until the deliverable is done.** Decide, go, and correct after
  his feedback.
- **A fix that changes nothing is not a fix.** Measure the artefact, not the
  tests. Green unit tests passed twice today on fixtures that did not match
  the real files: a shot keyed `at` where real placed shots use
  `t_start`/`t_end`, and a Setup built without its required fields.

- **Look at every contact sheet and every take strip; the gates do not see
  everything.** ep09's panel contact sheet showed a white gutter 97 px inside
  shot 14's edge, the narrator in his boater AND holding a hat (shots 11, 20),
  and an insert that was the place picture handed back; both panel gates
  passed all three. The take strips showed T02's fence sliding through the
  neighbour, which take_dq passed at 92.6 (2026-09-23).
- **A plan script writes plan.json only through `episode_home.write_plan`.**
  All 16 wrote unchecked; "nods slowly" replaced a good plan on disk and
  grids.py was the first to fail (2026-09-23).
- **Ten read-only audit agents found what a day of building had not**: the
  grid dressed every ep09 character from chapter 6 (a hard-coded chapter the
  lead had read past), a common-noun name that staged a 13-year-old's sheet
  for a stranger, and a "make public" step that checked nothing. Audit with
  fresh eyes after a heavy build (2026-09-23).

## Cast

- **Quote the hair when the chapter state is bareheaded (ep13, 2026-09-26).** The
  narrator's sheet wears a boater in every view, so the drawer had never seen his
  hair: five of ep13's first panels drew a bald man with a handlebar moustache.
  And never quote a row's colour word the sheet contradicts -- the curate's row
  says flaxen, his sheet is brown, and the board split between the two. The sheet
  binds every take; the tag must agree with it. No gate compares one character
  across panels; look at the whole board before the takes.

- **Describe the cast from its rows, never from memory.** ep07 shipped four
  characters that contradicted their rows. In ep09 all four newly written
  descriptions contradicted theirs; one milkman had sandy side-whiskers where
  his row gives a chestnut walrus moustache. `cast_refs.tag` now enforces it.
- **The words follow the picture when the book is silent.** Snippy's prompt
  asked for a moustache and the sheet came back clean-shaven. The picture is
  what gets staged.
- **Extraction rows can invent.** Two chapter-9 wardrobes gave gloves where
  the book gives bare hands, and the take lint refused four prompts.
- **Unique silhouettes.** Every character, walk-ons too, gets a colour, a dress
  and a hairline no one else in the episode has.
- **Staging is by declared cast.** Matching names by the last word of a display
  name staged "the neighbour's wife" for "the narrator's wife", and "the
  newspaper boy" for any boy, in six published takes.
- **One chapter's clothes at a time.** `refs.json` is rewritten per episode.
  Rows stamped for another chapter are refused.

- **Declared extras are the plan's claim; take the number from the book.**
  ep09 declared 6 for "a bevy of hussars ... two of them dismounted"; the
  take drew six riders and the two on foot, and the content gate failed it
  at 7 for 6. Declared 8 (2026-09-23).
- **A person with a hat in his hand must be called "bareheaded".** Tagged
  with the boater and holding it, the narrator was drawn with two (ep09 11,
  20). G-HAT refuses the clash in the plan now.
- **A common-noun name binds only in a definite phrase.** "the dismounted
  hussar" binds; "serge hussar jacket" and "a boy of sixteen" do not; "the
  narrator's wife" is the wife, not the narrator (2026-09-23).

- **Words lose to pixels, hardest on the face (WotW retro, 2026-10-10).** The
  narrator's grey hair and 16-day beard (ch22-27) were said in words beside the
  clean ep01 sheet: grey hair in 0-1 of ~24 ep26-27 panels, and 4 of 20 ep25
  panels were the sheet itself, suit, boater and all. Clothes-only changes (ep10
  soaked, ep13 scalded) mostly survived; face changes did not. A wardrobe
  promise needs a picture (`8c28bf6`, Scarlet) -- learned, lost on 09-18,
  relearned. The fix is a LOOK picture staged in grid and take, never more words.
- **Looks live on a story timeline (owner 2026-10-10).** `refs/looks.json`: one
  base look per character, every later look ONE hop from the base sheet (an
  identity edit for clothes, a fresh draw from the base prompt and seed for a
  face change), never an edit of an edit, never a composite (no head pasted
  back). Intervals are chapter AND scene: ch26 opens ragged and ends in the
  borrowed suit. `scripts/refs/looks_table.py` writes it once per book: from the
  dossier's costume plot when it has one (WotW), else from the script
  supervisor's `state_changes`, every quote found in its chapter at 0.85 --
  otherwise the next book gets one look for everyone.
- **A row never carries two heads.** The body holds no hair, beard or hat; the
  look's head leads the row. "Dark brown hair ... shaven" beside "ash-grey ...
  beard" let every gate that read the row allow both, and told H3 both.
- **Check what a gate compares against before trusting its silence.** The hair
  and beard checks compared the picture with a self-contradicting row, so they
  could never fire. They compare the staged look's MARKERS now.
- **"Clothes of <Picture k>" must be true.** The take's retention line copies
  the staged picture's clothes; with the clean sheet staged and ragged words,
  the costume changed mid-take (ep18, ep24, ep25 T0). Stage the look; the step-06
  lint refuses a person whose picture and words name two looks.
- **The panel IS the sheet.** Full-figure standing panels copied the staged
  sheet verbatim (pose, suit, boater). A look picture fixes the costume, not the
  copying: the panel can become the look picture standing front-on. Phase 2
  measures it (DINO/SSIM panel vs staged sheet, advisory); look at the board.

## Places

- **The hour comes from the reference, never the words.** This was measured
  twice on ep05.
- **The defining state goes first in a place's prompt.** The lawn's fire sat
  about 55 words in and was not drawn; redrawn with "ON FIRE" first, it was.
- **One picture per place per episode, chosen by the setup** (owner,
  2026-09-18). Two views of one observatory in one episode became two rooms.
  Still true; since 2026-10-10 a state of that place is one edit of its master
  (below).
- **Never rewrite the book's location rows for one episode.** Doing it for ep09
  moved ep03-ep08's Horsell Common into daylight. `Setup.view` is the choice.
- **Write cells from the drawn picture.** Cells written before drawing
  contradicted it: the cedar was on the wrong side, the arch opening in the
  wrong place.
- **Say a cell at the size of its shot** (G-SCALE). Wide cells in a close-up
  drew the place without the man; wide cells in a newspaper insert drew the
  whole platform.

- **A view drawn from words is a new room (WotW retro, 2026-10-10).** Since
  2026-09-22 every new view was a fresh Krea2 draw from that episode's words:
  17 drawn pictures of the narrator's house, the study six different rooms, the
  dining room three rooms under two ids. The 09-28 "views are drawn FROM the
  pinned picture" was ruled and never built. `places.py --new` drew fresh rooms
  too: a new id, a new row, a new picture. Now a place OWNS its member ids; a
  member's first picture is its master (`refs/places.json`); a framing or state
  view of a recurring place is its master, and the state is ONE 2511 edit of it
  (`place_state`, step 03_05); a view naming a new subject is a new side, drawn
  once and frozen. G-PLACE rewrites the plan in code; it never loops the writer.
- **One room under two ids is two rooms.** ep26's `narrators_dining_room` had no
  picture while ep07/ep11's dining room sat under `narrators_home`; step 03 drew
  a third. G-PLACE moves a member with nothing drawn onto the sibling view that
  already shows its room.
- **The pinned picture holds the state too.** ep26's villa reused the ep01 wide
  -- intact, sunny, neat -- while the prose asked for a forced door and red weed.
  The picture won. A state is a derived variant, never a sentence.
- **A rule written and never built is the commonest failure.** 09-28's derived
  views, the 09-16 Sage A/B, one-sheet-per-entity on the refs folder: each was
  text only. Land the code and its test with the rule, or the rule is a wish.
- **The plan gates, replayed on all 27 WotW plans (CPU, 2026-10-10):** G-LOOK 0
  rewrites; G-PLACE 0-2 a plan, 8 in all -- ep26 `narrators_dining_room` onto
  `narrators_home/dining_room_unlit_night`, ep27's fresh `reverse` onto the
  study master, six state views (`wide_empty`, `wide_restored_epilogue`, ...)
  onto their masters with the state kept. A first cut that also rewrote views
  naming a NEW subject (the dining room under the house id, a window view) made
  up to 5 a plan, all wrong: only a framing/hour/state view of a RECURRING place
  is its master. G-LOOK-WORDS: 7 advisories, refusing nothing. The GPU replay
  (look pictures staged in one ep25 and one ep27 grid; the villa and the study
  reverse as one-hop edits) is prepared and not yet run.

## Grids and panels

- **Qwen-Image: 1-3 references.** Identity goes first and the place last. Only
  the cast of the shots a grid owns goes in.
- **An unused LoadImage slot is a doll.** ComfyUI's example.png reached the
  encoder in every grid until `stage_only`.
- **Staging decides who appears, not words.** "A picture of the place alone"
  did not keep the only staged sheet out. Split the grid so a sheet goes only
  with its own shots.
- **The grid negative prompt is inert at CFG 1.0.** ComfyUI skips the
  unconditional branch, so every "no beard, no duplicates" there did nothing.
- **A fixed crop trim leaves gutters.** Measure the seam off (`seam_box`).

- **The grid prompt is v2: subject first, garments bound whole.** Same seeds on
  ep09: v1 cloned both leads at tea and drew the lawn's insert as a copy of its
  wide; v2 did neither. The clothing half of that A/B was judged against the
  wrong chapter (see docs/calibration/grid_prompt_ab.md, correction).
- **Lay grids out by shot size; hold head counts in a 1x1.** A mixed 2x2 drew
  a medium close as a full figure; eight seeds of a 2x2 drew 7-14 hussars
  where every 1x1 drew the declared count.
- **A grid is stale when what it would be drawn from changes** -- the prompt
  text and every staged picture's bytes -- not only its plan fields. The
  chapter-6 wardrobe could never have read as stale under the old check.
- **Crop a shaved panel square.** Resizing a 895x992 crop to a square
  stretched shot 14 11% into H3.

## Takes

- **H3 obeys direction, not amount.** 0 of 16 amounts were obeyed. Point every
  move at something already in the cell.
- **A take that froze after its own length changed wants its length back.**
  ep08 T16 went 51% frozen, then 75% on a fresh seed, then 10% with its coda
  restored.
- **A silent gap belongs to the silent shot inside it.** Trimming neighbours'
  codas closed the number and froze a take.
- **Mux lag follows length.** Shorten the take; a new seed does not help.
- **No last-frame pin.** It freezes or dissolves the segment.
- **No composed frame zero from sheets.** A panel cut from a multi-shot grid is
  allowed.

- **Aim every move at what the cell already holds (G-AIM).** In ep09's retake
  round 1, shots 14, 15 and 18 repeated their faults on fresh seeds: a tilt
  past the cell invented a lawn, a tilt from tiles the cell lacks opened
  elsewhere, a pan to an undrawn bridge invented a street.
- **A fault that repeats on a fresh seed is the plan's, not the seed's.**
- **Never truck sideways across a person anchored to the set (G-ANCHOR).** H3
  keeps the person where the cell put them and slides the scenery through
  them: ep09 T02, the neighbour leaning on the fence (owner: "ai slop, dq
  missed it"); also T10, ep07 T13, ep08 T14. Push in, crane or hold.
- **The take prompt says the place once too often.** T15, a 3-second rubble
  insert, opened 0.5 s on the burning lawn its prompt named three times.

## DQ

- **A gate that measured nothing has passed nothing.** "0/0 panels pass" read
  exactly like a clean run.
- **Thresholds carry the world they were fitted in.** Ink was fitted on night
  episodes and failed 11 clean daylight panels; the night control was picked by
  any "dark" in the prose.
- **Read whole words.** "compartment" was `men` and "surface" was a face. With
  no word boundaries the people check was off on about 80% of shots.
- **A crowd is declared, never inferred.**
- **A face counts at detector confidence 0.8 or more.** Smoke and steam scored
  up to 0.78; real faces scored 0.86 and above.
- **Look at what went public.** Four identical shopmen and a "NEWSPAPER BOY"
  headline passed every gate in ep08. The content gate now catches the first;
  OCR is needed for the second.
- **Say the place once.** ep09's 23 take prompts carried "The shot is inside
  this place" 23 times beside a staged panel; the median prompt fell from 558
  to 405 words when it went, and every prompt still passed the lint.
- **Read the reader strictly.** A cut-off answer, a "false" string and a
  subjects string each blinded a check silently; a missing named person never
  failed at all.
- **A guard can depend on state that moves.** The regenerate guard checked
  ep09's tags against refs.json, which holds only the chapter being made;
  binding chapter 10 broke ep09 until tags carried their own chapter.
- **`cut` reads brightness; a switch of picture is `jump`.** T15's second
  attempt changed pictures at cut 26.5 and passed at 74; the signature jump
  reads 0.16 against 0.83+ on every accepted take.
- **Judge a take by what is fixed in the world, not only by the frame.**
  `held` compares the face's travel with the scenery's: T02 1.01 over 1055 px
  of fence. Whether a held subject is a fault is the plan's call.
- **Calibrate before you wall.** A darkness wall would have failed 39 of 127
  accepted takes, and layout correlation 19 accepted pairs; neither was built.
- **"Bareheaded" in a cast row draws a bald man.** ep10's storm rows drew the
  narrator and the landlord with no hair until they said "Hatless, his dark
  brown hair plastered flat by rain".
- **A tight grid gets a short place.** Under the full place text a 1x1 medium
  close of the wife came back as the house front, five seeds running. With
  every shot tight, `brief_place` gives only the place's head and its light.
- **A gutter is pale and even.** The stacked check failed ep10 shot 1 on a
  door jamb (mean 106, std 14.7). Real gutters read 193-245 and std 1.5-4.6;
  counting only pale, flat lines took the worst clean panel from 0.748 to 0.020.
- **Lookalikes are counted among people.** Two tripods the book asks for read
  "0 people, 2 lookalikes" and failed ep10 shot 13; the count is capped by the
  people seen.
- **The same bad opening on every seed wants a head, not a fourth render.**
  ep10 T07 opened on 8 frames of a cart on the road on three seeds and T12 on
  11 frames of the machine sheet on two, and both were right to the end. A
  hand-written `heads.json` entry (narration shots only, and the take must
  still cover its shot) cuts past it, and `take_dq` now judges from the head.
- **A picture that contradicts the words makes H3 reconcile them, badly.**
  ep10 T18 asked for the landlord "lying back on the sand"; the panel stood
  him against the lane, and the take turned the whole world round his fixed
  face until sand filled the frame. Every gate passed it, and the face
  detector lost him at the end so no take-level measure could see it (a
  first-vs-last colour check read 0.51 on an accepted ep06 take: no wall).
  Caught upstream now: G-LAID in the plan and the posture question in the
  panel content gate.
- **Write the action, not a posture, for a person who moves.** ep11 shot 9's
  cell said the soldier "sits astride" the fence; the take rightly climbed
  over and walked, and the posture check failed it for not sitting. The book's
  own verb ("clambers over") asks for no posture.
- **A flat country needs its horizon said.** "A broad hillside set with flame"
  and "a valley" drew a far ridge that the reader called mountains in five
  ep11 shots across panels and takes; "level fields out to a low flat horizon"
  cleared every one.
- **Dark, distant subjects freeze under a push or a crane.** ep11 T03 (far
  tripods) and T08 (Mars) froze 51-100 % on two move types; a track past
  near tree tops and a tilt from the smoke read 10 % and 0 %.
- **A small dark subject under a truck freezes.** T07 read 52 % frozen as a
  sideways truck on a silhouette; as a crane-up the same shot read 26-37 %.
- **Run every new measure once on a real input before arming it.** ep12 was
  the first episode through the judged department; eight of its stops were
  measures built on fakes that crashed on the live ComfyUI or on real take
  records (docs/audit/2026-09-25_ep12_flow_findings.md, items 20-31).
- **A checker that found faults is not a crashed checker.** Both exit 1; a
  step must hand the first to its judge and ladder and refuse only the second
  (a verdict file written this run is the difference).
- **A head leak repeats on every seed and is cured by a head, not a render.**
  The step measure (`take_leak.step_leak`) finds it without an embedder: four
  published and unpublished heads read 0.85-1.17, nothing else above 0.62.
- **Dialogue a take cannot lip-sync goes over the shot as narration.** ep12
  T16's shout lagged 0.43-0.67 s on two lengths; voiced over the shot it needs
  no lip lock and the man still shouts on screen.
- **The delivered master is the Short, not the picture.** Every runtime wall
  capped the picture at 180 s while assemble appends the ~4.5 s title card and
  the 0.25 s chip after it; ep14 placed 177.9 s, delivered 182.6 s, and YouTube
  filed it as a regular video (hard requirement broken). The budget is derived
  once in `episode_spec` (`SHORT_WALL_S - TAIL_ALLOWANCE_S`), and the upload
  and public-flip doors read the FILE itself (`youtube_publish.file_refusals`:
  length AND 1:1), because `--override` waives `qc.passed` -- 2026-09-30.
- **Calibrate a content rule on the owner's judged episodes, by eye, per rule.**
  J5 (2026-10-11): the content gate refused 23/28 of the good ep05 and 0 of the
  bad ep08/09. By eye 21 of ep05's refusals were the rule, not the picture: a low
  far horizon read 'hills' (11), a twilight that asks for the last daylight read
  'day' (4), an over-the-shoulder near shoulder (2), crowds a pre-`extras` plan
  wrote in prose (5). Fixed those four (ep05 23 -> 6, ep07 5 -> 4, every eye-true
  fault kept); the rest is logged open. A gate's green on the bad episodes says
  their faults are not content faults, not that the gate works
  (`docs/audit/2026-10-10_continuity_retro/C3_content_gate.md`).

## The autopilot under the subscription (ep19-21, 2026-10-07/08)

ep19 and ep20 shipped public at $0 on the Claude Agent SDK; ep21 took a day of
fixes. Each lesson below cost at least one launch. Tracker rows A38-A74 in
`architecture/plan/2026-10-06_autopilot_build.md`.

- **The judge and the cure must measure with one ruler (A72).** ep21's battery
  judged ONE PER TAKE by the recorded voice (shots 0+1 = 7.88 s, packed); the
  holds cure projected the same pair at the series rate (8.29 s, clear) and grew
  nothing. Four ladder rounds, a brain park and a retry turned on 0.4 s. Every
  projection now reads `plan_gates.line_seconds`: the voice for a recorded line,
  the rate only for an unvoiced one. Before calling a fault "the writer's",
  compute its number both ways; if they disagree, the fault is the ruler.
- **A timeline is a run of the plan it was built FROM (A72).** A placed.json
  from another plan kept the aside from its free cure, and the ladder climbed an
  unsigned stray for an hour. `step_02.timeline_of_plan` reads through
  `load_placed`, the one door that knows staleness.
- **Every downstream rewrite of the plan is recorded (A70).** respot re-wrote
  plan.json on every run and the hole trim wrote unrecorded; the signature
  lapsed by links nobody recorded and step 02 RE-PLANNED a signed 31-shot plan
  over its voices and timeline. Writes after the signature go through
  `plan_provenance.record`, and respot writes only when a cut moved.
- **Every value the contract can sign, every consumer can say (A73).** The
  contract allows seven shot sizes; grids.py's size words and the cut clauses
  knew five, and the run died two grids in on `KeyError: 'full'`. A table keyed
  by a contract Literal is tested against `get_args` of that Literal.
- **A shadow is not a bar (A74).** The letterbox gate refused T27 and T30 HARD:
  a low-key cellar fades to black at the top and the bottom, rows at level 5-9
  with a row spread of 3.6-5.3 and no edge. A bar is flat to encoder noise (row
  spread <= 2.0) or ends at an edge (the picture rises >= 12 levels past it).
  Look at the strip of every take a HARD row refuses before believing the row.
- **A deferral's clean lines are not refusals (A71).** The table read
  `CAST BOUND : all bound` as cast_unbound (the substring) and spent the cure
  cap on the brain. A classifier matches the refusal's shape, never a word the
  clean line also holds.
- **A quiet master is lifted, a refused cut is not done (A61-A65).** -17.5 LUFS
  reached QC; `master_loudness.into_band` lifts the master into -15.5..-12.5
  with a limiter, and step 10 is not done while QC refused its master's sha.
- **A retry starts the clock and the take ladder's rounds over (A55-A57).** A
  terminal signed on a spent clock was read as done; `reset_since_verdict`
  re-judges it.
- **A YouTube refresh token dies every 7 days while the app is in Testing.**
  The table parks on `invalid_grant` with the mint command
  (`scripts/publish/youtube_auth.py`).
- **Patch text with a backslash goes through the Write tool, never a heredoc**,
  and a commit gates on pytest's exit code, never a pipe (three slips in 24 h).
- **A cache holds only while its measuring code holds (A75).** The take DQ
  cache keyed on the take's bytes alone, so the fixed letterbox measure never
  reached T27/T30 ("cached, bytes unchanged") and both went to the still
  terminal. `take_dq.measures_sha8` (the measuring modules' source) is part of
  the key now. Any cache of a verdict keys on the verdict's code too.
- **A content fault is the panel's only when the panel has it (A75).** Every
  take content fault was INPUT_BORNE, so ep21's T06 (a second, fair-haired man)
  and T14 (standing where the shot asks low) went to stills without one
  retake, though their panels passed content. A content fault on a clean panel
  is render-borne: one seed; a reproduced one goes to the terminal as before.
  Six of 32 shots would have shipped as stills; read the terminal's list before
  any publish.
- **A verdict is read where its cure lives, not at the last door (A76).** ep21's
  narrator measured as a split voice (ten pairs under their floors, eight calm
  pairs at 0.67-0.69 against 0.70) at 00:30; step 04 was "done" because the
  report EXISTED, and the upload door refused it fifteen hours and every
  picture later. The brain then blamed step 09 and parked. Step 04 now re-says
  the fewest lines covering every failing pair (greedy cover: l03, l07, l16)
  once, and the table routes the door's refusal to `redo 04`. Round one cured
  nine of ten pairs; the tenth (l07, l36) wanted l36, which round one's cover
  never chose, so the step takes up to two rounds, the second preferring lines
  not yet said again (A77).
- **Model ids come from the SDK's list, never by analogy (A76).** models.yaml
  and the brain asked for "claude-sonnet-5-5"; the CLI printed
  `unrecognized_model` on every call and the runs went on silently. Sonnet 5 is
  `claude-sonnet-5`; Opus 5.5 is `claude-opus-5-5`.
- **A round measures every take it touched, not only the one it named (A78).**
  The master eye retook T01; the renderer also re-rendered a stale T02, and the
  round measured only T01. T02 reached QC with no verdict, QC failed, and the
  brain parked the episode as a gate that gave up. `take_ladder.retake` now
  measures the named takes and every take `judged.unjudged_takes` lists.
- **A frozen-whole HARD row on a quiet insert is not a freeze (A78, open).**
  ep21 T02 -- wine spreading from the burst bottle, the camera drifting --
  read 74 % static with a longest still run of 0.46 s. A freeze a viewer sees
  holds; the gate should weigh the longest run, not the share, on an insert.
  Calibrate on the owner-judged episodes before changing it.
- **ep21's run, closed (2026-10-08 17:25Z, public https://youtu.be/LwGRFTce2jE,
  master_iter7, $0).** Seven masters; every stop after the plan was a ruler or
  a reader, not the picture: two rulers on one number (A72), a size word
  missing (A73), a shadow read as bars (A74), a cache under old code and a
  content fault blamed on its panel (A75), a voice verdict read only at the
  door (A76-A77), a retake that measured half of what it rendered (A78). The
  brain misread three of these stops as gates that gave up. Before trusting a
  park, read the refusing row yourself.
- **A line moved for lip-sync never lands on the next line (A79).** ep22's QC
  heard 'Come nearer. Dog. Good dog.': the dialogue 'Good dog!' was laid 1.97 s
  late to meet its take's soundtrack lag, on top of the next narration line in
  the same shot. Two voices at once is worse than a late mouth; `line_laid`
  now stops a moved line a breath before the next. A QC word-error on a line
  whose own recording reads clean is the mix, not the voice: find what else is
  sounding in its window before re-saying it.
- **ep22's run, closed (2026-10-08 21:3xZ, public https://youtu.be/VCvVvCcxlGE,
  master_iter3, $0).** Launched 17:30Z, public about four hours later; ONE stop
  (A79, two voices laid over each other) against ep21's twenty-two. The plan
  signed on its first climb, the voice held on its first check, every panel
  passed content on the first draw. The fixes of ep19-21 are the reason; the
  remaining time is renders and a full QC per master.
- **ep23's run, closed (2026-10-08 ~23:05Z, public https://youtu.be/DtC5WU2Gdeg,
  master_iter1, $0).** Un-parked at 21:32Z with a plan, voices and 19 takes
  already on disk; launched 21:35Z, public about 1.5 h later with ZERO stops
  and the first master signed. Two retake rounds cured every picture fault the
  router could reach. A parked episode keeps its work: resuming one costs only
  what is missing.
- **A text widened for one check widens every check that reads it (A80).**
  On 2026-10-07 I handed the panel and take content checks the SETUP's words so
  the pit-wall exemption could see a pit. The posture reader read them too:
  ep24's 'the London valley lies black' (and the capital 'London' taken for a
  person) asked every roof shot's narrator to lie down, and 'His face sits
  above it in the TOP third' asked a man to sit. Five of seven panel refusals
  were the reader's. Posture, cast, wear and lettering read the shot's own words
  (`panel_content.shot_words`); only the pit wall reads past `SETUP_MARK`; a
  body part is never the one who sits or lies.
- **A free cure runs beside a paid one, never instead of it (A81).** ep24 T02
  reached the master at score 0: 8 frames of the place plate before the panel,
  read as a hard jump. Its leak measure said a head cut covers it, but the
  router gives a take ONE cure and the move faults claimed it; the re-render
  leaked again. A covering leak now gets its head cut whatever else the take is
  routed to. And a QC refusal of a NEW master is a retry (the cut lifts a quiet
  cue, the take step measures what is unjudged); only the same bytes refused
  again go to the brain, which had parked every QC refusal as a gate that gave up.
- **A fix replayed against every guard downstream (A82).** A81's free head cut
  wrote ep24 T02 a trim; T02 is a DIALOGUE shot and the edit refuses any head on
  one (its wav is anchored in the take's first frames), so the whole master
  refused. The trim was also measured on a render the cure round replaced. The
  ladder never heads a dialogue take, a re-render clears its take's old head,
  and the edit drops a dialogue head with a note instead of refusing the
  episode. Before wiring a new cure, grep for the guards that read its output.
- **The cure must move what the gate measures (A83).** QC failed ep24 twice on
  one under-line cue (the spade, stem -23.6 against -20), and the lift skipped
  every under-line row because the MIX measure a voice masks never moves. The
  stem does move: an under-line cue is now lifted by its stem's deficit and
  judged against the level asked for (target less lift), like a cue with no
  baseline. Same shape as A72 -- a gate and its cure reading different numbers.
- **Open (A83): ep24 T02, a dialogue take, opens on 2-8 frames of plate on
  every render** (three renders, kept T02_head at score 0, lip-sync -0.34 s).
  A dialogue shot can neither be head-cut nor held as a still; the cure is a
  render that starts on its panel -- measure whether the panel-first prompt or
  a different staged first image stops the leak before the next dialogue insert.
- **A sound at the limiter is as loud as it may be (A84).** Lifted +4.6 dB, ep24's
  spade rose only 1.6: a transient bite peaks at the -3 dBTP cue limiter long
  before its momentary loudness meets the target. QC kept asking for 0.5 dB a
  limited stem cannot give. A stem pinned within 0.5 dB of the ceiling is heard.
  Before lifting a cue again, read its true peak.
- **One file, one reader (A85).** heads.json had ONE reader by design
  (`edit_gate.heads_in`: 'the cut and this gate can never disagree'); A82 dropped
  dialogue heads in assemble alone, the edit gate still expected T02 trimmed, and
  QC failed ep24 on a 20-frame offset. A rule about a shared file goes in its one
  reader. And a QC report, like a take's, holds only under the code that measured
  it (`step_11_qc.qc_measures_sha8`): the fixed rule could never reach a recut of
  the same bytes.
- **ep24's run, closed (2026-10-09 ~04:10Z, public https://youtu.be/oFtyf9Duqpc,
  master_iter6, $0).** Launched 23:00Z, about five hours to public. Pictures,
  voices and takes were done in under three; the rest was six stops in the edit
  and QC, every one a gate and its cure (or two readers of one file) measuring
  differently: setup words read as posture (A80), a covering leak never cut and a
  QC refusal sent to the brain (A81), a dialogue take trimmed (A82), an under-line
  cue never lifted (A83), a transient at the limiter (A84), the heads file read
  two ways and a stale QC FAIL reused (A85). Before the next episode: replay a
  fix through every reader of what it writes, and key every cached verdict on
  its code.
- **Cure the word, not the sentence (A86).** ep25 deferred on G-PHANTOM: the
  Regent's Park setup declares `fighting_machine` and its description twice
  says 'Martian fighting-machine' -- once in the setup's only sunset-light
  sentence. 'Martian' in a place text is a real risk (every take reads it as the
  creature), but deleting the sentence took the light with it. The free cure now
  drops a cast word that only qualifies a DECLARED prop and keeps the sentence;
  an undeclared machine still loses its sentence.
- **ep25's run, closed (2026-10-09 ~08:20Z, public https://youtu.be/mT3kdCUX6z0,
  master_iter1, $0).** Launched 04:15Z, about four hours to public; one plan
  deferral (A86, cured in code), every panel clean on content on the first draw,
  the first master signed. The edit and QC fixes of ep24 held: no stop after the
  takes.
- **Open (calibration): lettering the shot asks for.** ep25 T03 (an insert of a
  pocket watch and a labelled champagne bottle) and T04 (an empty shop street)
  failed 'text or lettering' on every render -- dial numerals, a label,
  shopfronts. `panel_content.lettering_expected` should count a watch or clock
  face, a labelled bottle and a street of shops as places lettering belongs;
  measure on the ep01-25 takes before changing it. keep_best shipped them.
- **Two gates can forbid every plan (A87).** ep26 deferred twice on G-STORY's
  wordless tail (6.09 against 6.0) and ONE PER TAKE (24, 25). With one wordless
  shot after a 2.2 s button line, the pair rule needs 8.3 s and the tail IS that
  pair less the speech: 6.1 s at least. No hold and no writer edit short of
  cutting the closing shot could pass both; the writer ran out of rungs. Proof by
  arithmetic, not feel: the tail limit now never sits below the pair rule's own
  demand when one wordless shot follows the button (`plan_gates.tail_limit`),
  ep10's 11.5 s still fails, and two wordless tail shots of one setup merge
  (`plan_cures.merge_silent_tail`). When a ladder fails on the same two rows
  every rung, check whether the rows can be satisfied together before cure.
- **Open: `tests/test_episode_tail.py::test_a_part_the_join_silently_drops_is_refused`
  is red on master before A87** (the title-card join); find the commit that
  broke it.
- **The plan is signed at the rate; the pictures are built on the voice (A88).**
  ep26's plan signed with every shot its own take at the series rate; recorded,
  shots 13 and 14 measured shorter, the packer joined them and step 06 refused
  the take's short second block. Step 05 now re-judges the pairs on the MEASURED
  timeline, runs the hold cure by the voice, records it, re-times and re-signs,
  and is not done while an unrendered timeline packs a pair. TAKE LENGTH went
  back to the rate (the renderer's own ruler): the voice made shots 4 and 17 0.4 s
  long, no hold shortens speech, and a voice-judged length would have refused the
  re-sign over takes the renderer makes. One ruler means the gate and ITS CURE
  agree, not that every gate reads the voice.
- **A cure that edits a plan runs the free cures after it (A89).** A88's hold cure
  split one of ep26's long shots into two with the same camera move, and the
  re-sign refused it. Any step that rewrites a signed plan runs `plan_repair
  --no-llm` before it re-signs.
- **A thing never takes a posture (A90).** ep26's panel check refused four
  correct panels: 'the dark dome of St Paul's sits small on the skyline' (the
  capital after 'St' read as a person) and 'their black shadows lying across the
  gravel road' (a participle counted whatever stood before it). Light, shadow,
  ground, buildings and sky never sit or lie (`panel_content.PART_SUBJECT`).
  The posture reader has now failed on three episodes running (ep24 setup words,
  ep24 'his face sits', ep26 things): read every posture refusal's own sentence
  before believing it.
- **A still is judged as a push, not as a take (A91).** QC failed ep26 on T06, a
  still: one frame step of 4.57 against SAME_FRAME 4.0, the take-vs-take limit.
  The steps rose smoothly through the push (median 1.68, top five 4.04-4.17);
  25 earlier stills read 1.02-3.75; another picture reads 32-63. A still's inside
  steps get `edit_gate.STILL_STEP` (twice SAME_FRAME, like STILL_FIRST).
- **ep26's run, closed (2026-10-09 ~15:25Z, public https://youtu.be/hd7gHnp-wRs,
  master_iter3, $0).** Launched 08:15Z, about seven hours to public, over the
  five-hour target: two plan deferrals on gates no plan could pass together
  (A87), a pair the voice packed after the plan signed (A88-A89), four panel
  refusals the posture reader invented (A90), a still judged as a take (A91).
  Every stop was a rule meeting a case its calibration never saw; none was the
  picture. The pictures and takes took under three hours.
- **A redo is chosen by the fault it cures (A92).** ep27's narrator split through
  one line, 'Yet I write on.' (mean 0.698 to his other lines, the lowest of ~60
  calm narrator lines over four episodes; length alone explains ~0.78). Two
  revoice rounds KEPT THE ORIGINAL because keep_best judged each try against the
  design clip, where the line already scored 0.71. A redo now keeps the try
  closer to the speaker's other lines in the episode (`say_lines.voice_fit`),
  and the split-voice cure has a third round.
- **The dry take build reads one ruler (A93).** After the voice, ep27's battery
  refused 'stamp 00:06 outside 00:00-00:05' on shots with no cuts: the dry build
  got voice-length shots and rate-length lines. It projects at the rate
  throughout (`plan_check.projected(voice=False)`), like TAKE LENGTH. The
  voice ruler is for the pairs and the holes the cures can move.
- **When no render cures a line, change the line's shape, not the gate (A94).**
  ep27's 'Yet I write on.' (2.46 s) stayed the narrator's outlier through three
  revoice rounds chosen by voice fit: every render of it sits further from his
  other lines than the original. It shares shot 1 with the next narration line,
  so the last cure joins them -- the book's same words, one measurable line --
  once, recorded (`plan_cures.join_line`, `step_04.join`). The recorder now
  reuses every recording whose text it already has (`say_lines.rekeyed`), so a
  join or an insertion re-says one line, not every line after it.
- **An omitted shot is out of every count (A97).** ep27's plan omits shots 6 and
  8; the timeline placed neither and the take builder rendered neither, and the
  cut refused 'no take for shots [6, 8]' because its take check walked every
  plan shot. The first episode since the rewrite to use `omit`: any check that
  counts plan shots must skip `episode.omit` (`assemble.shots_without_takes`).
- **A line QC hears wrong goes back to the record step (A98).** ep27's QC heard
  'Nights bring back the black powder.' as 'Night spring back...' (0.333): the
  voice ran 'bring' into the 's' before it, and the recording had already passed
  the ear narrowly as 'Nights spring back'. A recut reuses the audio and a re-say
  kept by voice fit cannot target clarity. Step 04 now stays open while the last
  QC report holds a misheard line it has not said again, re-says it once with
  `--clear` (the try the ear hears most clearly wins), and the chain re-times and
  re-renders only what moved.
- **Again: a heredoc ate a backslash (A98).** A `\` continuation inside a python
  heredoc patch landed as a literal `
` and the module would not import. The
  rule stands without exception: replacement text with a backslash goes through
  Write or Edit.
- **A measured overrun is the holds' to give back (A99, Jekyll ep01, 2026-10-13).**
  A new book has no measured narrator: the plan signed at 148 s at 3.0 words/s,
  the voice ran at ~2.5 and the timeline measured 174.8 s against 174 -- 0.8 s
  over, with 10.6 s of holds and a 5 s wordless hole in the runout. Three faults
  met. (1) No cure answered a measured overrun: `trim_measured_holes` answers a
  hole over the wall, and the plan's `holds` cure (where 'projects to ... an
  episode is' routes) only LIFTS the floor. (2) `timeline.py` writes placed.json
  BEFORE its band check, so the resume found a fresh timeline and SKIPPED step 05
  into the grids on a 174.8 s picture. (3) The autopilot's brain ordered a full
  step-02 redo for a sub-second overrun -- a replan and re-record where a free
  shave sufficed; the redo then did nothing but walk past the skipped step 05.
  Step 05 now refuses `done` over the budget (`step_05.overrun`) and, on the
  overrun, shaves holds across every shot to MAX_SECONDS less
  `plan_cures.RUNTIME_MARGIN_S`, largest first, floors kept, recorded, one
  re-time, battery, judge re-sign (`trim_measured_runtime`, `fit_runtime`). Read
  a timeline refusal's numbers before any redo: an overrun smaller than the
  holds is never the writer's.
- **ep27's run, closed -- and the book (2026-10-10 23:12Z, public
  https://youtu.be/Z4VNwQJ_5NI, master_iter2, $0).** The last chapter. Its stops:
  a narrator split through one short line, cured only by joining it to its
  neighbour (A92-A94); a dry take build reading two rulers (A93); the GPU falling
  off the bus (A95, an owner reboot); a locked database (A96); the first `omit`
  since the rewrite (A97); a line QC heard wrong (A98). With it the autopilot
  reported COMPLETE: 27 of 27 chapters public, nothing parked.
- **The book as one video (2026-10-10).** `scripts/publish/book_compilation.py`
  joins every published master (by ledger sha8) by stream copy -- the masters
  share 1536x1536, 24 fps, H.264, 48 kHz stereo -- and uploads one regular video
  whose description OPENS with a chapter per episode from 0:00. It refuses while
  any chapter is unpublished.
- **Title first in the book video (owner 2026-10-11).** A chapter is two videos:
  its title (the animated card) and its main video. The Short stays main + title
  + black chip. The book video runs TITLE FIRST, then main, per chapter. Both
  pieces are cut out of the shipped Short by frame: main = Short − card − chip
  frames, title = the card's range (checked on WotW ep01: frame 3711 is the
  card's first frame, 3818 the black). They land in `compilation/chapters/` and
  are re-cut only when their frame count is wrong. The first WotW book video
  had the card at each chapter's END; the owner caught it on the channel.
- **The book's main title, first runs (2026-10-11).** WotW and Scarlet book videos
  are live (HSn8Gl7mnyA, IDtuFR_VAqo); the old WotW one is private. What the
  first renders taught:
  - The sharpest faceless shot is not a trailer shot: the cold open picked a
    gate, a sawmill and a railway. The VLM now scores drama on a shortlist.
  - ACE-Step stings open ON their hit (0.68 s): lay the hit on the black and put a
    riser under the cold open; one loudnorm pass on 7 s lands 1.5 dB short.
  - No fixed scene threshold finds a card: WotW ep01's dark-to-dark cut scored
    0.24. The card is the BIGGEST change in the 240 frames before the black.
  - A yes/no "is anyone drawn twice?" passed two Holmeses. LIST then judge in
    code, and give the reader a worked example, or it echoes the template.
  - A thumbnail prompt asking for "both figures" drew Holmes twice on three
    seeds; the vetted hero plate over a title band is the fallback.
  - A portrait Short padded into the band shows its bars: cold open from square
    Shorts only.
  - Two runs on one folder: a "detached" `&` job survived its shell and raced
    the upload run. Start long jobs only as tracked background tasks.
  - Keep the GPU fed: the Scarlet title could render while WotW's CPU checks ran.

- **The book-video retro (owner 2026-10-11: "figure out all our issues ... find a way
  to fix it").** WotW and Scarlet were not re-made (the live videos are HSn8Gl7mnyA,
  HOLHQEN0Gic). Every fault is now a check:
  - **The card was guessed wrong four times** (WotW ep06/10/20, Scarlet ep12: seconds
    of chapter inside the "title"). Assemble now RECORDS each master's card by sha8
    (`cut/master_layout.json`). Measuring is only for older Shorts, at the change
    where the card's own length puts it.
  - **The upload door** (`book_compilation.door`) refuses a title piece longer than its
    card, a wrong running order, or a refused G-BOOKTITLE. It writes
    `compilation/door_sheet.png` (each chapter's title, then its last frame).
  - **The book's look:** Scarlet got WotW's painted LoRA style on its main title,
    thumbnail AND (latent) chapter-card art. Every picture is routed by the book's
    look (`plate_request`, `lead_for`). A VLM cannot judge it: it called a photoreal
    plate a "3D render".
  - **A person drawn twice is listed, then judged in code,** with a worked example.
    Yes/no passed two Holmeses, and a bare template was echoed back.
  - **Run safety:** a per-book lock, a line-buffered log line per chapter, the key-art
    writer falls back to the logline when the SDK hangs, a read-back failure is a flag
    not a crash, and every module must compile (heredoc mangling).
  - **The GPU is fed:** the main title's GPU half runs while the CPU cuts chapters.
    Frame counts are read off packets (215 ms), and the scene and black passes decode
    on CUDA.
  - **Another session shares this checkout:** never stash/checkout/-A, and commit
    your own paths early.
- **The continuity acceptance replay, re-run (2026-10-11, after c4112e7 and 08ebcb0).**
  Bar: the look's hair colour AND facial hair on >= 80 % of the replayed panels the
  person is in.
  - **ep27 study_table (epilogue_home): 3/3 = 100 % PASS** (shipped 0/3). The ran grid
    staged `epilogue_home`, and the eye agrees: ash-grey hair, grey moustache, boater,
    herringbone suit. The shipped panels had dark hair and a brown moustache.
  - **ep25 fulham_road (ragged_greyed): 0/3 FAIL.** The grid DID stage the look (ran
    graph: `ragged_greyed_*.png`). It shows a felt hat on 2/3 panels, grey hair on
    2/3 and the torn shirt on 3/3; shipped had a boater and suit. The miss is the
    **beard**: the look picture has none. LOOK-STATE refused it on all three draws
    (facial_hair none vs beard), and the climb ended keep_best flagged. The
    fault is upstream of the grid: a fresh Krea2 draw drops "sixteen days of beard".
  - **The judge was blind until 08ebcb0.** The Qwen3-VL caption wraps its JSON as a
    list holding one string of JSON, so every LOOK-STATE read was 'unread'. The
    unread verdict was advisory, so the first replay PASSED a look nobody had read,
    and both arms scored 0/3 on reads that never happened. An unread head now
    refuses, and the replay counts unread panels apart. A judge that reads nothing
    must say so loudly.
  - **LOOK-STATE does not see ghost faces.** ragged_greyed.png has two faces painted
    into the trouser texture. Its closed vocabulary (hat, hair, beard, top, dirt) has
    no word for it, and it passed those markers. The look picture needs a stray-face
    check (face count on the crop, 1 expected) before it is staged.
- **Cycle 1 of the continuity retro (2026-10-11, `docs/audit/2026-10-10_continuity_retro/C1_verdict.md`).**
  - **A pixel wall in a chaotic sampler measures the draw, not the quality.** 28 dB
    would refuse today's shipped 8-step (A1) on all 6 shots: an int8 rounding error
    travels through the sampler into a new draw. Judge numerics with a same-draw
    margin over the seed-to-seed distance (>= 3 dB, it classifies, never refuses),
    identity against the control's own seed spread (per shot >= -2 sigma_seed,
    dialogue mean >= -0.02), clones against the production take's own count, and
    invented speech against the control's own tail on that seed
    (`scripts/bench/rulers.judge_arm`).
  - **Qwen draws its own grid count on a strip.** A 2:1 canvas came back as a 2x2 of
    four copies (every 2x1 seam a row at 50 %), a 3:1 as four columns (seams at the
    4-column gutters). 15/201 strip panels seamed against 0/198 square-ish (Fisher
    p = 4.7e-5). A seed bump never cured it (ep22 .99/.98/.98, ep14 nine redraws).
    Grids are 1x1 or 2x2 only (G-GRID-SHAPE). Cost on the ep19-27 plans: +1..7 grid
    calls per episode (mean +4.4) at the same megapixels.
  - **keep_best keeps the last draw, not the best.** `supersede()` moves every earlier
    draw to `superseded/`, clean ones included (ep20 copper v1 and v4 read clean,
    the shipped draw stacked). A best-of-draws restore is NOT built: a redrawn anchor
    re-cuts the room and its siblings are redrawn to stage the new room (one-room
    ruling), so an older sibling would stage the old room.
  - **A seam survives a seed bump; isolate it once, then stage no panel.** The seam
    rung isolates a seam/stacked shot into its own 1x1 outside the cap (1x1s carried
    0/92 seams). A shot still seamed renders refs-only (owner ruling 2026-10-11): a
    staged doubled cell is a duplicate-figure source, so the take gets the sheets,
    the place and the words, ships, and is flagged in the audit sheet.
  - **Krea2 + Cinematic draws a beard only from a plain "full ... beard" noun** (2/2:
    captain, Ogilvy). It drops duration, stubble and qualified wording (0/7, including
    ragged_greyed's "sixteen days of grey-brown beard" on 3/3 draws). The closed
    `beard` marker now writes the drawn phrase (`looks.drawn_face`), and the grid tags
    carry it too (ep25: 4/12 one-face tags lacked any beard word).
  - **LOOK DECISION for the owner to veto (2026-10-11, not ruled):** the narrator's
    ragged_greyed look is drawn as "a full short grey-brown beard covering the jaw, chin
    and upper lip, sixteen days grown". Faithful to the book: sixteen days of growth is
    a short full beard, not stubble. Only the duration wording is rewritten (1 look in
    WotW + Scarlet); Lord Garrick's chin beard with a shaven upper lip, Lavelle's
    imperial and every `stubble` marker keep the book's words. No masked beard inpaint.
  - **H3 continues the line into a digitally silent guide tail.** Every invented word
    echoes the line's last word ("Indeed.", "Heed.", "Moving!"). Audio and mouth are
    one sample: a loud tail means a moving or open mouth, a quiet tail a shut one. 2 of
    154 shipped dialogue takes speak into silence (wotw ep10/T21, ep26/T25 -- left as
    shipped, known faults, owner 2026-10-11). G-TAIL now fails them; cure one reseed.
  - **A guide overwritten in `ComfyUI/input` makes the speech check lie.** 5 early-Scarlet
    takes staged unhashed `voice_NN.wav` names a later episode overwrote; their guides
    end 1.2-3.2 s off placed.json and read "invented" falsely. G-TAIL reads such a guide
    UNMEASURABLE (speech end > 1.0 s off placed.json), never invented.
  - **A blank head makes a blank judge.** Jekyll's and Hyde's dossiers name no hair,
    beard, age or hat, so every head marker would be blank and LOOK-STATE would pass
    anything. A NEW look table now refuses such a character ("head unauthored",
    `look_timeline.head_refusal`); existing tables are not re-judged. WotW: 0/47
    refused. Scarlet has no table, but 9/15 of its bound dossiers (Holmes included)
    author no head in `physical` -- a Scarlet table would be refused until they do.
  - **The cycle-1 GPU bench (69 of 90 min, `docs/audit/2026-10-10_continuity_retro/CYCLE_1.md`).**
    - **A distilled LoRA is run on its published grid -- and that is still not enough.**
      The ref2v 4-step is `simple`@12/3 (t 1000/750/500/250); `beta` puts two calls off
      it. G1 (A3 on the authors' grid) was benched: the S3 frogs at 50 % are smeared on
      seed 1 and gone on seed 2 (the 8-step keeps five). G1 is OUT; the 4-step stays
      unwired. Read the authors' graph before ruling a schedule, and then still bench it.
    - **CK int8 attention on the 8-step BASE is the speed step.** Same draw (PSNR 22.9-33.9
      vs seed-to-seed 13.1-22.2), identity within -2 sigma_seed (sigma .021; worst S4
      -.030), no invented word on S4 x 2 seeds, sampling 39-45 % faster, face sheets
      indistinguishable. Adopted for NARRATION takes (`takes_r2v.NARRATION_BASE`);
      dialogue waits for D1/D2 on a second seed.
    - **The beard comes back with the drawable noun:** ragged_greyed fresh draws carry a
      grey-brown beard on 3/3 (0/3 before), LOOK-STATE reads `beard` on 3/3. LOOK-STATE
      then refused all three on headwear: it reads a battered brown felt hat as
      `other_hat` -- a vocabulary fault of the judge, not the picture (cycle 2).
    - **Ghost faces are the USDU tile pass.** Same prompt and seed: the 1x decode has no
      face in the trousers, the 2x USDU output paints one on the right thigh. Cause (b);
      nothing built (n = 1 prompt).
    - **No strips, no seams:** 13 seamed shots re-laid as 1x1/2x2 and redrawn: 0 seams,
      0 stacked (the instrument reads 1.0 + a seam on the shipped panels).
    - **Room tone in the guide tail: inconclusive.** The zero tail invented no word on
      S4 seeds 1/3/4 either (two tails sounded, no word), so the A/B cannot rule.
- **Cycle 2 of the continuity retro (2026-10-11, `docs/audit/2026-10-10_continuity_retro/C2_verdict.md`).**
  - **A rung that throws history away rarely wins (commit 3).** Over 40 terminal plan
    climbs (ep17-27), fresh_brief produced the kept draft once, and that one was an
    anomaly (ep18 14:21, [3, 3, 1, 58 -> 58]). 547 of 849 rung minutes ran after the
    kept draft already existed. A rung is kept only while it is the source of kept
    drafts. The ladder is improve x 2 -> model_tier -> terminal.
    WATCH (next 3 episodes): log model_tier's input fault count -- it now edits
    improve2's draft with the whole merged history, where it used to edit fresh_brief's.
  - **The same faults are not the same outcome (refuted fix, not built).** 5 of 10
    re-climbs that started on the previous climb's fault count made progress (ep23
    40->17, ep25 36->13). A memory that skips them parks the series. Remember only
    "no progress twice" (cycle 3, H1).
  - **A reader's hat is a family, a writer's hat is a word (commits 4-5).** The VL reads
    a felt hat as `other_hat` 7/8 times; the judge compares families (brimmed =
    {felt_hat, other_hat}). The writer's table maps the book's words exactly (top hat,
    billycock, pork-pie, straw hat): re-deriving the 61 WotW looks moved exactly 8.
    "felt" is also a verb -- "he felt for his hat" must not read felt_hat (at most one
    word between "felt" and "hat"; "he felt his hat" still does). The READER's free
    "straw hat" still reads `boater` (`READER_HEADWEAR`): it is unmeasured, and as
    the brimmed other_hat it would hide the shipped ep25 straw-on-felt fault.
  - **A fixture typed by hand drifts from the contract (commit 6).** `appearances` is a
    count in every real dossier; the test's list hid a crash (`dossier_text`) on the
    only writer path a new book takes. Fixtures are built from a real dossier's keys.
    Scarlet replay (scratch only, worst-case headless writer draft): 26/26 rows built,
    0 refused; Jekyll and Hyde still refused. Two precision faults seen in that replay
    and NOT fixed: a negated dossier sentence ("does not specify hair, eye colour ...")
    parses as an authored hair layer (Watson's hair marker blank), and "grey eyes under
    a tangle of sandy hair" reads hair `grey` (Wiggins).
  - **A tight size is drawn a size wide (commit 8).** 84 planned MCU panels over 16
    episodes (ep12-27) have a median face_h of 0.208, against about 0.30 that the cut
    words ask for; 78 % are under 0.26. A crop to plan buys the pixels but cuts planned
    props (coins, bag, newspaper), so it is not a cure. G-FRAME records it, advisory.
  - **A same-man redraw on one row is a different man (commit 9).** Brigham Young ep08
    against ep10 has a head cosine of 0.16-0.23, near the cross-person median; Hope
    ep07 against ep09-14 0.43-0.46. A separate `_young` row holds about 0.6, same-man
    versions 0.80-0.96. G-LINEAGE writes the audit line; a surname is not an age-up
    marker (`brigham_young` is named "Brigham Young").
  - **A memo keyed on the master saves nothing when every rerun follows a recut (commit 10,
    dropped).** QC reran 7x on ep20, ep21 and ep24, but 20 of 21 reruns followed an
    assemble that wrote new master bytes (timing.jsonl, md5 of master_iterN); the one
    identical pair (ep20) was already re-measured for a code change. step 11 already
    reuses a report on identical bytes + identical measuring code. Read where the time
    went before building the cache.
  - **The cycle-2 GPU bench (75 of 90 min, `docs/audit/2026-10-10_continuity_retro/CYCLE_2.md`).**
    - **One prompt per tile paints faces (block 1).** USDU hands every 1024 tile the full
      subject prompt; a trouser or backdrop tile paints the subject's face. The narrator
      base sheet replayed from its own embedded graph is BIT-IDENTICAL to the shipped
      sheet.png (PSNR 99): the 1x decode is clean, the 2x has the backdrop face between
      figures 1 and 2 -- staged in ep18-27. A style-only tile prompt (`_neutraltile`)
      removed both ghosts (narrator backdrop, ragged_greyed thigh) and kept trouser
      sharpness (0.96-1.06 of today's), but its head facenet vs the 1x is 0.001-0.015
      lower and it adds colour streaks to the tweed. An owner ruling (look), not adopted.
      A sheet's own PNG carries its graph: replay it from there.
    - **A test with no case that can fail it proves nothing (block 2).** CK8 for dialogue
      was judged on two takes whose control tail sounds: on ep10/T21 CK8 says "keep
      moving" where A1 says "moving"; on ep15/T21 its lower-face tail ratio is 1.14 vs
      A1 0.94-0.97; banding mean rose (+.008/+.013). Dialogue stays on BASE. The identity
      sign tally is 4/8 negative: "CK costs ~.01 facenet" is NOT supported.
    - **Fewer words do not draw a closer face (block 3).** Dropping the geometry clause
      moved the median MCU face_h .189 -> .196, CLOSE-UP words -> .226 (bar .25), and
      the close words changed costumes (ep23 suit -> torn shirt, ep14 satchel gone). A
      2048 canvas drew SMALLER faces (.150-.178 vs .169-.208). Every redraw from the
      shipped text and staged bytes was bit-identical (ep16 s13, ep14 s22/s24).
    - **992 changed a look (block 4).** S6 at 992 drew the narrator grey-haired and
      grey-moustached (identity .489 vs .730 at 768); D1/D2 held (.823/.891). Sampling
      2.2-2.4x. Owner ruling, on the sheet.
    - **Prewarm does not survive the queue (block 5).** Three prewarm prompts queued
      before three takes left 11.5-13.7 s of overhead per take (bar 4 s, control
      13.5-16.4 s); frames bit-identical. Only the last prompt's outputs stay cached.
  - **The cycle-3 build (`docs/audit/2026-10-10_continuity_retro/CYCLE_3.md`, C3_verdict §5).**
    - **The best draft goes to disk every rung (commit 1).** A killed climb restarted from
      the last draft 111 times out of 329 rung verdicts when a better one existed (ep17
      1 -> 38, ep22 35 -> 46, ep26 5 -> 6). plan.climb.json holds the best; restore the
      draft, re-judge it, never trust an old verdict on moved code.
    - **A cheap fail before an expensive one (commit 2).** 10/14 QC failures were loudness,
      cue and edit rows that take seconds (ep27: every cheap row <= 17 s). Whisper runs
      only on a master that can still pass. An unmeasured line is not a heard line.
    - **The clock you budget against is not the clock you spend (commit 3).** 398 of
      3,499 machine-min over ep19-27 sat in killed steps the step clock never logged.
      Time the process with a heartbeat (studio/run_clock.py), not the step on exit.
    - **A reset clock is no clock (commit 4).** 67 retries each opened a fresh 5 h (all 4
      over_budget parks were retried into a new ceiling). A ceiling binds only if nothing
      can zero it: `retry` stamps `attempt_at`, `spent_before` never reads it.
    - **The clock refuses repeats, never firsts (commit 5).** A spent clock with half the takes
      on disk refused the other half, and the episode could never finish. Missing work always
      renders; only rungs stop. Past the ceiling a ladder signs its best flagged; only the
      closed SAFETY list (gate_policy.SAFETY) stops an episode. A plan line a builder repeats
      (studio/plan_tags.BUILDER, read from the code -- G-LIGHT and PLAN GATES are BUILDER,
      ONE PER TAKE is not) cannot ship flagged: it buys one climb, then stops.
    - **Stop at a boundary, never mid-step (commit 7).** 22 of 23 killed runs were sessions
      landing a fix (527 waste-min). `autopilot pause --at-boundary`, wait one unit, then
      commit. A started step that ends on the flag closes `deferred` (the events table has
      no 'paused'), never `failed`.
    - **A dossier says what it doesn't say (commit 8).** 117/281 physicals list "hair" inside
      a negation ("gives no height, build, hair ..."); the splitter cut it out as a hair
      clause. Negation scopes its comma list until a ';'. Scarlet's Watson, Hope, Lestrade
      and Gregson now take their bound row's hair; Jekyll's Utterson is honestly refused.
    - **The colour next to "hair" is the hair's (commit 9).** First-of over the hair layer
      read Gregg's "Sandy-ginger hair ... bald crown" as bald, the artilleryman's "black
      hair ..., red cut across the chin" as red (a shipped WotW look table carried it),
      and Scarlet's "grey eyes under sandy hair" as grey. The words next to the noun
      decide (before it, or right after: "hair turned ash-grey"); a grey modifier keeps
      grey; sandy is fair, matched last; every colour word has its \b.
    - **Same pixels, same size (J1; corrects CYCLE_2 carry #9).** The S6 "no-op crop" was a
      1024 -> 768 resample, and the reader tiles those differently. On truly identical pixels it
      agreed 2/2 and is deterministic by code (seeded, cached). The real instability is ONE sample
      on near-identical frames (6-16 % on count fields), frozen by the cache.
    - **Retired (C3_verdict D11):** H1 (narrow fault-set memory: ep22 61 -> 44 -> 4 and ep21
      50 -> 13 progressed after >= 3 stalls); H5/H6 (ghosts in takes / a ghost gate: 0/20 at
      contact-sheet size, and 0/12 at full 768 px on the six plain-wall narrator takes ep20 T20,
      ep22 T03, ep27 T24, ep18 T13, ep21 T16, ep24 T16 at 50 % and 90 %, read by eye
      2026-10-11); H8 for WotW (G-LINEAGE stays advisory); the merged LoRA; T #4's moved-SHA
      refusal (the boundary stop replaces it).
    - **Never sweep a drive to find a file (skeptic's own slip, 2026-10-11).** The ComfyUI root
      is `studio/comfy.py COMFY_ROOT`; read the constant.
    - **A ceiling bounds rungs, never firsts (2026-10-11, C3_p90_residual).** ep21 crossed 5 h
      20 min into step 09's 32-take round 0; the firsts, one QC and publish still owed ~79 min,
      so no rung rule could end it by 6 h. A rung now leaves the firsts still owed their shares
      under 6 h (the downstream reserve). Its price: the shares over-price a light episode --
      ep17 (297 min) would have lost 2 panel rungs.
    - **The neutral tile, benched once, switched once (P1, C3 bench block 2).** New refs draws run
      `image_krea2_cinematic_2x_neutraltile_visurena`: the 2x tile on style words only at denoise
      0.15. At 0.2 the style-only tile streaked the narrator's tweed 4.7x today's share; 0.15 is
      1.5x, 0 ghosts, the best head facenet. Trimming the tile words (c) or adding wardrobe nouns
      (d) did less. The title plate stays on the old workflow (D7).
    - **Deterministic, and stable on the seed (C3 bench block 1).** 12 shipped panels re-read at seeds
      111/211/311 against the cached 11: 2 field flips in 216 (0.9 %), both a people count on one
      12-figure crowd. The 6-16 % instability is the PIXELS (adjacent frames), not the seed:
      confirm-before-refuse on the same pixels buys nothing, so it is not built (D6).
    - **The refs drawers were the last house look (Jekyll, 2026-10-12).** The 10-11 "book look"
      fix reached the title plates only: build_pack, looks.py (fresh) and places.py still drew
      every book in WotW's Krea2 + Cinematic LoRA. A photoreal book would have had painted place
      masters under photoreal faces. `refs/look.json` + `studio/book_look.t2i` is now the one
      door. The look test measured style A at 15 s a picture against the house look's 40 s.
    - **A dated sentence in a dossier body is a state.** Lanyon's physical carried "By chapter 6
      ... noticeably balder and older"; the look table read it as his base hair, so the ch2 man
      with "a shock of hair prematurely white" was going to be drawn bald in every episode.
    - **An absence draws the thing (the door).** "Two storeys, no window" drew windows in 3 of 3
      look-test styles; the layout ("the upper storey one flat, blank forehead of discoloured
      plaster, the facade filling the frame edge to edge; one blistered door below") drew a blank
      wall on the first seed of three.
    - **A row text is linted where it is WRITTEN, by every writer (Jekyll ep01, 2026-10-12).**
      head_author and looks_table filed Utterson's "never lighted by a smile" and an unpaced
      "walking through London" unlinted; G-ROWTEXT refused them at bind time, ep01 step 01, ~3 h
      in. Both writers now cure (stillness table, row_lint.NEGATION_TABLE affirmatives, the pace
      append) and refuse every leftover fault before writing, so it surfaces in the refs step.
    - **A bound row without a gender is refused at bind, not at the takes (Jekyll ep01, 2026-10-12).**
      All eight rows were rebuilt bare (no display, no gender) and the episode wrote a ~2 h plan
      before takes_r2v refused them at G-TAKELINT. `pack_refs.rows_for` now keeps every identity
      field of the old row (display, gender, pronouns, marks, aka; an empty `named` value never
      erases one) and G-ROWGENDER refuses every genderless cast row at once, in step 01.
    - **The grid, the sheet ladder and every plan `look` follow refs/look.json, never the house (Jekyll ep01, 2026-10-13).**
      grids.py told every book "flat angular stylised 3d CGI ... NO photoreal skin" (and v2's STYLE_V2 the same), with
      "photographic" and WotW's "beard on the narrator" in the negative: a photoreal book drew painted door panels.
      `book_look.grid_style` / `grids.negative_for` now give a photoreal book a film-still line in its own lead words
      (a book's extra negative words go in look.json `negative`); the refs sheet redraw and the plan `look` read by
      takes, places and title plates obey the declaration too. A book with no declaration keeps every string byte for byte.
    - **A book's atmosphere is a constant, not a hope (Jekyll ep01, 2026-10-13).** Style A is fog and
      0 of 27 shots had any: the H3 style line's 16-word wall cut it ("The Sunday walks of London, 1886,
      gas") and the photoreal negative banned "blurry". `refs/look.json` `atmosphere` now reaches the
      grid line and reserves its words in the take line before the place and the light; a fog book bans
      "out of focus subject, motion smear" instead. Any declared look (photoreal or drawn, e.g. anime
      gothic) gets its own grid line, medium and panel words; WotW's prompts are byte-identical.
    - **The take was told its photoreal panel was "the house art style"** (take_refs). The panel is now
      named in the book's look -- and never with the word "still": L2 STILLNESS refuses it.
    - **A gate that reads "no cell" on a take that staged its panel is blind, not clean.** All 27 Jekyll
      takes skipped five rows. The panel is the cell now; on WotW ep19's shipped takes the opening and
      off-board rows would have failed 8 and 11 of 20, so they score but never fail on a panel board.
    - **A stillness meter is not a camera verdict.** `camera_ok` was False on 23 of 27 takes and passed
      all of them; its curve was clamped at 1.25x so 2.5x and 4.75x read the same. The binding row is
      `camera-move`, walled on the owner-liked WotW ep01-03 (0 of 69 fire), and it catches T14's tilt.
    - **A terminal still and a failed take do not ship (G-DEAD).** Jekyll ep01 held two 6.4 s panels and
      shipped T04, T06, T15 failed. Assemble cuts what live neighbours can cover (<= 1.5x slower) and
      refuses the rest. Static share is NOT a dead-shot test: WotW ep01 opens on two 1.00-static shots.
    - **An automatic camera rewrite is linted (studio/camera_lint).** "the man about" (a name cut at six
      words), "from the third" (a layout word as aim), "across the whole" (the old head's tail), a pace
      said twice, "a few yards" / "for twenty feet": the rebalance cure refuses a garbled candidate, the
      ladder repairs its aim, the prompt strips every distance and never adds a second pace.
    - **A crop of "one figure" can hold two** (Hyde's redraw, 2026-10-13): two poses 20 px apart were
      bridged as a dip inside one figure. A bridged run wider than 0.25 of the sheet splits at its gap.
    - **A drawn look needs its own refs drawer (Jekyll anime chain, 2026-10-13).** `book_look.t2i` and
      `sheet_ladder.redraw` knew photoreal and the house, so an `anime_gothic` book drew its sheets in WotW's
      painted Krea2 look. look.json `refs` now names the SDXL drawer, its tags and negatives; a person is ONE
      portrait front figure (a NoobAI turnaround drew 8 copies) and `sheet_front` takes a portrait sheet whole.
      Open: the look EDIT route (Krea2 identity edit) is still photoreal; a drawn book's garment looks need a test.
    - **"In every frame" fogs the fireside (chain test, 2026-10-13).** The grid's atmosphere sentence and the
      H3 line's reserved fog now reach a setup under the sky only (`book_look.under_sky`: `outdoors`, or no room
      word in `described`); an interior is drawn and rendered clear.
    - **NoobAI draws tags, not prose (Jekyll Hellsing cast, 2026-10-13).** The 12 cast members drawn from the
      look table's prose came back as women, a horned red demon, a walrus and four copies of Utterson; every one
      needed its own `entities` tags in look.json (1boy/1girl, age, hair, hat, coat), and the places too (a "blank
      plaster wall" in prose drew an archway). "walrus moustache" drew a walrus; "(clean-shaven:1.5)" + a weighted
      beard negative still bearded Jekyll on the pack seed, seed 11 held. A plan whose view names a place STATE
      makes `places.py --draw` draw that state fresh: re-derive it as one edit of its new master.
    - **A drawn look is its recipe, words AND order (Jekyll HEL style match, 2026-10-13).** The owner rejected
      the first Hellsing cast as "not the style I asked": look.json had drifted from the chain test's HEL recipe
      (`light grey background, even soft lighting` framing, a `(dark background), shadowed face, backlighting`
      negative, `victorian london, 1886` in the lead), which flattened the red-and-black gradients. Restored 1:1,
      the drawer then drew pure noise on every seed: the same negative tokens with the framing's weighted
      `(green theme:1.3)` bans ahead of the entity's burn NoobAI. `drawn_words` now joins base, entity, framing
      (the chain's order); keep colour bans in the framing negative, last. Prove a look change against the
      target pictures side by side (`style_match.jpg`) before any batch redraw.
    - **The red-and-black palette repaints the cast (Jekyll HEL cast v2, 2026-10-14).** Under the HEL lead every
      brown or dark coat came back red (Enfield, Newcomen, Guest, the cab driver); an entity negative
      `(red coat:1.4), red clothes ...` plus the colour named in the tags held them. NoobAI drew "custodian
      helmet" as a knight's helm and a yellow hard hat; describe the shape and ban `visor, knight, closed helmet`.
      More weights on Hyde's face (`lit face`, `human face`) made him darker; his chain-target words verbatim plus
      one owner fix and a seed sweep gave the human grin. Pick from 3+ candidates per person, drawn through
      `book_look.t2i` into an audit folder; commit the pick with `sheet_ladder.redraw` on the same seed (it
      reproduces the candidate bit for bit). `looks_table.py <book>` alone writes only refs.json's bound rows;
      name the rest.
    - **Side-whiskers are not a moustache (Jekyll HEL remake, 2026-10-14).** The closed FACIAL table read
      `whisker` as `moustache`, so looks.json stamped Hyde's "mutton-chop side-whiskers" (and Lanyon's white
      side-whiskers) a moustache and LOOK-STATE would have refused every Hyde drawn as the book says. The vocabulary
      gains `sideburns` (side-whiskers, mutton chops, sideburns; an explicit moustache or beard still wins, a bare
      "whiskers" stays a moustache) and one cheek family with `beard` (a reader calls mutton chops a beard).
      A table built before a vocabulary change is re-marked from its own words, never re-drafted:
      `looks_table.py <book> --remark` (0 writer calls, pictures and spans untouched; Hyde x2, Lanyon x1 moved).
    - **A drawn book's title card is drawn on its drawer (Jekyll HEL remake, 2026-10-14).** `series_title.base_art`
      knew Krea2 photoreal and the house Krea2 + LoRA, and read the look from ep01's plan: ep01's card stayed
      photoreal under a Hellsing cast, and with ep01 set aside it would have re-baked photoreal. A book with a
      `refs` drawer now draws the card art there (`kind: title`, no place framing so the lone figure is not
      banned; the `title` entity's tags, else motif.txt). The card's motion line stopped quoting WotW (heath,
      metallic hoot, red light).
    - **A resume must never re-say a refused seed (Jekyll HEL ep01, 2026-10-14).** The narrator's 3.0 s
      l15 failed the ear (sim 0.59-0.63 against 0.65); every relaunch rendered attempt `tries` and then attempt
      `1` -- say_lines zeroed the prior after the first pass -- so the second try repeated a refused seed and
      `tries` never moved past 2: three brain rounds on a loop that could not change its input.
      `say_lines.attempts_from(tries)` gives every pass of a run new attempt numbers.
      From the third try the design clip and the speaker's best line take turns as the reference: l15's
      best-line clones scored 0.42/0.53 where design seeds scored 0.59-0.63; genuine narrator lines cut to
      3.0 s score 0.69-0.82 against the design, so the 0.65 floor was right and the render wrong.
      Ten tries of l15 (every word heard) scored 0.42-0.63 and the step REFUSED; the brain found no order
      and the episode parked. The record step now ends like every taste ladder: after `TERMINAL_TRIES` (8)
      the best try heard right and within `TERMINAL_MARGIN` (0.08) of its floor is kept, flagged keep_best.
    - **A bind is current only to the look table (Jekyll HEL ep01, 2026-10-14).** refs.json was bound for
      chapter 1 before the table was rebuilt; Enfield's row said `base`, the table `frock_coat_topper`. Step 01
      skipped on its chapter stamp and step 06's G-LOOK asked for "rebind (step 01)" -- a step that called
      itself done. `step_01_bind.done` now also needs every bound row's look to be the table's for the chapter.
    - **Gaslight does not lie down (Jekyll HEL ep01, 2026-10-14).** "a yellow pool of gaslight lying on them"
      asked the walking little man to lie, on the panel and again on the take (a retake of a correct take):
      the thing list matched `light` only as a whole word. Any `*light`, fog, frost, a pool or a puddle is ground.
    - **Cel fills read as stillness (Jekyll HEL ep01, 2026-10-14).** frozen-whole's 0.65 share wall was fitted on
      WotW's painted takes; flat cel shading gives optical flow nothing across its fills, so T14 -- Enfield lifting
      his hand and turning his head as he names Hyde -- read 76 % static (longest still run 1.08 s) and failed HARD
      three rounds. On a drawn look the row is HARD only when the frame also holds past G-DEAD's 2.5 s
      (`stillness.DRAWN_RUN`); T01 (run 4.33 s) and T19 (2.71 s) still fail. House and photoreal books unchanged.
      **REVERSED by the owner, 2026-10-14:** the relaxation shipped T01, T02, T19 and T20 as holds he reads as dead.
      A drawn look is judged by the house stillness rule; its cure is a retake (move type) or the cut, never an exemption.
    - **A title keeps its capital (Jekyll HEL ep01, 2026-10-14).** A move_type cure locked shot 19; its end
      "Mr. Enfield at the CENTRE ..." lent the arrival its noun, `noun_phrase` lowered it to "mr. Enfield", the
      subject swap left "mr. <Subject 1>", the splitter cut the sentence at "mr." and L21 refused the take
      prompt. Honorifics are names to `is_name`, and `sentences` never splits after Mr./Mrs./Dr./St.
      (And again: a regex written through a heredoc put BACKSPACE bytes where `\b` was meant -- use a file.)
    - **A dialogue take frozen twice pans (Jekyll HEL ep01, 2026-10-14).** Locked with the actor's verb, T01 and
      T14 froze again on fresh seeds (92 %/86 % static, held 4.3 s/3.6 s): H3 barely animates a locked cel
      close. The same fault twice is the plan's; the ladder's next dialogue move is `pan_to` the speaker -- it
      turns where it stands, so G-TALK holds (WotW ep01 panned all four spoken shots).
      The first pan cure wrote "The camera pans across to Mr": `aim_of` cut the at_rest clause on the period
      of "Mr.". The aim now stops at a clause mark or a full stop, never a title's period, and a camera aim
      that is only a title is read again from at_rest.
      T01 then panned, turned, spoke and pointed its cane -- alive by eye -- and still held 4.1 s by whole-frame
      flow four rounds running (edge-masked flow read the same): a cel mouth is too small for the mean. On a
      drawn look a DIALOGUE take that the block-max meter finds alive in every span is not HARD-still.
      **REVERSED by the owner, 2026-10-14** (with the relaxation above): a speaking drawn take is judged by the house rule too.
    - **Nobody appears from nowhere (Jekyll HEL ep01, owner 2026-10-14).** "The first shot doesn't have the
      actual characters in the scene, so in the second shot the character magically appears." The plan was
      right at shot 0 (faces: the lawyer and Enfield); the GRID was not: `wide_only` (2026-10-02 09:39, ep16's
      four-pose turnaround) drew anyone only ever wide from wardrobe words, and shot 0 held a blond man and a
      man in a brown greatcoat -- neither sheet. Shot 1 staged Enfield's sheet, so he "appeared". The same rule
      drew shot 7's Hyde bearded from his row's words (the row says mutton-chop whiskers; his sheet is
      clean-shaven), shots 8-9 chained on that panel as their room, and shot 9 drew both Hydes. The cause of
      the four-pose fault was fixed three hours after `wide_only` (the one-figure crop, 7ad14e6); the
      exemption outlived its reason. Grids now stage every held person's crop at every size, the ceiling
      picks the closest readable faces (`scene_cast.pick`), and the plan gate G-PRESENT refuses a person first
      seen mid-scene without `enters` (ep01 shots 5, 12, 19). Replay: 199 such appearances over the 42 shipped
      plans, 103 of them after an establishing wide that holds nobody -- the pattern was the house style.
    - **The master is upscaled by RTX VSR, and QC's segment cap had to learn it (Jekyll HEL ep01, owner
      2026-10-14).** assemble's Lanczos 2x became NVIDIA RTX Video Super Resolution 4x ULTRA to 3072, in
      process (`studio/master_upscale.py`; the ComfyUI node holds the clip as float tensors and took 49 s a take).
      Measured on ep01: the upscale row 252 s against a 38-40 s Lanczos join (+3.6 min), QC 498 s against 403 s,
      a 1.5 GB master against 210 MB. The first QC FAILED 7/23 segments with every cut, offset and frame right:
      the segment mean cap (1.0) was fitted on Lanczos masters, and RTX sharpening puts a correct segment at
      0.97-1.48 (no frame over 1.56; off by one 1.50-5.20). The master's upscale is now recorded by sha8 in
      `cut/master_layout.json` and sets the cap (`edit_gate.segment_cap`, 2.0 for rtx). A new picture
      process re-asks every threshold calibrated on the old one -- the gate accused correct work.
    - **A walk is a step paid for in ground (Jekyll HEL ep01, owner 2026-10-14: "the little walk is weird").** T03's
      Hyde faced the camera square-on while he travelled sideways, legs pattering, torso and hat level as on a rail:
      3.94 steps/s for 0.027 body heights a step (a human walks 1.6-2.2 steps/s; liked WotW walkers cross 0.052+).
      Nothing read it: frozen-whole saw a live frame (14 % static), G-MOVE saw the camera obey (1.00x), `held` reads
      only a subject the plan keeps in place, and every eye reads still frames, which cannot show a gait. G-GAIT
      (`studio/gait.py`, HARD row `gait`) now counts the step rhythm against the ground crossed whenever the plan
      asks a subject to walk; its cure is the plan's verb ("in profile, a long stride, feet in the picture"), since
      "stumps along" minced again. Coverage is thin: 71 of 91 walker takes are unmeasurable (feet out of frame 37,
      no rhythm 31, depth 3) -- frame a walk with the feet in the picture so the gate can read it.
    - **A check is cut only for the reserve (Jekyll HEL ep01, owner 2026-10-14: "I think you skipped DQ checks").**
      Past the 5 h ceiling `--ceiling-spent` served old take and QC verdicts under any measuring code, so a new
      measure (G-GAIT) would never have read the takes with 51 min left under 6 h. A measuring check now runs while
      it leaves the downstream reserve under 6 h (`Budget.checks_cut`); only rescue rungs close at the ceiling.
    - **A held measure must be handed its inputs (Jekyll HEL ep01 v2, owner 2026-10-14).** The take identity row read
      "not measured" on every take for three weeks: 4c5f14c held the sheets back on a measured reason (3 false fails in
      34 WotW takes) and nothing ever turned it back on, so the master eye flagged identity drift the take gate had
      never looked for. The sheets go in again; the row is ADVISORY (`TAKE_IDENTITY_HARD`) because a replay with
      sheets would refuse 23 of 118 WotW ep19-27 and 37 of 97 Scarlet ep08-14 shipped face takes, and the master eye reads it (`master_eye.take_identity`).
      A gate held back needs a dated condition to come back, or it is a gate removed.
    - **The row and the sheet are one man (Jekyll HEL, owner 2026-10-14).** Hyde's row said "thick, bushy black
      mutton-chop side-whiskers" from "a swart growth of hair" -- which the book gives his HAND -- while his sheet is
      clean-shaven, and words-drawn wides drew a bearded stranger beside the sheet's Hyde. He is clean-shaven in
      heads.json, the look table (words, then `looks_table.py --remark`), look.json's drawer tags and the bound row.
      Black and brown are one hair family, so he and clean-shaven Enfield now share (dark, none): `heads.json`
      `apart_from` keeps an owner-ruled pair apart only with its stated reason (age, stature, cut, hat).
    - **A terminal no run can reach is a park (Jekyll HEL ep01 v2, 2026-10-14).** l15 is heard right and sits at
      0.42-0.63 against 0.65; the keep_best terminal needs 8 tries, but each run gave a line 2, so every run exited
      1 and the brain parked the episode twice (v1 needed 13 relaunches). A record run now takes the rounds the
      least-tried refused line still needs to reach the terminal (`say_lines.rounds_for`).
    - **The take terminal and G-DEAD must agree (Jekyll HEL ep01 v2, 2026-10-14).** Under the house stillness rule the
      first batched round re-headed four frozen cel takes with garbled aims ("tracks beside the lawyer across to the
      door's", "... to the folded", "Mr. Enfield's face,"): the aim took the first preposition's tail, cut it at six
      words and kept its comma. Two froze again, the identical-signature breaker sent them to the terminal, the
      terminal held T10 (6.75 s) and T16 (3.9 s) as stills -- and G-DEAD refused the master on all of it, a loop no
      retry could leave. Now: a from-to move aims at its destination, whole (`take_ladder.destination`); an aim cut
      on a possessive is read from at_rest; a frozen follow is given a push, never a lock; a frozen-only take gets its
      second move type past the breaker; and the terminal never holds a panel longer than G-DEAD's 2.5 s.
    - **The shorter take is measured against the length it was built for (Jekyll HEL ep01 v2 finish, 2026-10-15).**
      T14 ("It was a man of the name of Hyde.") failed lip-sync (WER 0.56) and G-TAIL ("of the name of Hyde" at
      -22.7 dB in the silent tail) on four renders. The router sent it to `timeline_trim`, but `shorten()` compared
      the timeline (5.04 s) against the FILE (5.88 s = frames_for(placed + HANDLE)), read every take as "the length
      changed under it", and re-rendered at the same length: four reseeds. Fixed (`take_ladder.built_for`, ce2ddea);
      the one real shorten (coda 1.5 -> 0.75 s, take 141 -> 124 frames) passed both rows at once: WER 0.11, tail
      -48.4 dB. The memory held: mux lag and a talking tail follow LENGTH, not seed.
    - **A cheque is print (2026-10-15).** The book's own prop -- "gold coins and a folded cheque" -- failed content as
      "text or lettering" and shipped flagged. `panel_content.PRINTED` now names cheques; a wide still refuses (811cabb).
    - **`take_dq --attempts` swaps an older attempt in and the next render round destroys it.** The kept file keeps
      its old mtime while T<NN>.graph.json is newer, so `take_currency` reads it "unfinished", and the next
      `takes_r2v` overwrites it WITHOUT archiving and with `tries` reset (same seed as try 0). Lost on the finish:
      T22's G-GAIT-cured render (95, re-made with --retake) and T19's 100 and 87.6 (the 87.6 twice, once through step 11 re-running step 09 on the "unfinished" takes). Until fixed: copy the kept T<NN>.mp4 to `attempts/` before any
      later round, and re-render a lost cure with `--retake` (tries 1 reproduces seed + 101).
    - **Over-the-shoulder 1x1 grids do not draw the shoulder.** door_day s02 (OTS onto the lawyer) on 5 seeds: the
      shoulder lost every time and twice the lawyer drawn in Enfield's hat. A shot whose second person is a shoulder
      is a plan-level fault for Qwen-Image 1x1; write it as a two-shot or put it in a 2x2 with other OTS faces
      (shots 14 and 19 drew their shoulders in pavement/sunday 2x2 grids).
    - **Identity DRIFT that follows the action is the plan's.** T19 ("lowers his eyes and shakes his head", push-in)
      read Enfield 0.52-0.75 on 7 renders; the moving takes all drift (his face goes under the brim), the one
      locked replan froze (82 %). A take's verb that hides the face cannot pass a first-vs-last identity measure.
    - **A kept attempt is a finished take; no take file is written over (fix, 2026-10-15).** The attempt-swap fault
      above is closed: `episode_home.swap_in` moves each roll WITH its graph (`T<NN>_failN.graph.json`) and stamps
      the swapped-in take landed now (`take_currency.stamp_landed`), so currency reads it finished and step 09's
      `done()` no longer calls it stale; `takes_r2v` archives before any render (`make_room` -> `displace`, and
      `collect` keeps aside anything still on disk) and carries `tries` forward; a retake round renders only its
      named and missing takes (`wants_render`) -- step 11's retake rung had re-rendered T19/T22 beside shot 13.
      The `--retake` workaround is retired. NB the take_dq.py edit moves `measures_sha8`: one full re-measure.
    - **A sheet and its row are one girl (Jekyll HEL ep01 v2, owner 2026-10-15: "the girl is not accurate in some
      shots").** Her row said "a small knitted woollen bonnet ... a plain grey pinafore"; her HEL sheet drew a black lace
      bonnet, a black pinafore and hollow solid-black eyes. The grids drew her from the words where her sheet was not
      staged and from the sheet where it was: T05 a grey knitted bonnet and red sleeves, T06 a white-grey heap, T07 a
      beige bonnet -- three girls for one. LOOK's look-back asks only the prompt's NOUNS (a bonnet, a pinafore: both
      there), so no gate could see it. SHEET-ROW (`studio/judges/sheet_row.py`, inside LOOK at refs/04) now LISTS the
      headwear, its colour and material, the garments' colour (whole sheet) and the eyes (whole sheet AND a head crop;
      `hollow` only when both agree) and code compares them with the look table's base layers: HARD on headwear colour,
      material, garment colour and eyes; the hat's kind only flags (LOOK-STATE owns it). Replay on the real reader
      (`docs/audit/2026-10-14_jekyll_ep01_hel_v2/girl/sheet_row_replay*.jsonl`): the lace sheet against its old row
      fails 3/3 (lace for knitted, black for grey, hollow eyes); the redrawn girl passes; of 7 other bound sheets it
      refuses Lanyon (row "grey silk top hat", sheet black -- true) and the constable (eyes read hollow on both reads;
      his row also says a custodian helmet and the sheet wears a peaked cap). Fix those rows or sheets before ch4/ch2.
      Calibration on the way: whole-sheet eyes read the new girl's blue eyes `hollow` on one load and `irises` on the
      next, the head crop read Poole's white pupilled eyes hollow -- one read is a coin, two views agreeing is a measure.
      The girl was redrawn ONE base sheet on the HEL drawer (seed 505, 3 rounds of candidates, the words then made to
      say the picture: a small soft grey woollen bonnet, fair plaits, blue eyes, a plain grey pinafore over a dark-red
      long-sleeved blouse, black boots -- dossier, heads.json, looks.json, look.json tags and the bound row).
    - **The LOOK gate had never read the Jekyll cast (2026-10-15).** With no verdict file and a shipped master the first
      verdict is "grandfathered" -- lettering and limbs only -- so the HEL cast drawn 10-14, after nothing had shipped on
      it, was signed light. Now only sheets OLDER than the newest master are grandfathered; a sheet drawn after it is
      read in full (`step_04_verdict.fresh_paths`). Reading it in full then refused the girl for a missing "light": a
      drawn look cuts the house sheet form before drawing, so its nouns are no longer asked (`look.asked_words`). And
      the ladder's redraw_seed REPLACED the owner's pick twice before the fixes landed -- run a dry `look.judge`
      (`girl/look_dry.py`) before step 04 on a hand-picked sheet. TaskStop on a backgrounded `uv run` leaves its python
      child running its ladder (memory: kill the run tree by CommandLine).
    - **Two of one person in one panel is the prose telling a sequence (T06, 2026-10-15).** Shot 6's frame told "run
      into one another, she falls on the cobbles, and he walks straight on over her": the panel drew the girl twice,
      fallen AND still running, and both panel gates and the eye passed it (casebook `copies`). Cured with the panel
      ladder's own `twin` reprose (`girl/cure_shot06.py`); a spike shot's first frame is one moment.
    - **A girl of about nine was "this woman" to H3 (T05-T07, 2026-10-15).** `age_of` read digits only ("girl of 9"),
      so the row "a small girl of about nine" stated no age and the take prompt said "<Picture 2> defines this woman
      alone" beside a child's sheet. Ages in words, after about/some/maybe, now read (`episode_ref_official.age_of`).
    - **A re-measure after a code change re-opens a take the cut once passed (T19, 2026-10-15).** iter2 shipped T19's
      87.6 render, which the attempt-swap fault then destroyed; the take left behind froze (83 % static) on locked,
      push, follow and pull-back alike, and G-DEAD refused the master (neighbours 8.54 s near-dead + 4.96 s cannot cover
      7.08 s at 1.5x). plan.py's own words -- "pushes in a hand's breadth toward Mr. Enfield's face, across the whole
      shot" -- passed on both seeds (95, 100); the ladder's terse "pushes in toward Mr. Enfield" froze. A cure that
      rewrites the camera clause loses what made the clause move; prefer the shot's authored move on a re-seed.
      `aim_of` also cut "Mr. Enfield's frank, lively face" into "toward Mr. Enfield's frank" (fixed: a possessive cut
      by its adjectives aims at its owner).
    - **A push into a walker turns his walk into a shuffle (T06, 2026-10-15).** The frozen crane (83 % on two seeds,
      G-STILL had named it) became a push toward the kerb: the girl large, red sleeves, plaits, screaming -- the
      owner's ask -- but both renders walked the little man on the spot (G-GAIT 0.041 / 0.04 heights a step; by eye
      ~10 px in two seconds). The crane render that passed 95 was kept and the plan says the crane again
      (`girl/restore_move.py`); the girl reads as a child in a grey bonnet and dress, smaller, without the red.
    - **OPEN: an archived attempt can carry another render's graph (2026-10-15).** After two step-09 rounds T06_fail4.mp4
      (rendered 10:28) sat beside a graph dated 10-14 14:53; `take_dq --attempts` swapped it in WITH that graph, so
      step 09 reads T06 stale and would re-render it (it did re-render T06/T07 once). Not yet fixed: `displace` /
      `swap_in` pairing when a round displaces a take whose own graph was already moved. Until fixed, never run step 09
      after a `--attempts` swap without checking `stale_takes`.
