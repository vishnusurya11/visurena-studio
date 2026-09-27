"""Where a dialogue line is laid in the master: where its take spoke it.

ep13 T11 (2026-09-27): MiniMax-H3 wrote the take's soundtrack 1.08 s after the
wav was laid and drove the mouth to THAT soundtrack; the master laid the line
at the planned time, so the voice was over before the lips moved.  The edit
lays it where the take put it, and QC listens there.
"""
from __future__ import annotations

from pathlib import Path

from studio import episode_home

LAG_TOL = 0.042
"""take_verdict.LAG_TOL: a lag inside it is the measure's own noise."""


def laid_at(line: dict, lag: float | None, shot_end: float) -> float:
    """A dialogue line at its take's soundtrack, never past its shot; narration as planned."""
    at = float(line["at"])
    if line.get("kind") != "dialogue" or not lag or abs(lag) <= LAG_TOL:
        return at
    return round(min(at + lag, shot_end - float(line.get("seconds", 0.0))), 3)


def take_lag(take_dir: Path, shot: int) -> float | None:
    """The take's measured soundtrack lag (take_dq's `mux_lag_s`), or None."""
    path = Path(take_dir) / f"T{int(shot):02d}.dq.json"
    return ((episode_home.read_json(path) or {}).get("audio") or {}).get("mux_lag_s") if path.exists() else None


def laid_lines(placed: dict, take_dir: Path) -> list[dict]:
    """placed.json's lines, each `at` where the master lays it."""
    ends = {s["index"]: s["t_end"] for s in placed["shots"]}
    return [{**l, "at": laid_at(l, take_lag(take_dir, l["shot"]), ends[l["shot"]])} for l in placed["lines"]]
