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
    if speech_seconds(text) > 3.2:
        risk += 1.0
    return risk


def line_value(text: str, emotion: str | None, speaker: str,
               leads: tuple[str, ...]) -> float:
    """How well a line survives with no scene around it."""
    words = text.split()
    score = 0.0
    seconds = speech_seconds(text)
    score += 2.0 if 1.2 <= seconds <= 3.2 else (-1.5 if seconds > 4.0 else 0.5)
    if THEME.search(text):
        score += 1.4
    if speaker in leads:
        score += 1.5
    if emotion:
        score += 1.2 if not any(w in emotion.lower() for w in RISKY) else 0.4
    else:
        score -= 0.4
    if REPLY.match(text):
        score -= 3.0          # a reply's meaning lives in the line before it
    if UNBOUND.match(text):
        score -= 2.0          # "the ring" -- which ring?
    if any(w in text.lower() for w in CAUSAL):
        score -= 2.0          # a line with a "because" is an answer
    first = [w.strip(",.").lower() for w in words[:2]]
    if any(w in PRONOUNS for w in first):
        score -= 1.8
    if re.search(r"\d", text):
        score -= 2.5          # addresses and numbers need context
    if len(words) < 3 or len(words) > 18:
        score -= 2.5
    return score - 2.0 * synthesis_risk(text, emotion)


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
