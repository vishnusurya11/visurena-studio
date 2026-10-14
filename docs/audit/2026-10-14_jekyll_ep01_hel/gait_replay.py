"""Replay G-GAIT (studio/gait.py) over every take whose plan asks a subject to walk.

    uv run python docs/audit/2026-10-14_jekyll_ep01_hel/gait_replay.py <book_dir> <ep>... > out.jsonl

One JSON row per walker take: book, episode, take, shots, state, freq, step_h,
travel_hps.  CPU only (YOLOv10m via OpenCV DNN, Farneback flow)."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from studio import gait, take_lock  # noqa: E402

detect = gait.yolo()
book = Path(sys.argv[1])
for ep in sys.argv[2:]:
    home = book / "episodes" / f"ep{int(ep):02d}"
    plan = json.loads((home / "plan.json").read_text(encoding="utf-8"))
    motion = {s["index"]: s.get("motion") or "" for s in plan["shots"]}
    room = home / "takes" / "r2v"
    shots = room / "shots.json"
    if not shots.exists():
        continue
    for rec in json.loads(shots.read_text(encoding="utf-8")):
        run = rec.get("shots") or [rec["index"]]
        text = " ; ".join(motion.get(i, "") for i in run)
        video = room / f"T{rec['index']:02d}.mp4"
        if not gait.walks(text) or not video.exists():
            continue
        m = gait.measure(take_lock.frames(video, None), detect=detect)
        print(json.dumps({"book": book.name[15:30], "ep": int(ep), "take": rec["index"], "shots": run} | m), flush=True)
