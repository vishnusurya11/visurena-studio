"""The girl in T05-T07 against her NEW sheet's row, list-then-judge (the take identity row reads
"0 cast on screen": facenet finds no face on a small cel child).  Three frames a take; the VLM
lists the little girl's headwear colour, garment colour, sleeve colour and hair colour; code
compares with the row (grey bonnet, grey pinafore, dark-red sleeves, fair hair).  Writes
girl_identity.json.  Usage: girl_identity.py [takes dir]"""
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from studio import look_back  # noqa: E402
from studio.judges import sheet_row  # noqa: E402
from studio.judges.look_state import unwrap  # noqa: E402

TAKES = ROOT / "library/20260827135504_the-strange-case-of-dr-jekyll-and-mr-hyde/episodes/ep01/takes/r2v"
COLOURS = sorted(set(sheet_row.COLOURS.values()))
ASK = ("Look at the little GIRL in this picture (a child, not a man). Output strict JSON with keys "
       '"girl_seen" (true/false), "bonnet", "garment", "sleeves", "hair", each one of '
       + ", ".join(COLOURS) + ', or "unseen".')
WANT = {"bonnet": {"grey"}, "garment": {"grey", "red"}, "sleeves": {"red", "grey"}, "hair": {"yellow", "brown"}}


def frames(video: Path, tmp: Path) -> list[Path]:
    import cv2
    cap, out = cv2.VideoCapture(str(video)), []
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    for k, at in enumerate((0.2, 0.5, 0.85)):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(n * at))
        ok, bgr = cap.read()
        if ok:
            p = tmp / f"{video.stem}_{k}.png"
            cv2.imwrite(str(p), bgr)
            out.append(p)
    return out


def judged(said: str) -> dict:
    got = unwrap(said) if said else {}
    got = got if isinstance(got, dict) else {}
    seen = {k: str(got.get(k, "")).lower() for k in WANT}
    off = [k for k, ok in WANT.items() if seen[k] in COLOURS and seen[k] not in ok]
    return {"seen": seen, "girl_seen": got.get("girl_seen"), "contradicts": off}


def main(takes: Path) -> None:
    out = {}
    with tempfile.TemporaryDirectory() as tmp:
        for i in (5, 6, 7):
            rows = [judged(look_back.vlm_reader(f, ASK)) for f in frames(takes / f"T{i:02d}.mp4", Path(tmp))]
            out[f"T{i:02d}"] = rows
            print(f"T{i:02d}", json.dumps(rows), flush=True)
    (Path(__file__).parent / "girl_identity.json").write_text(json.dumps(out, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else TAKES)
