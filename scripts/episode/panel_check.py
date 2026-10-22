#!/usr/bin/env python
"""The panel gate: judge every storyboard panel of an episode, before any take.

    uv run python scripts/episode/panel_check.py <book_id> <episode>

Writes episodes/epNN/storyboard/panel_dq.json, which takes_r2v refuses to
render without (audit 2026-09-22, item 5). Exits 1 when any panel fails, any
planned panel is missing, or there is nothing to judge -- a gate that measured
nothing has passed nothing (item 6).

Promoted from a session driver. What changed on the way in:
- WHO MAY BE IN A PANEL comes from the plan: the setup's declared crowd and
  the shot's `extras`. The driver guessed a crowd from people-words in the
  prose with no word boundaries, which stood the people check down on about
  80% of panels (items 1-2).
- THE HOUR comes from the setup's words (`panel_dq.at_night`), not from any
  "dark" in the shot's prose, which sent 15 of ep09's 23 daylight panels to
  the night control (item 36).
- The sharpness CONTROLS stay the two calibrated house wides. Measured against
  each setup's own place picture instead, owner-accepted ep06/ep07 panels
  scored down to 0.26 against a 0.5 floor, so that control was worse.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
from PIL import Image

from studio import episode_home, face_end, panel_dq
from studio.episode_home import episode_arg

CONTROL_PLACE = "horsell_common"
CONTROLS = {"day": "wide_establishing.png", "night": "wide_night.png"}
"""Two pictures drawn in the house style and accepted; a panel is soft when
its hardest edges are under SHARP_FLOOR of the control for its own hour."""


def strength(path: Path) -> float:
    return panel_dq.edge_strength(np.asarray(Image.open(path).convert("RGB")))


def controls(book: Path) -> dict[str, float]:
    """The house wides where the book has them; else the book's OWN place
    pictures, median per hour (Jekyll ep01 crashed opening WotW's wides)."""
    folder = Path(book) / "refs" / "locations" / CONTROL_PLACE
    if all((folder / name).exists() for name in CONTROLS.values()):
        return {hour: strength(folder / name) for hour, name in CONTROLS.items()}
    return own_controls(sorted((Path(book) / "refs" / "locations").glob("*/*.png")))


def own_controls(pictures: list[Path]) -> dict[str, float]:
    night = [strength(p) for p in pictures if "night" in p.stem]
    day = [strength(p) for p in pictures if "night" not in p.stem]
    day_c = float(np.median(day)) if day else float(np.median(night))
    return {"day": day_c, "night": float(np.median(night)) if night else day_c}


def seam_of(board: Path, index: int, frame: np.ndarray) -> bool:
    """A paper-white seam in the panel H3 is staged (storyboard/h3/), else in the cell."""
    staged = Path(board) / "h3" / f"shot_{index:02d}.png"
    return bool(panel_dq.seams(np.asarray(Image.open(staged).convert("RGB")) if staged.exists() else frame))


def judge(shot, setup, frame: np.ndarray, control: dict[str, float], seam: bool = False) -> dict:
    """One panel's verdict, with who may be in it read from the plan."""
    hour = "night" if panel_dq.at_night(setup.described) else "day"
    found = face_end.faces(frame)
    row = panel_dq.verdict(
        faces=panel_dq.confident_faces(found), present=panel_dq.present_faces(found),
        planned=len(shot.faces or []),
        sharp=panel_dq.edge_strength(frame) / control[hour],
        ink=panel_dq.inkiness(frame), tiled=panel_dq.tiledness(frame),
        crowd=bool((setup.crowd or "").strip()), size=shot.size,
        extras=getattr(shot, "extras", 0), prose=f"{shot.frame} {shot.at_rest}",
        stacked=panel_dq.stacked(frame), seam=seam)
    row["shot"], row["hour"] = shot.index, hour
    return row | framing_rows(shot, found)


def framing_rows(shot, found: list[dict]) -> dict:
    """G-FRAME (C2_verdict #8) and the push-on-a-wide-cell note (shot framework B-4): recorded beside the
    verdict, never in its flags."""
    from studio import framing_grammar
    record = panel_dq.frame_record(found, len(shot.faces or []), getattr(shot.size, "value", shot.size),
                                   f"{shot.frame} {shot.at_rest}")
    move = framing_grammar.verb(shot) if getattr(shot, "motion", "") else "locked"
    return record | panel_dq.push_on_wide_cell(record, move)


def main(book_id: str, number: int) -> int:
    book = episode_home.book_dir(book_id)
    ep = episode_home.load_plan(book, number)
    home = episode_home.home(book, number) / "storyboard"
    control = controls(book)
    rows, missing = [], []
    for shot in ep.shots:
        path = home / f"shot_{shot.index:02d}.png"
        if not path.exists():
            missing.append(shot.index)
            continue
        frame = np.asarray(Image.open(path).convert("RGB"))
        row = judge(shot, ep.setups[shot.setup], frame, control, seam_of(home, shot.index, frame))
        rows.append(row)
        print(f"  {'ok  ' if row['passed'] else 'FAIL'} shot {shot.index:02d}  "
              f"faces {row['cast_faces']}/{row['planned']}  sharp {row['sharp']:.2f} ({row['hour']})  "
              f"ink {row['ink']:.4f}  tiled {row['tiled']:.2f}  {','.join(row['flags'])}"
              + (f"\n        {row['push_note']}" if row.get("push_note") else ""), flush=True)
    episode_home.write_json(home / "panel_dq.json", rows)
    failed = [r["shot"] for r in rows if not r["passed"]]
    print(f"\n{len(rows) - len(failed)}/{len(ep.shots)} panels pass; failing {failed}; missing {missing}")
    if not rows:
        print(f"no panels under {episode_home.relative(book, home)}: nothing was measured, so nothing passed")
    return 1 if (failed or missing or not rows) else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], episode_arg(sys.argv)))
