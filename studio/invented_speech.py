"""INVENTED SPEECH: words H3 speaks in the silent tail of its voice guide (owner, 2026-10-11).

The guide is the recorded line padded with digital silence to the take's length.
H3 writes its own soundtrack, and in that padding it has been heard to go on
talking ("...a man indeed. Indeed.", "Dead! ... HAHAHAHAHAHA!").  The master
drops H3's audio, but the mouth moves and the picture ships, so a word in the
tail is a picture fault.

    speech_end   where the guide's speech ends (last 50 ms window above SILENT_DB)
    check        the take's audio from there + MARGIN_S: a tail quieter than
                 QUIET_DB is silent (never sent to the ear, which hallucinates
                 on silence); a sounding tail is heard, and every word is invented
    motion_ratio mean frame-to-frame change of the lower face in the tail over
                 the same during the line (advisory until calibrated)
"""
from __future__ import annotations

import re
from typing import Callable

import numpy as np

SILENT_DB = -45.0
QUIET_DB = -45.0
MARGIN_S = 0.25
WIN_S = 0.05


def rms_db(x: np.ndarray) -> float:
    r = float(np.sqrt(np.mean(np.square(x, dtype=np.float64)))) if len(x) else 0.0
    return 20 * np.log10(r) if r > 0 else -120.0


def speech_end(guide: np.ndarray, sr: int) -> float:
    """Seconds at the end of the last window of the guide louder than SILENT_DB."""
    win = max(1, int(WIN_S * sr))
    loud = [i for i in range(0, len(guide), win) if rms_db(guide[i:i + win]) > SILENT_DB]
    return (loud[-1] + win) / sr if loud else 0.0


def words_of(text: str) -> list[str]:
    return re.findall(r"[a-z']+", (text or "").lower())


def extra(line: list[str], said: list[str]) -> list[str]:
    """The words the take says after the last word it shares with the line."""
    from difflib import SequenceMatcher
    blocks = [b for b in SequenceMatcher(None, line, said, autojunk=False).get_matching_blocks() if b.size]
    return said[blocks[-1].b + blocks[-1].size:] if blocks else said


def check(take: np.ndarray, guide: np.ndarray, sr: int, hear: Callable) -> dict:
    """{'passed', 'line_end_s', 'tail_s', 'tail_db', 'words', 'heard'} for one take.  A
    sounding tail sends the WHOLE take and the WHOLE guide to the ear (a tail heard
    alone hallucinates: 'see you next week' on the S4 control's room tone)."""
    end = speech_end(guide, sr)
    tail = take[int((end + MARGIN_S) * sr):]
    out = {"line_end_s": round(end, 2), "tail_s": round(len(tail) / sr, 2),
           "tail_db": round(float(rms_db(tail)), 1), "words": [], "heard": ""}
    if len(tail) >= int(0.2 * sr) and out["tail_db"] > QUIET_DB:
        out["heard"] = hear(take)
        out["words"] = extra(words_of(hear(guide)), words_of(out["heard"]))
    return {**out, "passed": not out["words"]}


def change(frames: list[np.ndarray]) -> float:
    return float(np.mean([np.abs(b - a).mean() for a, b in zip(frames, frames[1:])])) if len(frames) > 1 else 0.0


def motion_ratio(during: list[np.ndarray], tail: list[np.ndarray]) -> float:
    """Lower-face motion in the tail as a share of the motion during the line."""
    base = change(during)
    return round(change(tail) / base, 3) if base else 0.0


# ---- G-TAIL: the production gate on dialogue takes (C1_verdict #7, 2026-10-11) ----------
#
# Replayed over all 204 shipped dialogue takes (C1_A_evidence/shipped_fixed.rows.json):
# fails exactly wotw ep10/T21 ("Moving!") and ep26/T25 (mouth branch); exempts the
# prompt-asked mouths; the 5 overwritten early-Scarlet guides read unmeasurable.

ASKED = re.compile(r"\b(?:laugh\w*|call(?:s|ed|ing)?|shout\w*|yell\w*|pant(?:s for|ing|ed)|eat(?:s|ing)?|"
                   r"drink\w*|bite\w*|chew\w*|gasp\w*|cough\w*|sob\w*|mouth)\b", re.I)
"""A post-line clause that ASKS the mouth to move: the take obeys it (3/3 measured)."""
OPEN_FLOOR, OPEN_SHARE = 0.06, 0.3
"""A mouth is open at max(OPEN_FLOOR, OPEN_SHARE x the line's p90 aperture) (C1_A §1)."""
OPEN_RUN, RISES = 6, 2
STALE_S = 1.0
"""A guide whose speech ends this far from placed.json's line end was overwritten:
the 5 stale Scarlet guides sit 1.19-3.18 s off, every live guide within 0.68 s."""
MOUTH_ARMED = True
"""The mouth branch, armed: 0 false fails over the replay (C1_verdict #7's condition)."""


AFTER = re.compile(r"\bAt \d+:\d+, as the line ends,[^.]*\.?", re.I)


def after_line(prompt: str) -> str:
    """The prompt's clauses timed after the line (`episode_ref_official`: 'At 00:03, as the line ends, ...')."""
    return " ".join(m.group(0).strip() for m in AFTER.finditer(prompt or ""))


def asked_mouth(after: str) -> bool:
    return bool(ASKED.search(after or ""))


def stale(guide_end: float | None, placed_end: float | None) -> bool:
    return guide_end is not None and placed_end is not None and abs(guide_end - placed_end) > STALE_S


def open_run(ap: np.ndarray, threshold: float) -> tuple[int, int]:
    """(longest run of open frames, rises from shut to open) over a tail's apertures."""
    open_ = np.nan_to_num(np.asarray(ap, dtype=float)) >= threshold
    longest = run = rises = 0
    for k, now in enumerate(open_):
        run = run + 1 if now else 0
        longest = max(longest, run)
        rises += int(now and k > 0 and not open_[k - 1])
    return longest, rises


def mouth_speaks(run: int, rises: int) -> bool:
    return MOUTH_ARMED and run >= OPEN_RUN and rises >= RISES


def tail_state(ship_db: float | None, words: list, mouth: bool, asked: bool, stale: bool) -> str:
    """pass | fail | exempt | unmeasurable for one dialogue take's shipped tail."""
    if stale:
        return "unmeasurable"
    if ship_db is None or ship_db <= QUIET_DB or not (words or mouth):
        return "pass"
    return "exempt" if asked else "fail"


def tail_row(got: dict | None):
    """HARD.  Unmeasurable or unmeasured passes (it can tell nothing) with no value."""
    from studio.take_verdict import Gate

    st = (got or {}).get("state")
    if st in (None, "unmeasurable"):
        return Gate("tail", None, True, True, f"cannot tell: {st or 'not measured'}")
    note = f"{st}: tail {got.get('ship_db')} dB, words {got.get('words') or []}, mouth {got.get('mouth')}"
    return Gate("tail", got.get("ship_db"), st != "fail", True, note, 0.0 if st != "fail" else 30.0)
