"""Record G-WHO's real reads of judged pictures into a test fixture (Jekyll ep06 retro B, 2026-10-29).

    uv run --no-sync python scripts/audit/who_fixture.py <book_id> <episode> <cases.json> <out.json>

cases.json: [{"case": "panel_25_v1", "image": "<book-relative png>", "faces": [...], "setup": "<setup>",
              "double_by_eye": true}, ...]

Each image is read with the G-WHO ask (the panel reader's own `read_who`, seed 19, cached), and the staged
marks of its cast are written beside the eye's answer.  tests/test_g_who_replays_its_calibration_set.py replays
every fixture under the CURRENT rule: a rule change that stops firing on an eye-confirmed double, or starts
firing on a picture the eye passed, fails before it lands (ep06: the fair/grey fix hid panel 25's double).
Reads go through ComfyUI's VL model ($0, local); run it when the GPU is idle."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import cast_refs, episode_home  # noqa: E402


def record(book: Path, number: int, case: dict) -> dict:
    from scripts.episode import panel_content_check as pcc
    setup = episode_home.load_plan(book, number).setups.get(case["setup"])
    figures = pcc.read_who(book / case["image"])
    cast = {name: {"markers": m, "top": top} for name, m, top in markers_of(book, case["faces"], setup)}
    return {"take": case["case"], "image": case["image"], "double_by_eye": bool(case["double_by_eye"]),
            "cast": cast, "frames": [figures]}


def markers_of(book: Path, faces: list[str], setup) -> list[tuple]:
    from studio import continuity
    out = []
    for name, markers in zip(faces, cast_refs.look_markers(book, faces, setup)):
        row = cast_refs.row(book, name)
        out.append((name, markers, continuity.top_for(book, name, continuity.look_for(setup, name, row), row)))
    return out


def main(book_id: str, number: int, cases: Path, out: Path) -> None:
    book = episode_home.book_dir(book_id)
    rows = [record(book, number, c) for c in json.loads(Path(cases).read_text(encoding="utf-8"))]
    Path(out).write_text(json.dumps({"book": book.name, "episode": number, "takes": rows}, indent=1), encoding="utf-8")
    print(f"{len(rows)} case(s) -> {out}")


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4]))
