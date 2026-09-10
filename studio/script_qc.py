"""Did the finished cut deliver the page it was written from?

THE GAP THIS FILLS.  Two independent research passes found the same hole: no
published automatic-trailer system commits to a beat template, cuts against
it, and then measures the finished artifact for conformance.  Systems that
have structure evaluate the SELECTOR (did it find the gold turning-point
shots); systems that produce a cut evaluate it with a Likert scale or with
similarity to real trailers.  Nobody asks the artifact whether it has the
shape it promised.

Our own QC could not see it either.  Run 19 measured loudness, cut counts and
speech occupancy and reported "floor pass" on a trailer whose first act was
0.7 s of 106 -- because nothing had ever said it should have a first act.

So this measures the MASTER against the PAGE: the runtime it promised, the
act shares it promised, where it said the title would land, and how much of it
speaks.  Every number here is checkable by someone else on the finished file.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from pydantic import BaseModel

from studio.trailer_assemble import TARGET_LUFS, TARGET_TP
from studio.trailer_script import QUOTA_SLACK, RUNTIME, RUNTIME_SLACK, TrailerScript
from studio.trailer_story import MOVEMENTS, QUOTA_SHARES

DRIFT = 0.5
"""Seconds the master may differ from the page before the cut is not the page."""

SPEECH_FLOOR = 0.20
"""The share of the runtime that must carry a line.  Run 19 shipped 0.115 and
the owner's verdict was "no dialogues"; measured practice is 41-45%, and this
is the floor under which the complaint is simply true."""


class ScriptQC(BaseModel):
    """What the finished file measured, against what the page promised."""

    seconds: float
    promised: float
    shares: dict[str, float]
    speech: float
    title_at: float
    lufs: float | None = None
    peak: float | None = None

    @property
    def misses(self) -> list[str]:
        """Every promise the master did not keep, by name."""
        out = []
        if abs(self.seconds - self.promised) > DRIFT:
            out.append("runtime")
        if abs(self.seconds - RUNTIME) > RUNTIME_SLACK:
            out.append("format")
        out += [f"act_{m}" for m in MOVEMENTS
                if abs(self.shares.get(m, 0.0) - QUOTA_SHARES[m]) > QUOTA_SLACK]
        if self.speech < SPEECH_FLOOR:
            out.append("speech")
        if self.lufs is not None and not (TARGET_LUFS - 1.5 <= self.lufs <= TARGET_LUFS + 1.5):
            out.append("loudness")
        if self.peak is not None and self.peak > TARGET_TP + 0.5:
            out.append("peak")
        return out

    @property
    def delivered(self) -> bool:
        return not self.misses


def seconds_of(path: Path) -> float:
    """The master's own length, read off the file rather than assumed."""
    # -v info, not error: the "Duration:" line IS ffmpeg's info output, and
    # quieting it is what left this fallback with nothing to read.
    proc = subprocess.run(
        ["ffmpeg", "-v", "info", "-i", str(path), "-f", "null", "-"],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    try:
        found = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "json", str(path)], capture_output=True, text=True,
            encoding="utf-8", errors="replace")
        if found.returncode == 0 and found.stdout.strip():
            return round(float(json.loads(found.stdout)["format"]["duration"]), 2)
    except (FileNotFoundError, OSError):
        pass                      # no ffprobe on this box; ffmpeg reports it too
    return _from_stderr(proc.stderr)


def _from_stderr(text: str) -> float:
    """Duration off ffmpeg's own report, for a box with no ffprobe."""
    for line in text.splitlines():
        if "Duration:" in line:
            clock = line.split("Duration:")[1].split(",")[0].strip()
            hours, minutes, seconds = clock.split(":")
            return round(int(hours) * 3600 + int(minutes) * 60 + float(seconds), 2)
    raise RuntimeError("no duration in ffmpeg's report")


def loudness_of(path: Path) -> dict:
    """Integrated loudness and true peak of the finished master."""
    proc = subprocess.run(
        ["ffmpeg", "-v", "info", "-i", str(path), "-af",
         "loudnorm=print_format=json", "-f", "null", "-"],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    body = proc.stderr[proc.stderr.rfind("{"):proc.stderr.rfind("}") + 1]
    found = json.loads(body)
    return {"lufs": float(found["input_i"]), "peak": float(found["input_tp"])}


def title_share(page: TrailerScript) -> float:
    """Where the title card lands, as a share of the runtime."""
    title = next((b for b in page.beats if b.function == "title"), None)
    return page.share_at(title) if title else 0.0


def measure(page: TrailerScript, master: Path, spoken: float | None = None) -> ScriptQC:
    """The master read back against the page that asked for it."""
    heard = loudness_of(master)
    said = page.speech_seconds() if spoken is None else spoken
    return ScriptQC(seconds=seconds_of(master), promised=page.seconds,
                    shares=page.movement_shares(), speech=round(said / page.seconds, 3),
                    title_at=title_share(page), lufs=heard["lufs"], peak=heard["peak"])
