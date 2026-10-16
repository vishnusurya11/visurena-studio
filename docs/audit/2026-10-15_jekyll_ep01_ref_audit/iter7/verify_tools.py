"""iter7 VERIFY tools (copied from iter5): (1) the staged references of every kept take, by hash, against the current card
pictures (G-TAKE-INPUTS, read off the graphs); (2) per-scene contact sheets in the 03_visual_qa.md form
(the scene's sheets in the left column, four frames per take: start, 1/3, 2/3, end).

    uv run python docs/audit/2026-10-15_jekyll_ep01_ref_audit/iter7/verify_tools.py refs
    uv run python docs/audit/2026-10-15_jekyll_ep01_ref_audit/iter7/verify_tools.py sheets
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from PIL import Image  # noqa: E402

from studio import take_inputs  # noqa: E402

BOOK = ROOT / "library/20260827135504_the-strange-case-of-dr-jekyll-and-mr-hyde"
EP = BOOK / "episodes/ep01"
TAKES = EP / "takes/r2v"
HERE = Path(__file__).parent
SCENES = {"door_day": [0, 1, 2, 22], "night_cross_street": [3, 4, 5, 6, 7], "night_door": [8, 9, 10],
          "pavement_day": [11, 12, 18, 19, 20, 21], "sunday_street": [13, 14, 15, 16, 17]}
CAST = {"door_day": ["gabriel_john_utterson", "richard_enfield"],
        "night_cross_street": ["richard_enfield", "edward_hyde", "child_of_hyde_incident"],
        "night_door": ["richard_enfield", "edward_hyde"],
        "pavement_day": ["gabriel_john_utterson", "richard_enfield"],
        "sunday_street": ["gabriel_john_utterson", "richard_enfield"]}
CELL = 300


def refs() -> None:
    cards = json.loads((TAKES / "prompts.json").read_text(encoding="utf-8"))
    rows, current = [], 0
    for c in cards:
        take = TAKES / f"T{c['index']:02d}.mp4"
        got = take_inputs.check(take, take_inputs.card_pictures(c, BOOK, 1))
        current += bool(got.current)
        rows.append({"take": f"T{c['index']:02d}", "current": bool(got.current), "staged": sorted(got.staged),
                     "stale": sorted(got.stale), "missing": sorted(got.missing), "refs": c["refs"]})
    (HERE / "staged_refs_iter7.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
    print(f"inputs: {current} of {len(cards)} takes current")


def frames(take: Path, n: int = 4) -> list[Image.Image]:
    import cv2
    cap = cv2.VideoCapture(str(take))
    dur = cap.get(cv2.CAP_PROP_FRAME_COUNT) / (cap.get(cv2.CAP_PROP_FPS) or 24)
    cap.release()
    out = []
    for k in range(n):
        t = min(dur - 0.05, dur * k / (n - 1))
        raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", f"{t:.2f}", "-i", str(take), "-frames:v", "1",
                              "-vf", f"scale={CELL}:{CELL}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                             capture_output=True).stdout
        out.append(Image.frombytes("RGB", (CELL, CELL), raw) if len(raw) == CELL * CELL * 3 else Image.new("RGB", (CELL, CELL)))
    return out


def sheet(scene: str) -> Path:
    takes, cast = SCENES[scene], CAST[scene]
    rows = max(len(takes), len(cast))
    canvas = Image.new("RGB", (CELL * 5, CELL * rows), (15, 16, 18))
    for i, who in enumerate(cast):
        s = Image.open(BOOK / f"refs/characters/{who}/sheet_front.png").convert("RGB")
        s.thumbnail((CELL, CELL))
        canvas.paste(s, (0, i * CELL))
    for r, t in enumerate(takes):
        for k, f in enumerate(frames(TAKES / f"T{t:02d}.mp4")):
            canvas.paste(f, ((k + 1) * CELL, r * CELL))
    out = HERE / f"scene_{scene}.jpg"
    canvas.save(out, quality=88)
    return out


if __name__ == "__main__":
    if sys.argv[1] == "refs":
        refs()
    else:
        for scene in SCENES:
            print(sheet(scene))
