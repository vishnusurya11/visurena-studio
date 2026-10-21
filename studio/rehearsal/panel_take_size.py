"""Panel face size predicts take face size (2026-10-21_ep02_proof DESIGN 4.4, package P6).

x: the panel's tallest present face at the 768 render, read through panel_dq.tiny_face_record (the
A28 column, the real code), from storyboard/panel_dq.json.  y: the take's smallest tracked size of
its tallest face (the warp gate's track with the largest median, its `min_px`), from
takes/r2v/T<nn>.dq.json.  A pair needs a panel face that is a cast face and a tracked take face.
Every pair of the episode is used, not only the refined rows.  A take is paired with the panel of its
first shot.

The pairing is tallest-to-tallest, never per matched cast face: panel_dq keeps one face height per
panel (its tallest) and the warp tracks carry no identity, so no record says which take face is which
panel face.  On a single-face pair (one panel face, one take track) the two ARE the same person; those
pairs are fitted apart (`single_face`) so a line that holds only because of the pairing shows.

Pre-registered kill: R^2 < 0.8 of the least-squares line, or any STATIC (the dq's camera
`still_ok`) SINGLE-face (one panel face, one take track) take whose size the line misses by more
than 20 %.  With fewer than three pairs nothing can pass.  A pass makes a plan's panels a
predictor of its face tiers before any take renders; it is not an eye measure, and the
instrument gate (4.2) does not govern it."""
from __future__ import annotations

import json
from pathlib import Path

R2_MIN = 0.8
STATIC_ERROR_MAX = 0.20
MIN_PAIRS = 3
PAIRING = ("tallest panel face (panel_dq face_h) to tallest take track (warp median); no per-face identity is "
           "recorded on either side, so only a single-face pair is a matched cast face; a take reads its first shot's panel")


def tallest_track(dq: dict | None) -> dict | None:
    """The warp gate's track with the largest median face, or None when it tracked none."""
    tracks = (((dq or {}).get("measures") or {}).get("warp") or {}).get("tracks") or []
    return max(tracks, key=lambda t: float(t.get("median_px") or 0.0)) if tracks else None


def pair_of(index: int, panel: dict | None, dq: dict | None) -> dict | None:
    """One (panel, take) pair, or None when either side has no face to compare."""
    from studio import panel_dq
    track = tallest_track(dq)
    if not panel or not panel.get("cast_faces") or track is None or track.get("min_px") is None:
        return None
    px = panel_dq.tiny_face_record(panel.get("face_h"))["face_px_768"]
    if px is None:
        return None
    tracks = len(dq["measures"]["warp"]["tracks"])
    return {"take": index, "panel_px": px, "take_px": float(track["min_px"]),
            "static": bool((dq.get("camera") or {}).get("still_ok")), "single": panel.get("faces") == 1 and tracks == 1}


def fit(pairs: list[dict]) -> tuple[float, float, float]:
    """(slope, intercept, R^2) of take_px on panel_px by least squares."""
    xs, ys = [float(p["panel_px"]) for p in pairs], [float(p["take_px"]) for p in pairs]
    n, mx, my = len(xs), sum(xs) / len(xs), sum(ys) / len(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx if sxx else 0.0
    intercept = my - slope * mx
    ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in zip(xs, ys))
    ss_tot = sum((y - my) ** 2 for y in ys)
    return slope, intercept, (1.0 - ss_res / ss_tot) if ss_tot else (1.0 if n else 0.0)


def error(pair: dict, slope: float, intercept: float) -> float:
    """How far the line misses the take's size, as a share of it."""
    return abs(slope * float(pair["panel_px"]) + intercept - float(pair["take_px"])) / float(pair["take_px"])


def single_fit(pairs: list[dict]) -> dict:
    """The line over the single-face pairs alone (where tallest-to-tallest is the matched face)."""
    single = [p for p in pairs if p["single"]]
    if len(single) < MIN_PAIRS:
        return {"n": len(single), "r2": None}
    slope, intercept, r2 = fit(single)
    return {"n": len(single), "slope": round(slope, 4), "intercept": round(intercept, 2), "r2": round(r2, 4)}


def tier_edges() -> list[float]:
    """The face tiers' edges: tiny under tiny_face.TINY_PX, mid under face_refine.SMALL_FACE_PX."""
    from scripts.episode.tiny_face import TINY_PX
    from studio.face_refine import SMALL_FACE_PX
    return [float(TINY_PX), float(SMALL_FACE_PX)]


def tier(px: float, edges: list[float]) -> str:
    return "tiny" if px < edges[0] else "mid" if px < edges[1] else "large"


def tier_agreement(pairs: list[dict]) -> dict:
    """On how many pairs the panel's face tier is the take's (AUDIT A6: the number a failed line hides)."""
    edges = tier_edges()
    moved = [f"T{p['take']:02d} {tier(p['panel_px'], edges)}->{tier(p['take_px'], edges)}" for p in pairs
             if tier(p["panel_px"], edges) != tier(p["take_px"], edges)]
    return {"same": len(pairs) - len(moved), "n": len(pairs), "moved": moved, "edges_px": edges}


def verdict(pairs: list[dict]) -> dict:
    """The pre-registered verdict (the line, its R^2, every static single-face miss, the kill lines), with
    its pairing said, the single-face pairs fitted apart and the tier agreement."""
    return {**pre_registered(pairs), "pairing": PAIRING, "single_face": single_fit(pairs), "tiers": tier_agreement(pairs)}


def pre_registered(pairs: list[dict]) -> dict:
    """DESIGN 4.4's kill over every pair: R^2 under R2_MIN, or a static single-face miss over 20 %."""
    if len(pairs) < MIN_PAIRS:
        return {"n": len(pairs), "passed": False, "kill": [f"{len(pairs)} pairs: fewer than {MIN_PAIRS}"]}
    slope, intercept, r2 = fit(pairs)
    kill = [f"R^2 {r2:.3f} < {R2_MIN}"] if r2 < R2_MIN else []
    misses = {p["take"]: round(error(p, slope, intercept), 3) for p in pairs if p["static"] and p["single"]}
    kill += [f"T{t:02d} static single-face error {e:.0%} > {STATIC_ERROR_MAX:.0%}"
             for t, e in sorted(misses.items()) if e > STATIC_ERROR_MAX]
    return {"n": len(pairs), "slope": round(slope, 4), "intercept": round(intercept, 2), "r2": round(r2, 4),
            "static_single_errors": misses, "passed": not kill, "kill": kill}


def read_json(path: Path, default):
    return json.loads(Path(path).read_text(encoding="utf-8")) if Path(path).is_file() else default


def episode_pairs(home: Path) -> list[dict]:
    """Every (panel, take) pair of one episode, from its named records (read only)."""
    room = Path(home) / "takes" / "r2v"
    panels = {int(p["shot"]): p for p in read_json(Path(home) / "storyboard" / "panel_dq.json", []) if "shot" in p}
    out = []
    for card in read_json(room / "prompts.json", []):
        i, shots = int(card["index"]), card.get("shots") or [card["index"]]
        found = pair_of(i, panels.get(int(shots[0])), read_json(room / f"T{i:02d}.dq.json", None))
        if found is not None:
            out.append(found)
    return out
