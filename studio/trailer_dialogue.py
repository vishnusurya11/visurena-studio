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
ORDER = ("hook", "answer", "threat", "button")
ROLE_KINDS = {"hook": ("hook",), "answer": ("stakes", "exposition"),
              "threat": ("threat", "stakes"), "button": ("button",)}
"""The threat role falls back to stakes because the contract (LineSlate) needs
a threat OR stakes; a hook with only exposition after it is not a slate."""


def names_figure(text: str, figure: str) -> bool:
    """True when the line prints the figure's name: a capitalised word of the
    registry id ("Jefferson Hope").  Lower-case "hope" is a common word."""
    parts = [p for p in figure.split("_") if len(p) >= 3]
    return any(re.search(rf"\b{re.escape(p.capitalize())}\b", text) for p in parts)


def fits(seconds: float, slot, beat: float | None) -> bool:
    """A line occupies whole beats: it starts on beat 2 of the slot's first bar
    and ends a beat before the music returns, so a 4-beat slot holds 2.
    Without a grid (rubato) the slot's seconds are the whole budget."""
    if beat is None or beat <= 0:
        return seconds <= slot.seconds
    usable = math.floor(slot.seconds / beat + 1e-9) - 2
    return usable > 0 and math.ceil(seconds / beat - 1e-9) <= usable


def line_seconds(line, measured: dict[str, float]) -> float:
    """MEASURED seconds when a voice file exists, else the prediction."""
    return measured.get(line.text) or speech_seconds(line.text)


def shares_content_word(a: str, b: str) -> bool:
    from studio.trailer_story import STOPWORDS
    wa = set(CONTENT_WORD.findall(a.lower())) - STOPWORDS
    wb = set(CONTENT_WORD.findall(b.lower())) - STOPWORDS
    return bool(wa & wb)


def role_candidates(role: str, pool: list, hook, figure: str) -> list:
    """The lines that may play a role, best first.  The answer comes from
    another voice and should relate to the hook (Lieu's accent); the threat
    is the figure's own where the figure has one; a button is short."""
    kinds = ROLE_KINDS[role]
    found = [l for l in pool if l.function in kinds]
    if role == "answer":
        found = [l for l in found if l.speaker != hook.speaker]
        found.sort(key=lambda l: not shares_content_word(l.text, hook.text))
    elif role == "threat":
        found.sort(key=lambda l: (l.function != "threat", l.speaker != figure))
    elif role == "button":
        found = [l for l in found if l.words <= 6]
    return found


def first_fit(candidates: list, slot, beat: float | None, measured: dict) -> object | None:
    """The first candidate that fits the slot it would occupy; never atempo."""
    for line in candidates:
        if fits(line_seconds(line, measured), slot, beat):
            return line
    return None


def fill_roles(hook, pool: list, slots: list, budget: int, figure: str,
               beat: float | None, measured: dict) -> list:
    """Answer, threat, button after the hook, each against the slot it lands
    in.  With only two slots the second must be the threat: the contract
    needs a threat or stakes, and exposition would spend the slot."""
    chosen = [hook]
    for role in ORDER[1:] if budget > 2 else ("threat",):
        if len(chosen) >= budget:
            break
        pick = first_fit(role_candidates(role, pool, hook, figure), slots[len(chosen)],
                         beat, measured)
        if pick is not None:
            chosen.append(pick)
            pool = [l for l in pool if l is not pick]
    return chosen


def order_lines(top: list, slots: list, figure: str, *, measured: dict | None = None,
                beat: float | None = None, iconicity: str = "none"):
    """Hook -> answer -> threat -> (title) -> button, one line per slot.

    The number of lines is the number of slots, capped at four; each line is
    chosen for the slot it will occupy, from its measured seconds where a
    voice file exists.  A line naming the figure is out before anything else:
    the trailer sells the question of who, and the answer is not a line.
    """
    from studio.trailer_stage_spec import MAX_LINES, LineSlate
    if not slots:
        raise ValueError("no slots: nothing to put a hook in")
    measured, budget = measured or {}, min(len(slots), MAX_LINES)
    pool = [l for l in top if not names_figure(l.text, figure)]
    hook = first_fit(role_candidates("hook", pool, None, figure), slots[0], beat, measured)
    if hook is None:
        raise ValueError("no hook fits the first slot")
    chosen = fill_roles(hook, [l for l in pool if l is not hook], slots, budget, figure,
                        beat, measured)
    if not {l.function for l in chosen} & {"threat", "stakes"}:
        raise ValueError("a hook with no threat or stakes after it")
    return LineSlate(lines=chosen, iconicity=iconicity)
