#!/usr/bin/env python
"""The craft census (A1, craft ruling 2026-10-21): one $0 counter over a plan and its take prompts.

    uv run python scripts/episode/craft_lint.py <codex> <n>

Counts, per take, the craft defects no lint refuses today, so every later fix has a base rate to
quote: a hold head renamed "keeps" past L2, the "now in frame" arrival, "walking pace", a speech
verb beside a closed mouth, a sky word on a night setup, a 6-word run said twice, an `end` written
as a camera sentence, and the mechanical garbles.  The CLI reads the RENDERED prompts off each
take's own `T<NN>.graph.json` (on Jekyll ep01, 27 of 28 `prompts.json` entries are not what
rendered); step 06 prints the same line over the cards it just built.  Report only: it never
parks a run and never refuses a take.  Reads named files only (the HDD rule).
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import house_style, take_currency  # noqa: E402
from studio.take_inputs import night_of  # noqa: E402,F401  (one night rule for the census and QC)

DD = re.compile(r"detailed_description:\n(.*?)(?:\n\n[a-z_]+:|\Z)", re.S)
SENTENCE = re.compile(r"(?<=[.!?])(?<!\bMr\.)(?<!\bMrs\.)(?<!\bDr\.)\s+(?=[A-Z<])")
SPOKEN = re.compile(r"<d>.*?</d>", re.S)
SPEECH = re.compile(r"\b(?:speak|speaks|speaking|says|saying|answers?|answering|asks?|asking|talks?|"
                    r"screams?|shouts?|cries|replies|replying|tells?)\b", re.I)
GARBLE = re.compile(r",,|\.,|\s,|with the camera \w+(?: \w+)? now in frame")
CAMERA_END = re.compile(r"^\s*the camera\b|\bcamera\b[^.;]{0,30}?\b(?:pushes|pulls back|pulls out|tracks|pans|"
                        r"tilts|dollies|cranes|orbits|zooms|racks|rises|holds)\b", re.I)
"""An `end` that opens "The camera" or gives the camera a move; a bare verb is not one ("he pans
for gold", "cart tracks": wave 0 review finding 10)."""
BLOCK = re.compile(r"\[Shot \d+\] From \d\d:\d\d to (\d\d:\d\d)\.(.*?)(?=\[Shot \d+\]|\Z)", re.S)
INSERT_SCOPE = "only that object and what touches it is in frame"
SUBJECT = re.compile(r"<Subject (\d+)>")
BOILER = ("continues to the last frame of the shot", "through the last frame", "at the first frame the focus",
          "the frame's height", "mouth shapes every syllable")
"""The builder's fixed sentences: said in every block by design, so never a repeat."""
SMALL = 3
"""A class with this many hits or fewer names its takes in the line."""


def detailed(prompt: str | None) -> str:
    """The prompt's `detailed_description` section (style line + blocks), or "" when it has none."""
    hit = DD.search(prompt or "")
    return hit.group(1).strip() if hit else ""


def body(dd: str) -> str:
    """The blocks without the style line and without the spoken words (a line is the book's)."""
    return SPOKEN.sub(" ", dd.split("\n", 1)[1] if "\n" in dd else "")


def sentences(text: str) -> list[str]:
    return [s.strip() for s in SENTENCE.split(text) if s.strip()]


def renamed_hold(dd: str) -> int:
    """1 when the first camera sentence (not "The camera is ...") holds under the word "keeps"."""
    heads = [s for s in sentences(body(dd)) if s.startswith("The camera ") and not s.startswith("The camera is ")]
    return int(bool(heads) and heads[0].startswith("The camera keeps"))


def now_in_frame(dd: str) -> int:
    return dd.count("now in frame")


def walking_pace(dd: str) -> int:
    """Every literal "walking pace" (ep01: 8 in 5 takes).  Seven of them are the gait tautology
    ("walks at a walking pace", 4 takes); T01's is "at a normal walking pace" on a walk, the form
    the ruling benches before it is cut (T19)."""
    return dd.lower().count("walking pace")


def speech_closed(dd: str) -> int:
    """Sentences that close a mouth and give the same face a speech verb (ep01 T13)."""
    return sum(1 for s in sentences(body(dd)) if "mouth is closed" in s and SPEECH.search(s))


def sky_at_night(dd: str, night: bool) -> int:
    """Sky words (sun, daylight, dawn ...) in a night setup's description, style line included."""
    return len(house_style.SKY_SOURCE.findall(dd)) if night else 0


def six_word_repeat(dd: str) -> int:
    """Distinct 6-grams said twice or more in the blocks, the builder's fixed sentences aside.  The
    unit is the overlapping 6-gram: one repeated 10-word phrase counts 5 (the line says "6-grams")."""
    text = re.sub(r"\d\d:\d\d", "", body(dd).lower())
    for fixed in BOILER:
        text = text.replace(fixed, " | ")              # a fixed sentence breaks a run, never makes one
    runs = Counter(" ".join(chunk[i:i + 6]) for part in text.split("|")
                   if (chunk := re.findall(r"[a-z<>0-9']+", part)) for i in range(len(chunk) - 5))
    return sum(1 for n in runs.values() if n > 1)


def garbles(dd: str) -> int:
    """Doubled or orphaned commas, and a camera verb pasted into the arrival ("with the camera tilts up")."""
    return len(GARBLE.findall(body(dd)))


def beat_at_end(dd: str) -> int:
    """A beat stamped "At <the block's last second>": nothing can start on the last frame
    (A18: T03 and T11, "At 00:05" in a block that ends at 00:05)."""
    return sum(len(re.findall(rf"\bAt {end}\b", text)) for end, text in BLOCK.findall(dd))


def insert_second_body(dd: str) -> int:
    """Blocks whose insert scope ("only that object and what touches it") stands over a second body
    (A18: T07, the girl running into the boots insert)."""
    return sum(INSERT_SCOPE in text and len(set(SUBJECT.findall(text))) >= 2 for _, text in BLOCK.findall(dd))


def end_camera(shots: list) -> list[int]:
    """Plan shots whose `end` opens with "The camera" or carries a camera verb (ep01 shot 6)."""
    return [int(_get(s, "index")) for s in shots if CAMERA_END.search(str(_get(s, "end") or ""))]


def _get(row, key):
    return row.get(key) if isinstance(row, dict) else getattr(row, key, None)


TAKE_CLASSES = (("renamed hold", renamed_hold), ("now in frame", now_in_frame), ("walking pace", walking_pace),
                ("speech beside a closed mouth", speech_closed), ("repeated 6-grams", six_word_repeat),
                ("garble", garbles), ("beat at block end", beat_at_end),
                ("insert scope with a second body", insert_second_body))


def census(prompts: dict, night: dict, shots: list) -> dict[str, dict[int, int]]:
    """{class: {take or shot: hits}} -- only the ones that hit.  An unreadable prompt counts nothing."""
    texts = {int(i): detailed(p) for i, p in prompts.items()}
    out = {name: {i: n for i, dd in texts.items() if (n := rule(dd))} for name, rule in TAKE_CLASSES}
    out["sky word at night"] = {i: n for i, dd in texts.items() if (n := sky_at_night(dd, bool(night.get(i))))}
    out["end as camera"] = {i: 1 for i in end_camera(shots)}
    return out


def readable_census(prompts: dict, night: dict, shots: list) -> tuple[dict[str, dict[int, int]], int]:
    """The census over the prompts that carry a `detailed_description`, and how many did: an
    unreadable prompt is not a clean take (wave 0 review: n counted it, every class at 0)."""
    readable = {int(i): p for i, p in prompts.items() if detailed(p)}
    return census(readable, night, shots), len(readable)


def said(name: str, hits: dict[int, int]) -> str:
    """`walking pace 8 in 5`, `speech beside a closed mouth 1 (T13)`, `end as camera 1 (shot 6)`."""
    total = sum(hits.values())
    text = f"{name} {total}" + (f" in {len(hits)}" if total != len(hits) else "")
    if hits and len(hits) <= SMALL:
        tag = "shot " if name == "end as camera" else "T"
        text += " (" + " ".join(f"{tag}{i}" if tag == "shot " else f"T{i:02d}" for i in sorted(hits)) + ")"
    return text


def line(counts: dict[str, dict[int, int]], n: int) -> str:
    """The one line every step 06 report carries."""
    return f"craft census, {n} takes (report only): " + "; ".join(said(k, v) for k, v in counts.items())


def recorded(take_dir: Path, records: list[dict]) -> dict[int, str]:
    """{take: the prompt it RENDERED from}, off each take's own graph; a take with none is left out."""
    got = {int(r["index"]): take_currency.recorded_prompt(Path(take_dir) / f"T{int(r['index']):02d}.mp4")
           for r in records}
    return {i: p for i, p in got.items() if p is not None}


def episode_census(home: Path) -> tuple[dict[str, dict[int, int]], int]:
    """The census over an episode folder: plan.json, takes/r2v/shots.json and the rendered graphs."""
    home = Path(home)
    plan = json.loads((home / "plan.json").read_text(encoding="utf-8"))
    take_dir = home / "takes" / "r2v"
    records = json.loads((take_dir / "shots.json").read_text(encoding="utf-8"))
    prompts = recorded(take_dir, records)
    setups = plan.get("setups") or {}
    night = {int(r["index"]): night_of(setups[r["setup"]]) for r in records if r.get("setup") in setups}
    return readable_census(prompts, night, plan.get("shots") or [])


def built_line(episode, built: list[dict]) -> str:
    """Step 06's line over the cards it just built (what will render), against the plan's setups."""
    prompts = {int(c["index"]): c.get("prompt") for c in built}
    night = {int(c["index"]): night_of(episode.setups[c["setup"]]) for c in built
             if c.get("setup") in episode.setups}
    counts, n = readable_census(prompts, night, list(episode.shots))
    if not n and prompts:
        return f"craft census: not measured (0 of {len(prompts)} cards carry a detailed_description)"
    return line(counts, n)


def main(argv: list[str]) -> int:
    from studio import episode_home
    book = episode_home.book_dir(argv[0])
    counts, n = episode_census(episode_home.home(book, int(argv[1])))
    print(line(counts, n))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
