# 2026-10-13 — The book's narrator, the tale, and a plan written for a viewer

Status: **BUILT 2026-10-13** (story/plan lane), decided on the owner's behalf under his
"decide, don't ask" order, open to veto.
Evidence: `docs/audit/2026-10-13_jekyll_ep01_review/` (DIAGNOSIS, STORY, MOTION).
Tracker: `architecture/plan/2026-10-13_story_plan_lane.md`.

## The fault

Jekyll & Hyde ep01: the owner "did not like the video at all". The root under most of
it: WotW's data and constants filled every gap a fresh book exposed.

- **No narrator.** A third-person book had none. G-SPEAKER refused `narrator` five ladder
  rounds running and printed the cast as its menu; the writer took `henry_jekyll` --
  the wrong man, the wrong person, an octave high. Nobody decided it; ep02 inherited it.
- **The tale was paraphrased.** Chapter 1 is mostly Enfield telling a story. The
  dialogue dial (5-20 %) and the 8-word quote wall turned it into reported speech in
  another man's mouth.
- **Too dense.** 362 words, 9.4 s of pauses, projected at a guessed 3.0 words/s (the
  voice measured 2.46): 146 s projected, 173 s run.
- **Told, not shown.** It opened on 15 s of Utterson's habits (a `nonscene` row the judge
  demanded), and the trampling was never on screen.
- **The camera moved instead of the story.** 7 of 27 shots were weather filler; 6 of 8
  dialogue shots pushed in, because three rules forced a push.

## The ruling

1. **A book's narrator is set once, before episode 1** (`studio/book_narrator.py`,
   `library/<book>/refs/narrator.json`: speaker, person, on_camera, voice). A
   **third-person book gets a dedicated `narrator` voice row** -- a calm, low storyteller,
   never a cast member, never on camera. A first-person book declares its "I". A book
   that declares nothing keeps the one narrator its PUBLISHED episodes share (WotW,
   Scarlet: nothing changes). Neither: **step 02 stops before any writer is asked**, and
   G-SPEAKER's refusal names nobody. A character narrating in the narrator's place is
   refused; one narrating beside him is advice.
2. **`tale`, a third line kind**: a character telling his own story in his own voice,
   voice-over over pictures of what he tells; the book's words kept; outside the
   dialogue ceiling and the quote wall; it meets the chapter's speech floor.
3. **Pacing (G-PACE)**: a new book projects at the studio's measured 2.45 words/s (never
   3.0); <= 310 words; >= 15 s of beats and codas; over budget a LINE is cut
   (`plan_cures.cut_lines`), never a breath. Step 05's measured-runtime trim stays the
   last resort.
4. **Plan checks**: G-ACTION (at most 2 empty shots moved only by weather); the critic
   lists the chapter's threat and its key event, and code judges G-HOOK (the opening
   shot or line carries the threat) and G-SPIKE (the key event is shown in a shot); a
   `nonscene` row may be folded.
5. **Dialogue camera**: a held dialogue exchange is one shot/reverse-shot unit for
   G-MOVES; a held angle on a spoken line is not G-STILL; a frozen dialogue take gets the
   actor's verb, never a push; the take builder's example is a locked head; G-TALK
   allows one travelling dialogue shot (a pan is no travel).
6. **The writer's brief has a viewer**: five rules -- hook in the first shot, the spike is
   shown, the teller tells his own tale, hold after every reveal, withhold what the
   chapter withholds.

## Calibration and the replay

Every number is measured: WotW ep01-03 (liked) 266-307 words, 18-20 s of pauses, 0-1
travelling dialogue shots, 0 weather fillers; Jekyll ep01 362 words, 9.4 s, 7 travels,
7 fillers. All 41 shipped WotW and Scarlet plans were replayed through the new gates on
CPU: G-SPEAKER 0 hard rows (2 advisories: WotW ep22 curate, ep24 artilleryman), G-ACTION
0, G-MOVES and G-STILL only lose rows. G-PACE and G-TALK fire on later shipped plans and
are advice on a rendered plan (the G-SETUP rule), hard on a new one. Two first drafts
would have refused liked plans (G-TALK counting pans; the move share divided by the
shorter list); the replay caught both before they landed.

## Not decided here

Breaths of at least 0.9 s between lines (the SOUND lane), the narrator's voice itself
(the VOICE lane casts `cast/narrator/`), Hyde's sheet, fog and the take gate (PICTURE).
