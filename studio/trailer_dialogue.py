"""Choosing the few lines a trailer can actually speak.

A trailer line has to work with no scene around it.  That rules out most of a
screenplay: replies ("Do you mean that you are on the right track?") are
grammatically complete and semantically empty, because their meaning lives in
the line before them; and a line opening on an unbound "the ring" or "he" asks
the audience to remember something they were never told.

The budget is small and it is set by the music, not by taste: a cue's quiet
troughs are the only places a line can sit without fighting the bed.
"""
from __future__ import annotations

import math
import re

REPLY = re.compile(
    r"^(do you mean|you mean|i confess|that depends|i am rather|and (how|what|you)"
    r"|why, that|indeed|quite so|no, sir|yes, sir|well,|but |and |so |then )", re.I)
UNBOUND = re.compile(r"^(the|that|those|these)\s+[a-z]", re.I)
ANAPHORIC = {"it", "that", "he", "she", "they", "them", "him", "her"}
"""Openers that point BACK at something; deictic "this" points at the picture
and is how "This is Sparta" works, so it is not here."""
CAUSAL = ("because", "so that", "the reason", "that is why", "which is why")
THEME = re.compile(
    r"\b(man|men|soul|god|death|evil|truth|fear|murder|life|nature|two|myself"
    r"|human|sin|devil|mercy|madness|danger|blood|revenge|justice|face|name"
    r"|dead|kill|secret|hide|dark)\b", re.I)
THIRD_PERSON = re.compile(r"\b(he|she|him|her|his|hers|they|them|their|theirs)\b", re.I)
PRESENT = re.compile(r"\b(is|are|am|do|does|have|has|can|will|know|want|see|go"
                     r"|come|say|think|need)\b", re.I)
PAST = re.compile(r"\b(was|were|had|did|went|came|said|told|knew|saw|took|made"
                  r"|got|thought|wanted|been)\b", re.I)
PRONOUN_OPENERS = {"i", "we", "you", "he", "she", "it", "they"}
RISKY = {"desperate", "terrified", "explosive", "exultant", "hysterical",
         "weeping", "screaming", "shrieking", "sobbing", "near tears"}


def speech_seconds(text: str) -> float:
    """Roughly how long a line takes to say, at trailer delivery pace."""
    groups = len(re.findall(r"[aeiouy]+", text.lower())) or 1
    return round(0.22 * groups + 0.45, 2)


def synthesis_risk(text: str, emotion: str | None) -> float:
    """How likely a synthesised read is to give itself away.

    Emotional peak is what makes a line quotable AND what breaks TTS, so the
    two axes are positively correlated and a single ranked list hands you the
    worst possible slate.  This is subtracted from the selection score.
    """
    risk = 0.0
    if emotion and any(word in emotion.lower() for word in RISKY):
        risk += 1.0
    if "!" in text:
        risk += 1.0
    if "'" in text and re.search(r"\w'(?![st]\b)", text):
        risk += 1.0          # dialect elision: livin', o'
    if speech_seconds(text) > 6.0:
        risk += 1.0        # genuinely hard to synthesise, not merely long
    return risk


def is_parallel(text: str) -> bool:
    """True when two or more sentences open with the same content word.

    "The face supplied the fear.  The smell supplied the poison.  The ring
    supplied the woman."  Anaphora is what a line is built out of when it was
    written to be quoted.  Two sentences that both start "I" are narration,
    not rhetoric, so pronoun openers do not count.
    """
    openers = [s.strip().split()[0].lower()
               for s in re.split(r"(?<=[.!?])\s+", text) if s.strip().split()]
    openers = [o for o in openers if o.strip(",.'\"") not in PRONOUN_OPENERS]
    return len(openers) > 1 and len(openers) != len(set(openers))


def stance(text: str) -> float:
    """How far the line commits to a claim rather than running an errand.

    A question is not penalised: 18% of iconic trailer lines are questions,
    every one a hook the next line answers (research 1.2).
    """
    value = 0.0
    if re.match(r"^(i|we)\b", text.strip(), re.I):
        value += 1.2       # a speaker staking something on themselves
    if re.search(r"\b(never|always|every|no man|nothing|all)\b", text, re.I):
        value += 0.8       # an absolute claim needs no scene to be true in
    if is_parallel(text):
        value += 1.5
    if re.search(r"\b(ask|tell|send|fetch|step up|come along)\b", text, re.I):
        value -= 1.2       # an errand is stage direction with a voice
    return value


