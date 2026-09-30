# Why 32 rounds — five-expert debate, 2026-09-30

Owner: "before you were able to do it in 3-4 rounds, max 5." Five experts, read-only, argued
from the disk: the yield historian, the cure-rate economist, the input-quality expert, the
ladder-policy designer, the judge calibrator. Unanimous verdict in five sentences:

1. **The renderer never got worse — the exam tripled** (8 take gates in Sherlock ep01-09 →
   26 in ep14; WotW ep05 passed 30/30 against 16 gates, ep14 passed 11/30 against 26, almost
   all hard failures on gates born after ep11).
2. **First-pass yield was never golden** (SiS ep07 32%, WotW ep02 35%) — but the old process
   absorbed failures with silent same-round retries and ONE person-chosen batched round (F1);
   the automated ladder turned the same yield into serial rounds: one round per rung, re-judged
   between rungs, restarted from seed on every resume.
3. **86% of ep14's take faults mirror the panel or the prompt** (36/42 rows, verified on
   pixels); ep13's faults contain zero content kinds — a clean board leaves only curable faults.
4. **~40% of the retake churn was judge false alarms** (9 of 11 audited accusations false:
   the clone wall ignoring the declared crowd, the mustache check concatenating cast rows, the
   lettering wall refusing the chapter's own newspapers and boards, thresholds fitted on the
   other book), and the ladder has no rung for "the judge is wrong".
5. **Measured cure rates**: move_type 89-100% on frozen/held (~8 min/cure); seed ~0% solo
   (3.6 GPU-h); shorter_take on lag 0/15 (the free head/timeline cure worked); content by take
   render 3/21 vs by panel redraw 1/1.

## The agreed solution (built the same day, test-first)

**A. Judge truthfulness (the false-alarm 40%)**
- A1 Mustache per face row, never the concatenated cast string (bug).
- A2 A declared crowd is not a clone farm: with `crowd` prose, figure-count is no fault and
  lookalikes wall only at >= 3.
- A3 Staged print is not lettering: a shot whose plan/setup prose stages printed matter
  (newspaper, board, map, placard, sheets, notes, blackboard, telegram) expects text — the
  lettering row is advisory there unless OCR reads real words; map/sheets/notes/blackboard
  join the PRINTED vocabulary.
- A4 `is_daylight` knows dusk/dawn skylit exteriors (the no-floor wall read a rosy dusk as
  a night grade every round; value constant across seeds).
- A5 Pass-through demoted to advisory until benched on WotW owner rows (its own docstring:
  margin one take wide); `held` stays a wall (it truly caught T22).

**B. The ladder rebuild (F1 restored as code)**
- One batched rung, tries=2 (ROUNDS_CAP=2 across resumes in ladder.json; round 0 + 2 cures =
  MAX_TAKE_ATTEMPTS=3 by construction). Per-take router, measured, not ordered:
  frozen/held/pass-through/last-vs-panel/drift → move_type; lag → FREE timeline/head cure,
  never a render; leak → head_cut (free); repeated content and every input-borne kind
  (content, clones, identity, unread, look, letterbox) → NO take render: one panel redraw +
  one render where the board can cure it, else the terminal now; else seed (the blanket seed
  round is retired — 0 measured solo cures).
- Circuit-breaker: an identical accusation surviving its own cure goes to the terminal, not
  around again (fault signatures per take in ladder.json).
- Stills fire at round 0 for input-borne faults on narration shots (cap 2, adjacency and the
  letterbox bypass unchanged); a still prefers a panel that passes the escaped kind.

**C. The plan tells the truth first**
- G-CROWD: `crowd` prose with `extras=0` is a contradiction refused at plan time (11 ep14
  shots were born self-contradictory).
- The battery lists which shots stage printed matter (the expects-text set) so the writer
  and the gates agree on where text belongs.

Expected: ep14's fault stream replayed under A+B ≈ 5 rounds / ~3 GPU-h instead of 19 / ~10;
with the aspect and one-room fixes already in, a 30-shot episode's takes land in
round 0 (~2 h) + <= 2 batched rounds + terminal.

Full reports: the five agents' hand-backs of 2026-09-30 (session record); frames for the
false-alarm audit in D:\temp\judge_audit_ep14. Related decisions: 2026-09-24 automate-the-
taste-gates (judges sign, never park), 2026-09-28 one-room-per-setup, the 2026-09-29 caps.
