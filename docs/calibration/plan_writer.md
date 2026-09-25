# plan writer — the episode writer under the contract and the plan ladder, measured on a real unit

## First contact 2026-09-25 — chapter 13 of the first produced book (narrator + curate), tier `local` = gpt-5.6-luna, reasoning off

The unit was deferred twice and crashed once before a plan existed. Every refusal
was the CONTRACT (pydantic, free, deterministic) on a rule the writer's skill
already states; the battery (`plan_check`) and the critic never got a draft.

| pass | rungs | refusals, in order | outcome |
|---|---|---|---|
| 1 | improve, improve, fresh_brief, model_tier | 5 contract faults; rule 5; rule 5; 4 faults; rule 5 | deferred; step 03 then ran on no plan.json |
| 2 | same | 'slowly' ×2; rule 5; shot numbering; 'slowly' ×3; 19-word lines ×2 | deferred |
| 3 | one rung, three gateway re-asks | 'slowly' at shots 8 and 14, three times | crashed: the refusal carried no CONTRACT line |
| 5 | same, the writer editing its draft | ordering; rule 5; a beat before the button; ordering -- then the `canon` rung (337 s) passed the CONTRACT and the battery refused ~80 lines (light directions, at_rest floors, head fractions, `source` spans saying "chapter 13", 11 takes over 8 s) | deferred with a contract-valid draft the next pass would have thrown away |
| 6 | resumed on `canon` | the resumed draft: CONTRACT OK, G-LIGHT clean, 34 lines (was 80); two improve rungs stuck on the dialogue dial (20.4 % / 22 % against 20 %, printed "20%"); fresh_brief wrote a new contract-valid draft; model_tier's failed ordering | deferred with the fresh draft -- the 34-line one was overwritten |
| 4 | same as 1, three re-asks each | 'slowly'; 3 lines on one shot; 20-word lines ×2; a dialogue face not at close; 'slowly' ×3 | deferred: every rung fixed what was named and, rewriting from nothing, tripped another rule |

~50–75 s and cents per draft; a ladder is ~8 min.

## What generated it

- **A re-ask repeated the same prompt.** `llm._structured_once` re-asked on a
  `StructuredOutputException` with the original prompt: the model never heard what
  was wrong. Now the re-ask quotes the latest refusal under `--- REFUSED, fix these ---`.
- **Each rung rewrote from nothing.** With the refusal list growing, every fresh
  draft tripped a different rule (five rungs, five different rules). The contract
  now refuses INSIDE the structured call (`Draft` validates `to_episode`), so the
  gateway's three re-asks fix a draft in place before a rung is spent.
- **Rule 5's message read as the rule.** "the last line is not the protagonist's"
  was taken as "make it the protagonist's": four of five drafts ended on the
  narrator. The message now names the fault and the protagonist.
- **A field rule has no CONTRACT text.** A `Shot`'s own validator ('slowly')
  refuses inside pydantic with only its message; the ladder reads the pydantic
  cause off the gateway's exception, so every schema refusal is a pending
  refusal and only a provider failure raises.
- **The refusal named the shot, not the sentence.** 'slowly' at shot 8 survived
  three re-asks. A refusal line now quotes the field it is about
  (`-- motion: '...'`), so the writer sees the sentence to change.
- **A deferred unit kept running.** Step 02 wrote `plan.deferred.json` and returned;
  the runner launched step 03 on a plan that did not exist. A deferral is now an
  outcome (`Deferred`, event `deferred`, exit 2) that stops the unit.

- **A rung rewrote from nothing.** Pass 4 proved the rest: with the refusal
  quoted, each rung fixed what was named and lost something else. A refusal
  names rows, so the writer now EDITS: on a contract refusal it re-asks with its
  previous plan as JSON under `--- YOUR PREVIOUS PLAN ---` and "change only the
  refused rows" (three edits, then the refusal reaches the ladder); an improve
  rung hands the battery-refused plan on disk back the same way. The contract
  validator on `Draft` is gone again (a field rule refuses inside pydantic before
  it; the writer's own loop is where the contract belongs).
- **`model_tier` escalated to the same model.** The "reasoning" tier is the
  workhorse model with reasoning off (the owner's cost choice for every other
  caller); the rung now asks `canon`, the one tier that reasons, on a deferred
  unit only.

- **The reasoner came last.** Pass 5: four rungs on the cheap tier failed the
  CONTRACT; the reasoner's one rung passed it and reached the battery. A rule
  miss (contract or battery) now escalates the desk to `canon` for the rest of
  the climb; the critic's judgement faults stay on the cheap tier.
- **A deferred draft was thrown away.** The draft that reached the battery went
  into `plan.deferred.json` with its 80 lines and the next pass authored from
  nothing. Step 02 now RESUMES it: the reasoner edits the deferred draft under
  its own refusal lines before the ladder starts.

- **The deferral kept the last draft, not the best.** The desk now remembers
  the battery-refused draft with the fewest lines and defers that one.
- **"20%" refused by a 20% ceiling.** The dialogue dial's message prints one
  decimal and the edge it crossed.

Cost so far: passes 1-4 on the cheap tier ~cents each; passes 5-6 on `canon`
5-10 min a draft (reasoning tokens), a ladder ~30-40 min.

Unchanged and to be measured on the next passes: `MAX_IMPROVE = 2` (now with three
re-asks each), the 18-word wall, the no-slow rule.
