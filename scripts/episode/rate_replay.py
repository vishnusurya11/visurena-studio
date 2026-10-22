#!/usr/bin/env python
"""Does a line project better at its own speaker's rate?  Leave-one-episode-out, read-only (A15).

    uv run python scripts/episode/rate_replay.py <codex> [<codex> ...]

Craft ruling 2026-10-21, A15: `plan_gates.measured_rate` gives every unvoiced line one blended rate
(Jekyll ep01 2.45 w/s; its narrator speaks 2.23, Enfield 2.96, Utterson 3.06).  The proposed fallback
is per speaker (5 or more voiced lines), per kind, blended, then STUDIO_RATE, and it ships ONLY IF it
beats the blended rate out of sample over every voiced lines.json; a pause term ships only if it wins
out of sample too.  For each episode this projects every passed line from the book's OTHER episodes
and prints the mean absolute error, in seconds, of the blended rate, the per-speaker fallback and a
pause model (seconds = a x words + b x breaks, least squares).  It changes no projection: the verdict
line says what ships.  Reads `episodes/epNN/audio/lines/lines.json` by name (the HDD rule).  $0.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import plan_gates  # noqa: E402

MIN_LINES = 5
"""A speaker (or a kind) gets its own rate from this many voiced lines."""
BREAK = re.compile(r"[,;:—]|[.!?](?=\s)")
MODES = ("blended", "speaker", "pause")


def voiced(doc) -> list[dict]:
    """The rows of a lines.json that were heard: text, measured seconds, passed."""
    rows = doc["lines"] if isinstance(doc, dict) and "lines" in doc else doc
    return [r for r in rows or [] if isinstance(r, dict) and r.get("text") and r.get("seconds") and r.get("passed", True)]


def words(row: dict) -> int:
    return len(str(row["text"]).split())


def rate(rows: list[dict]) -> float | None:
    w, s = sum(words(r) for r in rows), sum(float(r["seconds"]) for r in rows)
    return w / s if w and s else None


def speaker_rates(rows: list[dict]) -> dict[str, float]:
    """{speaker: words a second} for every speaker with MIN_LINES voiced lines."""
    names = {r.get("speaker") for r in rows}
    mine = {n: [r for r in rows if r.get("speaker") == n] for n in names}
    return {n: rate(rs) for n, rs in mine.items() if len(rs) >= MIN_LINES}


def rate_for(line: dict, train: list[dict]) -> float:
    """Per speaker, then per kind, then blended, then the studio's measured rate."""
    for key in ("speaker", "kind"):
        same = [r for r in train if r.get(key) == line.get(key)]
        if len(same) >= MIN_LINES:
            return rate(same)
    return rate(train) or plan_gates.measured_rate([])


def pause_fit(train: list[dict]) -> tuple[float, float]:
    """(seconds a word, seconds a break) by least squares over the training lines."""
    import numpy as np
    x = np.array([[words(r), len(BREAK.findall(str(r["text"])))] for r in train], float)
    coef, *_ = np.linalg.lstsq(x, np.array([float(r["seconds"]) for r in train]), rcond=None)
    return float(coef[0]), float(coef[1])


def project(line: dict, train: list[dict], mode: str) -> float:
    """The seconds a model gives a line it has not heard."""
    if mode == "pause":
        a, b = pause_fit(train)
        return a * words(line) + b * len(BREAK.findall(str(line["text"])))
    return words(line) / (rate_for(line, train) if mode == "speaker" else rate(train) or plan_gates.measured_rate([]))


def episodes(book: Path) -> dict[str, list[dict]]:
    paths = sorted(Path(book).glob("episodes/ep[0-9][0-9]/audio/lines/lines.json"))
    found = {p.parts[-4]: voiced(json.loads(p.read_text(encoding="utf-8"))) for p in paths}
    return {k: v for k, v in found.items() if v}


def errors(eps: dict[str, list[dict]]) -> dict[str, list[float]]:
    """Each model's absolute error on every line of every episode, fitted on the book's others."""
    out: dict[str, list[float]] = {m: [] for m in MODES}
    for held, test in eps.items():
        train = [r for k, v in eps.items() if k != held for r in v]
        for line in test if train else []:
            for mode in MODES:
                out[mode].append(abs(project(line, train, mode) - float(line["seconds"])))
    return out


def loo(books: list[Path]) -> dict:
    """{lines, blended, speaker, pause}: mean absolute error in seconds, pooled over the books."""
    pooled: dict[str, list[float]] = {m: [] for m in MODES}
    for book in books:
        for mode, errs in errors(episodes(book)).items():
            pooled[mode] += errs
    n = len(pooled["blended"])
    return {"lines": n, **{m: round(sum(e) / n, 3) if n else None for m, e in pooled.items()}}


def verdict(out: dict) -> str:
    """What ships, by the ruling's bar: per-speaker only if it beats blended out of sample."""
    if not out["lines"]:
        return "per-speaker not measured: no episode has another to fit on; nothing ships"
    head = (f"per-speaker wins: MAE {out['speaker']} s against blended {out['blended']} s over {out['lines']} lines"
            if out["speaker"] < out["blended"] else
            f"per-speaker does not win: MAE {out['speaker']} s against blended {out['blended']} s over "
            f"{out['lines']} lines; nothing ships")
    return head + f" | pause model {out['pause']} s ({'wins' if out['pause'] < out['blended'] else 'does not win'})"


def main(argv: list[str]) -> int:
    from studio import episode_home
    out = loo([episode_home.book_dir(c) for c in argv])
    print(out)
    print(verdict(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
