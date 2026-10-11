# Lessons

Each rule in SKILL.md, with the measurement that made it. When a new failure
teaches something, add it here with its evidence, then put the rule in
SKILL.md.

## Process

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
