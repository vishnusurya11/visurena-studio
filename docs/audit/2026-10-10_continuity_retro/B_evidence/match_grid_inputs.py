"""Recover which pictures a grid staged: brute-force grids.inputs_sha over a pool.

inputs_sha(text, slots) = sha256(json.dumps([text, sorted(sha256(bytes) of each slot)]))[:16]
Pool: current repo pictures (location views, sheets, fronts, props, this episode's anchors)
plus every content-addressed copy in ComfyUI/input whose stem is one of theirs (old bytes).
"""
import hashlib, itertools, json, re, sys
from pathlib import Path

BOOK = Path(r"D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\library\20260827135508_the-war-of-the-worlds")
INPUT = Path(r"D:\Projects\KingdomOfViSuReNa\alpha\ComfyUI_windows_portable\ComfyUI\input")
_cache = {}


def h(p):
    if p not in _cache:
        _cache[p] = hashlib.sha256(Path(p).read_bytes()).hexdigest()
    return _cache[p]


def pool_for(ep, setup_loc, setup):
    out = {}
    locdir = BOOK / "refs" / "locations" / setup_loc
    stems = set()
    for p in locdir.glob("*.png"):
        out[str(p)] = f"CUR {setup_loc}/{p.name}"
        stems.add(p.stem)
    for p in (BOOK / "refs" / "characters").glob("*/sheet*.png"):
        out[str(p)] = f"CUR char {p.parent.name}/{p.name}"
    for p in (BOOK / "refs" / "props").glob("*/sheet*.png"):
        out[str(p)] = f"CUR prop {p.parent.name}/{p.name}"
    anc = BOOK / "episodes" / ep / "storyboard" / "anchors"
    for p in anc.glob("*.png"):
        out[str(p)] = f"CUR room {ep}/anchors/{p.name}"
        stems.add(p.stem)
    stems |= {"sheet", "sheet_front"}
    for p in INPUT.iterdir():
        m = re.match(r"^(.*)_[0-9a-f]{8}\.png$", p.name)
        if m and m.group(1) in stems:
            out[str(p)] = f"INPUT {p.name}"
    return out


def solve(grid_json):
    g = json.loads(Path(grid_json).read_text(encoding="utf-8"))
    ep = f"ep{g['episode']:02d}"
    plan = json.loads((BOOK / "episodes" / ep / "plan.json").read_text(encoding="utf-8"))
    loc = plan["setups"].get(g["setup"], {}).get("location", "")
    text = Path(grid_json).with_suffix(".txt").read_text(encoding="utf-8")
    pool = pool_for(ep, loc, g["setup"])
    # dedupe by content
    byhash = {}
    for p, label in pool.items():
        byhash.setdefault(h(p), []).append(label)
    hashes = list(byhash)
    for k in (1, 2, 3):
        for combo in itertools.combinations(hashes, k):
            if hashlib.sha256(json.dumps([text, sorted(combo)]).encode()).hexdigest()[:16] == g["inputs"]:
                return g, [byhash[c] for c in combo]
    return g, None


if __name__ == "__main__":
    for path in sys.argv[1:]:
        g, found = solve(path)
        name = Path(path).stem
        if found is None:
            print(f"{name}\tNO MATCH (pool exhausted)")
        else:
            print(f"{name}\t" + " || ".join(" | ".join(l) for l in found))
        sys.stdout.flush()
