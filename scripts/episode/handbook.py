#!/usr/bin/env python
"""The episode handbook: how a chapter becomes an episode, end to end.

    uv run python scripts/episode/handbook.py [<codex_id> <episode>]

Written so somebody can run the next chapter in a fresh window without reading
this conversation: every stage in order, the command, what it costs, what it
writes, and the gate that stands in front of it.  The rules section is the part
that was learned the expensive way, each with the measurement that taught it.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import importlib.util as _iu

ROOT = Path(__file__).resolve().parents[2]


def _sibling(name: str):
    spec = _iu.spec_from_file_location(name, Path(__file__).with_name(f"{name}.py"))
    module = _iu.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


rc = _sibling("runcards")

RUN = """# EPISODE 2 - chapter 2, every stage in order.  Nothing below spends until a
# line says PAID, and no line renders or spends without the --approved you type.
BOOK=20260822113400; EP=2; EPDIR=library/${BOOK}_a-study-in-scarlet/episodes/ep02

# 0a RESUMING an episode?  Read this first and say it back before touching anything:
uv run python scripts/episode/story.py $BOOK $EP --say

# 0b the plan.  Write it (or have the author agents write it), then prove it:
uv run python -c "import json,sys;sys.path.insert(0,'.');from studio.episode_spec import Episode;\
Episode(**json.load(open('$EPDIR/plan.json',encoding='utf-8')));print('VALID')"

# 1  AUDIO FIRST.  Nothing downstream exists until the lines do.
uv run python scripts/episode/say_lines.py $BOOK $EP          # --redo=18 for one line

# 2  the timeline is derived from the measured lines, never the other way round
uv run python scripts/episode/respot.py   $BOOK $EP
uv run python scripts/episode/timeline.py $BOOK $EP

# 3  one empty plate per setup
uv run python scripts/episode/frames.py   $BOOK $EP

# 4  cast sheets - only for a face this episode brings that has none yet
uv run python scripts/episode/cast_cards.py $BOOK --check      # what is wrong with the ones you have
uv run python scripts/episode/cast_cards.py $BOOK --prompts    # read the prompt before you pay for it
uv run python scripts/episode/cast_cards.py $BOOK --draw lestrade bust --approved      # PAID $0.08

# 5  storyboard prompts: agents write them, code refuses the bad ones
uv run python scripts/episode/sheet_dq.py   $BOOK $EP
uv run python scripts/episode/sheetcards.py $BOOK $EP          # -> sheets.html  READ IT BEFORE PAYING

# 6  draw the sheets                                            PAID ~$1.00 for six setups
uv run python scripts/episode/seq_boards.py   $BOOK $EP --approved=sheets
uv run python scripts/episode/sheetcards.py   $BOOK $EP         # the same page, now with the pictures
uv run python scripts/episode/redraw_panel.py $BOOK $EP S14.1 --approved   # one bad cell, $0.08

# 7  take prompts
uv run python scripts/episode/takecards.py  $BOOK $EP          # -> takes.html  READ IT BEFORE RENDERING

# 8  render, judge, retake                                      your GPU, hours
uv run python scripts/episode/takes_r2v.py  $BOOK $EP --approved
uv run python scripts/episode/take_dq.py    $BOOK $EP $(seq 0 22)
uv run python scripts/episode/takes_r2v.py  $BOOK $EP --retake=3,11 --approved

# 9  the title card, in two approvals: the picture first, then look at it, then
#    the animation, because the still is money and the animation is your queue
uv run python scripts/episode/title.py      $BOOK $EP --approved=title    # PAID $0.20, draws only
uv run python scripts/episode/title.py      $BOOK $EP --approved          # animates it too

# 10 cut, measure, publish
uv run python scripts/episode/assemble.py   $BOOK $EP --engine=r2v
uv run python scripts/episode/qc.py         $BOOK $EP --engine=r2v
uv run python scripts/episode/runcards.py   $BOOK $EP          # -> report_final.html

# and every time something is settled, record it WITH ITS REASON:
uv run python scripts/episode/story.py $BOOK $EP \
    --decide "END pins removed" --because "a second pin says nothing changes, and the take freezes"