def length_band(words: int) -> float:
    """The trailer format is 3-12 words; past 14 the line becomes a paragraph."""
    if 3 <= words <= 12:
        return 1.0
    if words > 14:
        return -1.0 * ((words - 14) // 4)
    return 0.0


def generality(text: str) -> float:
    """Cornell (ACL 2012): memorable lines use indefinite articles, few
    third-person pronouns, present tense -- they are about anyone, now."""
    value = 0.6 if re.search(r"\b(a|an)\b", text, re.I) else 0.0
    value -= 0.8 * len(THIRD_PERSON.findall(text))
    if PRESENT.search(text):
        value += 0.5
    if PAST.search(text):
        value -= 0.6
    return value


def rarity(text: str) -> float:
    """Mean word length as a Zipf proxy for rarer words, clipped to [-1, 2].

    Per-book IDF distinctiveness needs a pool and lives in the ranker; this is
    the pool-free half of the same claim."""
    words = re.findall(r"[a-z]+", text.lower())
    if not words:
        return 0.0
    mean = sum(len(w) for w in words) / len(words)
    return max(-1.0, min(2.0, mean - 4.0))


def context_debt(text: str) -> float:
    """What the line owes to a scene the audience will not see."""
    debt = 0.0
    if REPLY.match(text):
        debt += 3.0          # a reply's meaning lives in the line before it
    if UNBOUND.match(text):
        debt += 2.0          # "the ring" -- which ring?
    if any(w in text.lower() for w in CAUSAL):
        debt += 1.0          # a line with a "because" is half of an argument
    first = [w.strip(",.").lower() for w in text.split()[:2]]
    if any(w in ANAPHORIC for w in first):
        debt += 1.8
    if re.search(r"\d", text):
        debt += 2.5          # addresses and numbers need context
    return debt


def line_value(text: str, emotion: str | None, speaker: str,
               leads: tuple[str, ...]) -> float:
    """How well a line survives with no scene around it.

    Two scorers were wrong here.  The first paid for SHORTNESS and put "No
    data yet." above the best line in the book.  The second, measured against
    38 real trailer lines, deleted half of them with `< 5 words -> -3.0` and
    every hook with `? -> -4.0`.  This one is graded on a corpus it was never
    tuned on (tests/fixtures/cornell_pairs.json, pairwise >= 0.55).

    Synthesis risk is not subtracted: on the held-out pairs it was the single
    strongest inverter, and it is a property of the ENGINE, which is why the
    slate keeps it beside the line for the card decision instead.
    """
    score = stance(text) + length_band(len(text.split())) + generality(text)
    score += rarity(text) - context_debt(text)
    if THEME.search(text):
        score += 1.4
    if speaker in leads:
        score += 0.8       # a modifier, not the bulk
    if emotion:
        score += 0.5 if not any(w in emotion.lower() for w in RISKY) else 0.2
    else:
        score -= 0.4
    if speech_seconds(text) > 8.0:
        score -= 2.0          # past this it is a paragraph, not a line
    return round(score, 4)


def dialogue_candidates(scenes: list[dict], restricted: set[int],
                        leads: tuple[str, ...]) -> list[dict]:
    """Every speakable line, scored, best first, one per speaker per scene."""
    seen: set[str] = set()
    found: list[dict] = []
    for scene in scenes:
        if scene["number"] in restricted:
            continue
        for element in scene.get("elements", []):
            if element.get("kind") != "dialogue" or not element.get("character"):
                continue
            text = (element.get("text") or "").strip()
            key = re.sub(r"[^a-z]", "", text.lower())[:60]
            if not text or key in seen:
                continue
            seen.add(key)
            found.append({
                "scene": scene["number"], "speaker": element["character"],
                "text": text, "emotion": element.get("emotion"),
                "seconds": speech_seconds(text),
                "risk": synthesis_risk(text, element.get("emotion")),
                "score": line_value(text, element.get("emotion"),
                                    element["character"], leads)})
    return sorted(found, key=lambda c: -c["score"])


def pick_lines(candidates: list[dict], count: int = 4,
               per_speaker: int = 2) -> list[dict]:
    """The few lines to actually speak, spread across speakers."""
    chosen: list[dict] = []
    used: dict[str, int] = {}
    for candidate in candidates:
        if len(chosen) >= count:
            break
        if used.get(candidate["speaker"], 0) >= per_speaker:
            continue
        chosen.append(candidate)
        used[candidate["speaker"]] = used.get(candidate["speaker"], 0) + 1
    return chosen


def assign_lines(beats: list[dict], lines: list[dict], ceiling: int = 4,
                 max_span: int = 2) -> dict[str, dict]:
    """Put each line on the beat that can carry it, spanning the cut if needed.

    Three hard conditions, each a way a line fails in a cut rather than a
    preference.  The SPEAKER must be in the shot the line STARTS on, or the
    audience hears a voice with no mouth.  The line must FINISH within the
    shots it is given, or the next line steps on it.  And a line belongs on the
    beat from its OWN scene where one exists -- over any other picture it stops
    being dialogue and becomes voice-over, asserting a link the book does not.

    A line may run across ONE cut.  Requiring it to fit inside a single 2.5s
    shot placed exactly one line in each of two trailers, which is not a
    dialogue pass; it is a caption.  What a trailer actually does is start the
    line on the speaker's face and let it carry over the picture that follows.
    """
    placed: dict[str, dict] = {}
    owned: set[int] = set()
    for line in sorted(lines, key=lambda c: -c["score"]):
        if len(placed) >= ceiling:
            break
        needed = speech_seconds(line["text"])
        best: tuple | None = None
        for index, beat in enumerate(beats):
            if index in owned or line["speaker"] not in beat["cast"]:
                continue
            room = 0.0
            for span in range(1, max_span + 1):
                if index + span > len(beats) or (index + span - 1) in owned:
                    break
                room += beats[index + span - 1]["seconds"]
                if room >= needed:
                    key = (beat.get("scene") != line["scene"], span, index)
                    if best is None or key < best[0]:
                        best = (key, index, span)
                    break
        if best is None:
            continue
        _, index, span = best
        placed[beats[index]["beat_id"]] = {**line, "span": span}
        owned.update(range(index, index + span))
    return placed


# ------------------------------------------------------------ ordering the slate

CONTENT_WORD = re.compile(r"[a-z']{4,}")
FUNCTION_WORDS = {"have", "has", "had", "been", "being", "will", "would", "shall", "should",
                  "could", "must", "does", "did", "than", "then", "there", "them", "they",
                  "what", "when", "which", "where", "your", "very", "some", "into", "upon",
                  "also", "only", "more", "most", "such", "much", "here", "these", "those",
                  "this", "with", "from", "were", "about", "shall"}
"""Four-letter-plus words that carry no content: `shares_content_word` related
two source quotes to 'You HAVE been in Afghanistan' on 'have' alone (run 10)."""
ORDER = ("hook", "answer", "threat", "button")
ROLE_KINDS = {"hook": ("hook",), "answer": ("stakes", "exposition"),
              "threat": ("threat", "stakes"), "button": ("button", "threat")}
"""The threat role falls back to stakes because the contract (LineSlate) needs
a threat OR stakes; a hook with only exposition after it is not a slate."""
DUCK_OVERRUN = 1.0
"""How far past its trough a line may run on the rubato path: the ducker's
release (08-assemble, `sidechaincompress ... release=1000`).  The bed's mid
band ducks under a line for as long as the line runs, so a line that ends
within one release of the trough's end is still inside the window one release
curve governs.  Scarlet run 6: slots of 2.6 and 2.0 s, the best hook 3.3 s,
music_only three runs in a row -- `rank` admitted the line at twice the
longest slot and `fits` refused it at the trough's edge."""
MAX_DUCKS = 2
"""A line that overruns its trough ducks the loud bed: a hole.  Two at most
(05-dialogue): the cue was chosen for its dynamic range, and six holes
destroy it.  A line inside its trough is not a duck, and neither is a line
in a MADE window: the phrase was chosen to be ducked, on the grid."""
WINDOW_BAND = (0.0, 0.8)
"""Where a window may open, as a share of the cue.

The low edge used to be 0.2, which on run 10's hundred-second cue meant no
line could be laid before twenty seconds -- so the hook landed at 38.9 s and
the trailer opened with half a minute of instrumental.  R2 asks for the hook
inside twelve seconds and the editor's rule asks for a line inside fifteen,
and neither is reachable while the first fifth of the cue is off limits.
The upper edge stays: a line laid over the title card is a caption."""

CARD_WORDS = 8
"""R9: a card is READ, and eight words is what a viewer reads in a shot.  Run
10 shipped an eighteen-word card and an eleven-word card back to back."""

HOOK_BY = 12.0
"""R2: how late a trailer may leave asking its question."""

MIN_SPOKEN = 3
SPOKEN_PER_100S = 5
"""R1: a trailer with one line in a hundred seconds is a music video with
pictures.  `music_only` is a refusal to be quoted back, not an outcome."""

VOICELESS_ROLES = ("hook", "button")
"""The narrator frames and raises stakes; the hook and the last word belong
to the people the story happens to."""
LINE_ROOM = 5.4
"""Seconds the longest admissible line takes: `trailer_plan.MAX_LINE_WORDS`
(14) at `speech_seconds`' 0.22 s a vowel group and the 1.6 groups a word
measured on Scarlet run 9's pool (34 lines).  A made window leaves this
much plus the two beats `fits` keeps at either end."""


def made_slots(metre) -> list:
    """One window per phrase start in the band: from the phrase start to the
    first later phrase start that leaves LINE_ROOM plus two beats, capped at
    the next hit so the line ends before the impact, never across it.

    Scarlet shipped music_only four runs running, waiting for troughs the
    music model does not reliably write; the grid always has phrases, and
    08-assemble ducks the bed's mid band under whatever line is laid on
    one.  A capped window shorter than a bar is not a window."""
    from studio.trailer_stage_spec import Slot
    room, hits = LINE_ROOM + 2 * metre.beat, metre.hits + [metre.title_hit or metre.seconds]
    low, high = (share * metre.seconds for share in WINDOW_BAND)
    out = []
    for start in (p for p in metre.phrase_starts if low <= p <= high):
        end = next((q for q in metre.phrase_starts if q >= start + room), None)
        if end is None:
            continue
        end = min([end] + [h for h in hits if start < h < end])
        if end - start >= metre.bar:
            out.append(Slot(start=start, end=round(end, 3), made=True))
    return out


def windows_of(metre) -> list:
    """Every window a line may take, in time order: the troughs the cue was
    measured with and, on a metre grid, the phrases the mix can duck.  A
    rubato cue has no phrases and keeps only its troughs."""
    return sorted(list(metre.slots) + made_slots(metre), key=lambda s: s.start)


def targets(slots: list, count: int) -> list[float]:
    """Where `count` lines should open to span the windows: evenly from the
    first window to the last, hook first and button last."""
    first, last = slots[0].start, slots[-1].start
    return [first + (last - first) * i / max(count - 1, 1) for i in range(count)]


def names_figure(text: str, figure: str) -> bool:
    """True when the line prints the figure's name: a capitalised word of the
    registry id ("Jefferson Hope").  Lower-case "hope" is a common word."""
    parts = [p for p in figure.split("_") if len(p) >= 3]
    return any(re.search(rf"\b{re.escape(p.capitalize())}\b", text) for p in parts)


def fits(seconds: float, slot, beat: float | None, overrun: float = 0.0) -> bool:
    """A line occupies whole beats: it starts on beat 2 of the slot's first bar
    and ends a beat before the music returns, so a 4-beat slot holds 2; the
    return is an L0 point and is never crossed.  Without a grid (rubato) the
    slot's seconds plus any `overrun` the duck budget allows are the budget."""
    if beat is None or beat <= 0:
        return seconds <= slot.seconds + overrun
    usable = math.floor(slot.seconds / beat + 1e-9) - 2
    return usable > 0 and math.ceil(seconds / beat - 1e-9) <= usable


def holds(slot, beat: float | None) -> float:
    """The seconds of speech a window holds under the fit rule."""
    if beat is None or beat <= 0:
        return slot.seconds
    return max(math.floor(slot.seconds / beat + 1e-9) - 2, 0) * beat


def refusal(role: str, candidates: list, slots: list, beat: float | None, measured: dict) -> str:
    """Why a role went unplaced, said so the LABELLER can act on it: it can
    label another line, or a shorter one; it cannot lengthen a window."""
    if not candidates:
        return f"no line is labelled {role}"
    shortest = min(line_seconds(l, measured) for l in candidates)
    longest = max(holds(s, beat) for s in slots)
    return (f"no {role} fits a window: the shortest {role} takes {shortest:.1f} s, the longest "
            f"window holds {longest:.1f} s; label shorter lines as {role}")


def line_seconds(line, measured: dict[str, float]) -> float:
    """MEASURED seconds when a voice file exists, else the prediction."""
    return measured.get(line.text) or speech_seconds(line.text)


def shares_content_word(a: str, b: str) -> bool:
    from studio.trailer_story import STOPWORDS
    wa = set(CONTENT_WORD.findall(a.lower())) - STOPWORDS - FUNCTION_WORDS
    wb = set(CONTENT_WORD.findall(b.lower())) - STOPWORDS - FUNCTION_WORDS
    return bool(wa & wb)


def closes_open(line) -> bool:
    """R8: a last word that leaves the question open -- a question, or a
    threat.  A trailer that answers itself has nothing left to sell."""
    return line.text.rstrip().endswith("?") or line.function == "threat"


def playable(role: str, line) -> bool:
    """Whether a line may play this role at all, before any preference.

    Two rules, both from run 10's master: a card longer than `CARD_WORDS` is
    a paragraph on screen (R9), and narration never asks the question or
    speaks the last word (R1) -- the narrator frames, he does not confront.
    """
    if line.speaker is None and line.words > CARD_WORDS:
        return False
    return not (role in VOICELESS_ROLES and line.pool == "narration")


def role_candidates(role: str, pool: list, hook, figure: str) -> list:
    """The lines that may play a role, best first.  A spoken line outranks a
    card (a line nobody speaks ships as text) at every role after the hook;
    the answer comes from another voice and should relate to the hook
    (Lieu's accent); the threat is the figure's own where the figure has
    one; a button is short."""
    kinds = ROLE_KINDS[role]
    found = [l for l in pool if l.function in kinds and playable(role, l)]
    if role == "answer":
        found = [l for l in found if l.speaker != hook.speaker]
        found.sort(key=lambda l: (l.speaker is None, not shares_content_word(l.text, hook.text)))
    elif role == "threat":
        found.sort(key=lambda l: (l.speaker is None, l.function != "threat", l.speaker != figure))
    elif role == "button":
        found = [l for l in found if l.words <= 6]
        found.sort(key=lambda l: (l.speaker is None, not closes_open(l)))
    return found


def overruns(line, slot, measured: dict) -> bool:
    """True when the line ends after a trough it was laid in: it will duck
    the bed.  A made window is ducked by design and spends nothing."""
    return not slot.made and line_seconds(line, measured) > slot.seconds


def allowance(placed: list, measured: dict) -> float:
    """How far the next line may overrun: one release while ducks remain."""
    spent = sum(overruns(line, slot, measured) for line, slot in placed)
    return DUCK_OVERRUN if spent < MAX_DUCKS else 0.0


def first_fit(candidates: list, slot, beat: float | None, measured: dict,
              overrun: float = 0.0) -> object | None:
    """The first candidate that fits the slot it would occupy; never atempo."""
    for line in candidates:
        if fits(line_seconds(line, measured), slot, beat, overrun):
            return line
    return None


def by_nearness(slots: list, target: float, after: float) -> list:
    """The windows opening at or after `after`, nearest the target first."""
    return sorted((s for s in slots if s.start >= after), key=lambda s: abs(s.start - target))


def place(candidates: list, slots: list, target: float, after: float, beat: float | None,
          measured: dict, overrun: float = 0.0) -> tuple | None:
    """The best candidate in the window nearest its aim that holds one: a
    window nothing fits is passed over for the next nearest."""
    for slot in by_nearness(slots, target, after):
        line = first_fit(candidates, slot, beat, measured, overrun)
        if line is not None:
            return line, slot
    return None


def roles_for(budget: int) -> tuple[str, ...]:
    """The spine's roles for `budget` windows: hook first, button last, and
    the middle alternating answer / threat.  Four windows are the classic
    order; with two the second must be the threat, because the contract
    needs a threat or stakes and exposition would spend the window.  A 100 s
    cut wants five or more lines (R1): the extra windows are more middle,
    not a fifth role."""
    if budget <= 2:
        return ORDER[:1] + ("threat",) * (budget - 1)
    if budget <= 4:
        return ORDER[:budget]
    middle = tuple(ORDER[1:3][i % 2] for i in range(budget - 2))
    return ORDER[:1] + middle + ORDER[3:]


def fill_roles(placed: list, pool: list, slots: list, budget: int, figure: str,
               beat: float | None, measured: dict) -> list:
    """The roles after the hook (`roles_for`), each aimed at its share of
    the span and placed in a window after the last line."""
    hook, aims = placed[0][0], targets(slots, budget)
    for aim, role in enumerate(roles_for(budget)[1:], start=1):
        found = place(no_second_card(role_candidates(role, pool, hook, figure), placed),
                      slots, aims[aim], placed[-1][1].end, beat, measured,
                      allowance(placed, measured))
        if found is not None:
            placed.append(found)
            pool = [l for l in pool if l is not found[0]]
    return placed


def no_second_card(candidates: list, placed: list) -> list:
    """R9: never two cards in a row.  Two cards back to back is a page, and
    run 10 put an eighteen-word one next to an eleven-word one."""
    if placed and placed[-1][0].speaker is None:
        return [l for l in candidates if l.speaker is not None]
    return candidates


def wanted_speech(runtime: float, ceiling: int) -> int:
    """R1: how many lines this trailer must actually SAY.

    Scaled by the picture's own length, never by a constant: a twenty-five
    second cut and a hundred second cut are different films.  The contract
    (`LineSlate.MAX_LINES`) is the ceiling.
    """
    want = math.ceil(SPOKEN_PER_100S * max(runtime, 0.0) / 100.0)
    return min(max(MIN_SPOKEN, want), ceiling)


def speech_refusal(lines: list, wanted: int) -> str | None:
    """R1's refusal, said so the LABELLER can act on it."""
    spoken = [l for l in lines if l.speaker]
    if len(spoken) >= wanted:
        return None
    return (f"the slate speaks {len(spoken)} line(s) and this trailer needs {wanted}; "
            f"label more spoken lines as hook, stakes, threat or button")


def button_refusal(lines: list) -> str | None:
    """R8's refusal: the last thing said leaves the question open."""
    spoken = [l for l in lines if l.speaker]
    if not spoken or closes_open(spoken[-1]):
        return None
    return (f"the last spoken line {spoken[-1].text!r} closes the trailer; "
            f"label a question or a threat as the button")


def hook_refusal(lines: list, by: float = HOOK_BY) -> str | None:
    """R2's refusal: a trailer asks its question in the first twelve seconds."""
    hook = next((l for l in lines if l.function == "hook" and l.window), None)
    if hook is None or hook.window.start <= by:
        return None
    return (f"the hook opens at {hook.window.start:.1f} s and a trailer asks its "
            f"question inside {by:.0f} s; label a shorter line as hook")


def story_refusal(slate, runtime: float, ceiling: int) -> str | None:
    """The first story rule this slate breaks, or None.  Separate from the
    contract on purpose: the contract says what a slate IS, these say what a
    trailer DOES, and only the second set is worth a second labelling."""
    for refusal_ in (speech_refusal(slate.lines, wanted_speech(runtime, ceiling)),
                     hook_refusal(slate.lines), button_refusal(slate.lines)):
        if refusal_:
            return refusal_
    return None


def order_lines(top: list, slots: list, figure: str, *, measured: dict | None = None,
                beat: float | None = None, iconicity: str = "none"):
    """Hook -> answer -> threat -> (title) -> button, one line per window.

    The number of lines is the number of windows, bounded by the lines
    offered and the contract's ceiling (`MAX_LINES`); the roles
    (`roles_for`) aim at even shares of the span (`targets`) and each line is chosen for
    the window it will occupy, from its measured seconds where a voice file
    exists.  Every line carries its window out.  A line naming the figure is
    out before anything else: the trailer sells the question of who, and
    the answer is not a line.
    """
    from studio.trailer_stage_spec import MAX_LINES, LineSlate
    if not slots:
        raise ValueError("no slots: nothing to put a hook in")
    measured = measured or {}
    pool = [l for l in top if not names_figure(l.text, figure)]
    if not pool:
        raise ValueError("no lines to order: the slate is empty or names only the figure")
    budget = min(len(slots), len(pool), MAX_LINES)
    hooks = role_candidates("hook", pool, None, figure)
    first = place(hooks, slots, targets(slots, budget)[0], 0.0, beat, measured,
                  allowance([], measured))
    if first is None:
        raise ValueError(refusal("hook", hooks, slots, beat, measured))
    placed = fill_roles([first], [l for l in pool if l is not first[0]], slots, budget, figure,
                        beat, measured)
    if not {l.function for l, _ in placed} & {"threat", "stakes"}:
        raise ValueError("a hook with no threat or stakes after it")
    return LineSlate(lines=[l.model_copy(update={"window": s}) for l, s in placed],
                     iconicity=iconicity)
