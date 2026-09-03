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

import re

REPLY = re.compile(
    r"^(do you mean|you mean|i confess|that depends|i am rather|and (how|what|you)"
    r"|why, that|indeed|quite so|no, sir|yes, sir|well,|but |and |so |then )", re.I)
UNBOUND = re.compile(r"^(the|that|those|this|these)\s+[a-z]", re.I)
PRONOUNS = {"it", "that", "this", "he", "she", "they", "them", "him", "her"}
CAUSAL = ("because", "so that", "the reason", "that is why", "which is why")
THEME = re.compile(
    r"\b(man|men|soul|god|death|evil|truth|fear|murder|life|nature|two|myself"
    r"|human|sin|devil|mercy|madness|danger|blood|revenge|justice|face|name"
    r"|data|dead|kill|secret|hide|dark)\b", re.I)
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
    """True when two or more sentences open with the same word.

    "The face supplied the fear.  The smell supplied the poison.  The ring
    supplied the woman."  Anaphora is what a line is built out of when it was
    written to be quoted, and it is cheap to detect and impossible to fake.
    """
    openers = [s.strip().split()[0].lower()
               for s in re.split(r"(?<=[.!?])\s+", text) if s.strip().split()]
    return len(openers) > 1 and len(openers) != len(set(openers))


def stance(text: str) -> float:
    """How far the line commits to a claim rather than seeking one."""
    value = 0.0
    stripped = text.strip()
    if stripped.endswith("?"):
        return -4.0        # a question's answer is the next line, and there is none
    if re.match(r"^(i|we)\b", stripped, re.I):
        value += 1.2       # a speaker staking something on themselves
    if re.search(r"\b(never|always|every|no man|nothing|all)\b", text, re.I):
        value += 0.8       # an absolute claim needs no scene to be true in
    if is_parallel(text):
        value += 1.5
    if re.search(r"\b(ask|tell|send|fetch|step up|come along)\b", text, re.I):
        value -= 1.2       # an errand is stage direction with a voice
    return value


def line_value(text: str, emotion: str | None, speaker: str,
               leads: tuple[str, ...]) -> float:
    """How well a line survives with no scene around it.

    The previous version scored SHORTNESS -- +2.0 for under 3.2s, -1.5 over
    4.0s, -2.5 over eighteen words -- and so ranked "No data yet." above the
    best line in A Study in Scarlet.  Length is not the property.  A line fails
    in a trailer because it is a reply, a question, an errand or an unbound
    reference, and it succeeds because it makes a claim that stands alone.

    Duration is left to `assign_lines`, which knows how long the SHOT is.  Only
    genuinely unspeakable length is penalised here.
    """
    words = text.split()
    score = stance(text)
    if THEME.search(text):
        score += 1.4
    if speaker in leads:
        score += 0.8       # a modifier, not the bulk
    if emotion:
        score += 0.5 if not any(w in emotion.lower() for w in RISKY) else 0.2
    else:
        score -= 0.4
    if REPLY.match(text):
        score -= 3.0          # a reply's meaning lives in the line before it
    if UNBOUND.match(text):
        score -= 2.0          # "the ring" -- which ring?
    if any(w in text.lower() for w in CAUSAL):
        score -= 1.0          # a line with a "because" is half of an argument
    first = [w.strip(",.").lower() for w in words[:2]]
    if any(w in PRONOUNS for w in first):
        score -= 1.8
    if re.search(r"\d", text):
        score -= 2.5          # addresses and numbers need context
    if len(words) < 5:
        score -= 3.0          # too little said to be worth stopping for
    if speech_seconds(text) > 8.0:
        score -= 2.0          # past this it is a paragraph, not a line
    return score - 1.2 * synthesis_risk(text, emotion)


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