uv run python scripts/episode/story.py $BOOK $EP --next "what happens next, one line"
"""

BRIEFS = [
    ("The author - one per setup, all at once",
     "Your setup is one location. Read the chapter, the plan and your peers' patches so the voice "
     "matches. For every panel write <b>frame</b> (the picture), <b>motion</b> (what happens in it), "
     "<b>camera</b> (where the lens stands, as a picture, with no move word in a still), "
     "<b>at_rest</b> (what stays still, so the drawer leaves it alone), and where the panel earns it, "
     "<b>end</b> + <b>changed</b> (the END picture, complete in its own right, and one sentence naming "
     "what moved, the frame edge it reached and its apparent size). Rules: say what IS, never what is "
     "not; the panel is the INSTANT BEFORE its action; no two panels of your setup may be the same "
     "picture; geometry as frame edges and apparent sizes, never &quot;ahead of&quot; or "
     "&quot;beside&quot;; every prop carries a size; anyone the words name is a person the render must "
     "be given a face for; public places carry named background people at their own work. Hand back a "
     "JSON patch for YOUR setup only. Edit no repo file, draw nothing, spend nothing."),
    ("Reviewer 1 - story and continuity",
     "You are the first to see all the setups together; each author saw only its own. Does this read as "
     "one continuous event in story order? Does every panel hand off to the next, inside a setup and "
     "across the cut between them? Is the same object the same object throughout, is the wardrobe state "
     "right for each place, does the time of day run forwards, does each END follow from its own motion? "
     "At most twelve findings, each naming the panel, the field, the fault, and the exact replacement."),
    ("Reviewer 2 - physical and optical sense",
     "Is every described picture possible, and do the pictures of one place agree? Vehicle and "
     "architectural geometry, eyelines, the 180-degree line, apparent sizes, light direction, the scale "
     "of a person against a door or a vehicle, and any relation written as a preposition rather than an "
     "edge and a size. Do the arithmetic: a 9:16 frame whose height holds a 9 ft 6 in hansom is 16 ft "
     "wide, which is the length of the rig, so it cannot stand at one edge and cross to the other."),
    ("Reviewer 3 - the rules, mechanically",
     "Measure, do not read. Per panel: zero negation; the instant before, never the action finished; no "
     "two panels alike in TEXT; end and changed present together; the wardrobe contract wherever it "
     "shows and untrimmed; crowd life in public setups; no camera move word in a still; every prop named "
     "in motion present in frame; every person the words name carried into the references; the panel "
     "count matching the grid. Verify with <code>uv run python -c</code> and paste the numbers."),
    ("The fixer, then the lints again",
     "Apply all three reviews. Where two reviewers disagree, rule and say why; push back on a finding "
     "you believe is wrong. Done means the plan validates, the sheet prompts all generate, sheet_dq "
     "passes, and the tests pass. Judgement is for agents, exactness is for code: never let an agent do "
     "a lint's job, and never let a lint decide a picture."),
]

ENTRY = [
    ("A chapter of a book already set up (voices, refs, plates)", "stage 1, lines", "the normal path"),
    ("A book with no cast voices yet", "voice design first", "the episode cannot begin; audio first is not negotiable"),
    ("A chapter bringing a character with no sheet", "cast_cards.py --check, then draw that one",
     "$0.08, and the faces rule then stages them everywhere the words name them"),
    ("A chapter in a location never drawn", "one plate, then that setup's sheet only",
     "--setup=&lt;name&gt; keeps the other sheets' money in your pocket"),
    ("An episode half rendered", "takes_r2v.py with no --retake",
     "it renders only what has no record; check no other run is alive FIRST, by command line -- `ps -W` prints none"),
    ("A cut that needs re-cutting, no new pictures", "assemble.py then qc.py",
     "costs nothing, and master_iterN never overwrites"),
    ("One bad cell in a good sheet", "redraw_panel.py &lt;book&gt; &lt;ep&gt; S14.1 --approved",
     "$0.08, and it leaves its neighbours alone"),
    ("A finished episode to review", "runcards.py, then read report_final.html",
     "every input and output per take, with the issues"),
]


SYMPTOMS = [
    ("A take is frozen, or starts on a still and moves a second later",
     "A second pin on that segment, a motion written out of stillness words, or -- upstream of both -- a "
     "shot whose value never turns.",
     "One pin per cell at its start and no end pins; give every segment a timed action a viewer can name; "
     "and check the shot is about something (stage 0, the turn)."),
    ("Renders suddenly taking half again as long",
     "Something else reached the GPU between two takes and the weights were evicted.",
     "Submit the whole run in one go, and never run a DQ while takes are in flight (stage 8)."),
    ("Walking looks like slow motion",
     "The word \"slow\" attached to a person; the turbo LoRA already pulls that way.",
     "Write the gait: he limps on his stick at a normal walking pace while the other walks normally."),
    ("The horse trots and the cab goes nowhere",
     "A locked-off frame in which nothing of the world moves.",
     "Make it travel: the cab crosses the frame, or the camera tracks it and the street passes behind."),
    ("A face is wrong, or a moustache is missing",
     "That person had no cast sheet staged. `faces` says whose face must READ, not who is in the room.",
     "Every person the shot's own words name is given their reference, derived from the text."),
    ("A prop is the wrong size in half the panels",
     "The contract named the prop and never sized it, so every panel invented one.",
     "Every prop states its length against the body, its thickness and where it sits; and check the "
     "contract was not silently trimmed on the way in."),
    ("Two panels on a sheet are the same picture",
     "Usually an END panel whose change cannot read at that shot size, or whose words said identical.",
     "Write the END as a picture in its own right; drop it when the only change is a small move in a wide."),
    ("A shot cuts back to something already seen",
     "The model was handed a picture it could not place: an unlabelled strip, or the plate called a shot.",
     "One labelled picture per pinned cell, each named as its shot's first frame; the plate is a definition."),
    ("The sheet comes back with no gutters and white lines through the cells",
     "The drawer ignored the grid.",
     "The cell gate catches it and one STRICT redraw fixes it; never ship the cut cells."),
    ("An episode runs long, or a line lands late",
     "Seconds written into the plan instead of measured off the voice.",
     "The plan carries no seconds; respot and timeline derive them, and QC measures the master against them."),
]

CHECKS = [
    ("Before you pay for the sheets", "sheets.html",
     "Read each panel's words against its neighbours. Is every one a different picture? Is each the "
     "instant before its action? Does the wardrobe contract appear wherever it shows, with sizes? Is the "
     "crowd named? Is the geometry edges and sizes rather than prepositions?"),
    ("After the sheets are drawn", "sheets.html again",
     "Now the pictures sit beside their words. Look for a panel that drew the action already finished, a "
     "twin of its neighbour, a prop at the wrong size, a face that is not the cast sheet. One bad cell is "
     "a $0.08 redraw, not a new sheet."),
    ("Before you spend a night of GPU", "takes.html",
     "Every input the model will be given, labelled. Check that every person on screen has a cast sheet, "
     "that the time ranges start at 0 and cover the take, that every range contains an action, and that "
     "the audio line is the one you expect."),
    ("After the master", "report_final.html",
     "The finished episode with every issue, every input and every output, and each shot's own seconds "
     "cut from the master beside the take that made them."),
]


STAGES = [
    ("0", "story.md — where it got to", "story.py &lt;book&gt; &lt;ep&gt; [--say] [--decide .. --because ..]", "free",
     "The one file that answers \"what is this and where did it got to\". The facts are regenerated off "
     "disk every run because they go stale the moment anything renders; the judgement -- what was settled, "
     "why, what is next -- is kept verbatim, because nothing on disk can reconstruct it. Read it before "
     "touching an episode you did not start, and say it back in three sentences.",
     "your own honesty: log the choice whose reason a stranger could not reconstruct, WITH the reason"),
    ("1", "The plan", "plan.json, written by hand or by a story agent", "free",
     "23 shots, 23 lines, six setups, no seconds anywhere. Lines name their shot; each shot carries "
     "frame, motion, camera, at_rest, and where it earns one end + changed. Validated by "
     "<code>studio/episode_spec.py</code>: one hook, one turn at 50-75 %, one button that is not the "
     "lead's, dialogue on a readable face, no location over ~25 s, routes never going backwards, "
     "every string affirmative.",
     "G1 PLAN: an action in every segment, no negation, no stillness word, no \"slow\" on a person, "
     "the wardrobe contract wherever a hand, hat or jacket shows, props named in motion present in "
     "frame, sub-shot faces named."),
    ("2", "Lines (AUDIO FIRST)", "say_lines.py &lt;book&gt; &lt;ep&gt; [--redo=18]", "free, local GPU",
     "Every line spoken by its cast voice on IndexTTS2 and measured. Whisper WER &lt;= 0.20 and ECAPA "
     "&gt;= 0.70; a redo keeps the better of the two tries; from the third try the reference is the "
     "speaker's own best line. Nothing downstream exists until this does: the picture is cut to the "
     "voice, never the other way round.",
     "the listen gate, twice, then your ear"),
    ("3", "Timeline", "respot.py then timeline.py", "free",
     "respot scales every sub-shot cut to the measured line lengths; timeline writes placed.json, "
     "where each shot's seconds are 0.25 + the lines it carries + 0.70 breath between them + 0.25 + "
     "beat + coda, snapped up to a whole frame.",
     "the sync rule: every line sits at its shot's start + 0.25, on the master and inside its take"),
    ("4", "Plates", "frames.py &lt;book&gt; &lt;ep&gt;", "free, local GPU",
     "One empty 9:16 plate per setup. No people: the plate defines the room and nothing else, which "
     "is why the prompt calls it a definition rather than a shot.",
     "eye"),
    ("5", "Cast sheets", "cast_cards.py &lt;book&gt; --draw &lt;who&gt; &lt;bust|indoor|outdoor&gt; --approved",
     "$0.08 each, PAID",
     "An identity bust and one wardrobe card per state. The sheet is the list of things the model is "
     "forbidden to invent, so every prop carries a size.",
     "studio/cast_agree.py: positive, unconditional, plain backdrop, one man, face fraction, hands clear"),
    ("6", "Storyboard prompts", "written by agents, then sheet_dq.py &lt;book&gt; &lt;ep&gt;", "free",
     "One sheet per setup, panels in story order, built in labelled blocks. One author per setup in "
     "parallel, then three reviewers across all of them, then one fixer. See the agent ladder below.",
     "G2 SHEET PROMPT: every panel a different picture, each the instant before its action, END panels "
     "naming a changed state, geometry as frame edges and sizes, crowd life in public setups, no camera "
     "move word in a still, contracts not silently trimmed"),
    ("7", "Storyboards", "seq_boards.py &lt;book&gt; &lt;ep&gt; --approved=sheets",
     "$0.13 a 3x2, $0.20 a 3x3, PAID",
     "gpt-image-2.5 draws each sheet from the plate and the cast sheets; cells are cut between the "
     "gutters found on the sheet. A failing sheet gets one STRICT redraw. One bad cell alone: "
     "<code>redraw_panel.py &lt;book&gt; &lt;ep&gt; S14.1 --approved</code>, $0.08, which leaves the good panels alone.",
     "G3 CELL: gutters, white lines, the landmark growing along the route, and NO TWO PANELS ALIKE at "
     "0.70 over every pair including a panel and its own END panel"),
    ("8", "Take prompts", "takecards.py &lt;book&gt; &lt;ep&gt;", "free",
     "Built by <code>studio/episode_ref_official.py</code> in MiniMax's ref2va grammar. Whole-second "
     "ranges that touch and cover the take, an action in every segment, affirmative only, 150-240 words "
     "a shot block. References, each one labelled: a cast sheet for everyone the shot's own words "
     "name (up to four, read out of the text rather than off a list), the plate, then one picture "
     "per pinned cell, and nothing else.",
     "the prompt lint, which refuses rather than sends: 18 rules, and build() raises on any negation"),
    ("9", "Takes", "takes_r2v.py &lt;book&gt; &lt;ep&gt; --approved", "free, local GPU, ~3.3 s a frame",
     "MiniMax-H3 ref2va with the Ref2V 8-step 768p LoRA at 1.0, euler/beta, sigma shift 12/3, "
     "768x1344. A take is a run of shots under 12 s in one setup. Every cell is pinned ONCE at its "
     "first token start; there are no end pins.",
     "G4 TAKE: frozen at start, frozen share, foreign picture, cut landing, drift, lip sync, identity; "
     "one score, best of N automatically, two retakes at most"),
    ("10", "Cut and QC", "assemble.py --engine=r2v then qc.py --engine=r2v", "free",
     "One segment per take-run, the bed 11 dB down with room tone, a gentle duck, lines at their placed "
     "times, the title card, a 0.25 s black tail. Kept as master_iterN.mp4, never overwritten.",
     "G5 MASTER: every segment is its take frame for frame, no duplicated frame across a cut, cuts "
     "within half a frame, then -15.5..-12.5 LUFS, TP &lt;= -1.0, every line heard"),
    ("11", "The pages", "sheetcards.py, takecards.py, runcards.py", "free",
     "sheets.html to validate the boards before drawing, takes.html to validate the prompts before "
     "rendering, report_final.html for the finished episode with every issue, input and output.",
     "your eye, which is the only gate that matters"),
]

RULES = [
    ("Audio first, always", "The plan carries no seconds. Every shot's length comes from its measured "
     "lines, so the picture is cut to the voice.", "the sync rule, owner-approved"),
    ("The panel is frame zero", "A cell shows the instant BEFORE its action. Six cells drawn at the "
     "climax gave the render nothing to do and it froze.", "measured: those six takes 60-95 % frozen"),
    ("One pin per cell, never two", "A pin is a soft conditioning row at a time, not a frame "
     "replacement. A second pin on a hold says \"nothing changes\" and the take freezes.",
     "71 segments: start + same cell 65 % frozen, start + END cell 59 %, start only 30 %"),
    ("No negation anywhere", "MiniMax reads none of it, and a negated noun is still that noun: our own "
     "board drew CRISTERION from a \"no signage\" clause.", "the builder raises on any negation"),
    ("Say what IS, with a number", "A relation written as \"ahead of\" drew a four-wheeler with the "
     "horse beside the axle. Frame edges and apparent sizes instead.",
     "the cab sheet, twice"),
    ("Every prop carries a size", "A contract is the list of things the model may not invent. \"A "
     "walking stick\" has no length, so 23 panels each guessed one.",
     "the cane came back the size of a lamp post"),
    ("An action a viewer can name", "Not a breathing face. A step, a head turned, a hand raised, a door "
     "pushed, a cab crossing the frame with the street passing.", "owner: a TV episode, not a poster"),
    ("A limp is a gait, not a speed", "\"Slow\" on a person renders as slow motion, and the turbo LoRA "
     "already pulls that way. Write the limp and a normal walking pace.", "measured on three walks"),
    ("An END panel must read at its own shot size", "A wide where the only change is a man moving two "
     "paces is the same picture twice, and no redraw will fix it.",
     "the gateway END failed four times before it was dropped"),
    ("A shot that turns no value has nothing to photograph", "McKee: mark the value at the open and "
     "again at the close, and if they read the same the shot is there to explain something. That is our "
     "freeze, one stage upstream of where we kept looking for it: we treated it as an engine fault, then "
     "a pin fault, then a prompt-vocabulary fault. It is all three, and underneath it is a shot that was "
     "never about anything. `Shot.turn` says \"before -> after\".",
     "studio/story_layer.py reports it; three iterations found it the expensive way"),
    ("One question, answered inside the episode", "Armstrong's form: \"Today, can X do Y?\" -- "
     "\"today\" makes it answerable in one episode and \"can\" makes the answer yes or no. An episode "
     "with no such question has no reason to stop where it stops.",
     "Succession season 4 holds to it every hour"),
    ("One GPU, one stage at a time", "Every take of a run is submitted before any is collected, so they "
     "execute consecutively and the weights load once. Then the whole DQ, then the whole retake batch. "
     "Never a DQ while takes are in flight: the lip-sync gate reaches Whisper through ComfyUI and every "
     "Whisper job evicts the video weights.",
     "measured: 407-583 s back to back against 742-998 s interleaved"),
    ("Whoever the words name gets their reference", "`faces` says whose face has to READ; it never said "
     "who is in the room. The names are read out of the shot's own frame, motion, camera, at_rest, end "
     "and changed, and every one of them is staged as a picture, up to four.",
     "18 of 19 takes staged nobody for a person their own scene named; the owner caught it as a missing "
     "moustache"),
    ("Every reference is a picture the model can place", "Each one is labelled and named as some shot's "
     "first frame. An unlabelled contact strip, or the plate handed over as though it were a shot, comes "
     "back as a cut to a picture nobody asked for.",
     "the strip was dropped; the plate is declared a definition"),
    ("Never spend on a habit", "Every paid picture and every render passes an approval gate that "
     "refuses unless the owner approved THAT kind. An approval for sheets does not buy a title card.",
     "it did once, which is why the gate exists"),
]

AGENTS = [
    ("One author per setup, in parallel", "Each writes only its own location's panel text, reading its "
     "peers' patches so the voice matches, and hands back a patch that is merged centrally. Six agents "
     "cannot collide if none of them can write the plan."),
    ("Three reviewers, across all setups", "Story and continuity; physical and optical sense; the rules "
     "mechanically. Each sees what the others cannot: the story reviewer found the time of day running "
     "backwards across four locations, the physical reviewer found a cab panel that is geometrically "
     "impossible, the rules reviewer found the wardrobe block ordering Watson drawn bareheaded on every "
     "sheet."),
    ("One fixer", "Applies all three, rules where they disagree, and says why. It should push back: "
     "ours refused to delete sixteen end-state pictures and corrected a reviewer on a fact."),
    ("Then the lints again, then draw", "Judgement is for agents. Exactness is for code. Never the "
     "other way round: a lint that costs a token and returns a different answer twice is not a lint."),
]


def rows(items, heads):
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in item) + "</tr>" for item in items)
    return f"<table class=lines><tr>{''.join(f'<th>{h}</th>' for h in heads)}</tr>{body}</table>"


def main() -> None:
    flow = "".join(
        f'<section id="s{n}" class=card><h2>{n}. {rc.esc(name)}</h2>'
        f"<div class=cols><div class=col><p><b>Command</b></p><pre>{cmd}</pre>"
        f"<p><b>Cost</b> {rc.esc(cost)}</p></div>"
        f"<div class=col><p>{what}</p><p><b>Gate:</b> {gate}</p></div></div></section>"
        for n, name, cmd, cost, what, gate in STAGES)
    head = (
        '<section id="top"><h2>A chapter becomes an episode</h2>'
        "<p>One chapter, one episode, two to three minutes, 9:16. First-person narration over pictures "
        "cut to the measured voice, in the chapter's own locations, drawn as one storyboard sequence per "
        "setup and rendered take by take on a local MiniMax-H3.</p>"
        "<p>Run the stages in order. Each one is free unless it says PAID, and every paid step and every "
        "GPU render refuses to start without your explicit approval on the command line. To start a new "
        "episode, the book needs its chapters parsed, its cast voices designed, and "
        "<code>refs/refs.json</code> with a physical description per character.</p></section>")
    sections = [head, flow,
                f'<section id="rules" class=card><h2>The rules, and what taught them</h2>'
                f'{rows([(f"<b>{rc.esc(a)}</b>", rc.esc(b), f"<i>{rc.esc(c)}</i>") for a, b, c in RULES], ("rule", "what it means", "evidence"))}</section>',
                f'<section id="agents" class=card><h2>Writing with agents</h2>'
                f'{rows([(f"<b>{rc.esc(a)}</b>", rc.esc(b)) for a, b in AGENTS], ("step", "how"))}</section>',
                '<section id="money" class=card><h2>What it costs</h2>'
                "<p>Pictures are the only money. A 3x2 sheet is $0.13, a 3x3 is $0.20, a single panel or a "
                "cast card is $0.08, the title still is $0.20. Six sheets for a six-setup episode is about "
                "$1.00 a pass, and a pass that needs strict redraws runs to about $1.60. Everything else is "
                "your own GPU: roughly 3.3 seconds of render per frame, so 160 seconds of picture is about "
                "three and a half hours.</p>"
                "<p>Every call is written to <code>library/&lt;book&gt;/spend.jsonl</code> by "
                "<code>studio/image_spend.py</code>. The OpenAI usage page is the truth; the ledger is an "
                "estimate calibrated against it.</p></section>",
                '<section id="files" class=card><h2>Where things land</h2>'
                "<pre>library/&lt;book&gt;/\n"
                "  refs/refs.json              the cast contracts\n"
                "  refs/characters/            cast sheets and their wardrobe cards\n"
                "  title/epNN.png|mp4          the episode's title card\n"
                "  spend.jsonl                 every paid call\n"
                "  episodes/epNN/\n"
                "    plan.json                 the episode, with no seconds in it\n"
                "    lines/                    every line as a wav, and lines.json\n"
                "    placed.json               the timeline, derived from the lines\n"
                "    frames/                   plates, sheets, cells, sheet_dq.json\n"
                "    shots_r2v/                every take, its graph, its DQ\n"
                "    master_iterN.mp4          the deliverable, never overwritten\n"
                "    sheets.html               validate the boards before drawing\n"
                "    takes.html                validate the prompts before rendering\n"
                "    report_final.html         the finished episode, every issue and input\n"
                "    findings.json             every issue with its evidence and status</pre></section>"]
    extra = [
        '<section id="run" class=card><h2>Episode 2, to copy and paste</h2>'
        "<p>Every line is safe to read first. Nothing here spends or renders without the "
        "<code>--approved</code> you type yourself.</p>"
        f"<pre>{rc.esc(RUN)}</pre></section>",
        '<section id="briefs" class=card><h2>The agent briefs, to paste into a fresh window</h2>'
        + "".join(f"<h3>{rc.esc(t)}</h3><p>{b}</p>" for t, b in BRIEFS) + "</section>",
        '<section id="entry" class=card><h2>Where a session actually starts</h2>'
        + rows([(f"<b>{rc.esc(a)}</b>", f"<code>{rc.esc(b)}</code>", rc.esc(d)) for a, b, d in ENTRY],
               ("what you have", "start at", "watch for")) + "</section>",
        '<section id="symptoms" class=card><h2>When it comes back wrong</h2>'
        + rows([(f"<b>{rc.esc(a)}</b>", rc.esc(b), rc.esc(d)) for a, b, d in SYMPTOMS],
               ("what you see", "what it actually is", "the fix")) + "</section>",
        '<section id="checks" class=card><h2>What to read at each approval</h2>'
        + rows([(f"<b>{rc.esc(a)}</b>", f"<code>{rc.esc(b)}</code>", rc.esc(d)) for a, b, d in CHECKS],
               ("moment", "page", "what to look for")) + "</section>",
    ]
    sections = [sections[0], extra[0]] + sections[1:4] + extra[1:] + sections[4:]
    nav = ('<a href="#top">start</a><a href="#run">episode 2</a>' + "".join(f'<a href="#s{n}">{n}. {name}</a>' for n, name, *_ in STAGES)
           + '<a href="#rules">rules</a><a href="#agents">agents</a><a href="#briefs">briefs</a>'
           '<a href="#entry">entry paths</a><a href="#symptoms">symptoms</a><a href="#checks">checks</a>'
           '<a href="#money">cost</a><a href="#files">files</a>')
    out = ROOT / "docs" / "episode_handbook.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(rc.page("The episode handbook — one chapter, end to end", nav, sections), encoding="utf-8")
    print(f"handbook -> {out}")


if __name__ == "__main__":
    main()
