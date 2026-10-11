#!/usr/bin/env python
"""Phase-0 bench rulers (continuity retro 2026-10-10, S §2 rows 85-88, P2 §3).

Per take, on N frames sampled through it (grey, 0-255):
  texture    mid-band DoG energy (sigma 1 vs 4), outside face boxes      higher = better
  flat       share of 16x16 blocks with luma std < FLAT_STD (mid-luma)   lower  = better
  face_flat  the same at 8x8 inside readable face boxes (size-normalised) lower  = better
  banding    comb index of the luma histogram of smooth dark pixels      lower  = better
  lap        Laplacian variance -- reported only (fails calibration, E §2)
  tail       texture(last) / texture(first)                              higher = better
A ruler VOTES on the bench only if its AUC on content-matched owner-good vs owner-bad
takes is >= 0.75 in its declared direction (`calibrate`).

    uv run --no-sync python scripts/bench/rulers.py measure <out.json> <video...>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

FLAT_STD = 2.5
BLOCK = 16
SHARES = (0.06, 0.18, 0.30, 0.42, 0.54, 0.66, 0.78, 0.94)
DIRECTION = {"texture": 1, "flat": -1, "face_flat": -1, "banding": -1, "lap": 1, "tail": 1}


def _blur(img: np.ndarray, sigma: float) -> np.ndarray:
    import cv2
    return cv2.GaussianBlur(img.astype(np.float32), (0, 0), sigma)


def texture(grey: np.ndarray, exclude: np.ndarray | None = None) -> float:
    """Mean |DoG(1,4)| over mid-luma pixels not excluded."""
    band = np.abs(_blur(grey, 1.0) - _blur(grey, 4.0))
    keep = (grey > 16) & (grey < 240)
    if exclude is not None and exclude.any():
        import cv2  # the DoG reaches ~2 sigma past a box edge: exclude that rim too
        keep &= ~cv2.dilate(exclude.astype(np.uint8), np.ones((17, 17), np.uint8)).astype(bool)
    return float(band[keep].mean()) if keep.any() else 0.0


def block_stds(grey: np.ndarray, block: int) -> tuple[np.ndarray, np.ndarray]:
    h, w = (grey.shape[0] // block) * block, (grey.shape[1] // block) * block
    b = grey[:h, :w].reshape(h // block, block, w // block, block).swapaxes(1, 2)
    return b.std(axis=(2, 3)), b.mean(axis=(2, 3))


def flat_share(grey: np.ndarray, block: int = BLOCK) -> float:
    """Share of mid-luma blocks whose luma std is under FLAT_STD."""
    std, mean = block_stds(grey.astype(np.float32), block)
    live = (mean > 20) & (mean < 235)
    return float((std[live] < FLAT_STD).mean()) if live.any() else 0.0


def banding(grey: np.ndarray) -> float:
    """Comb index of the dark smooth pixels' luma histogram (posterised steps)."""
    local = np.abs(grey.astype(np.float32) - _blur(grey, 2.0))
    pick = (grey < 60) & (local < 1.5)
    if pick.sum() < 500:
        return 0.0
    h = np.bincount(np.clip(np.round(grey[pick]).astype(int), 0, 63), minlength=64).astype(float)
    lo, hi = np.nonzero(h)[0][[0, -1]]
    h = h[lo:hi + 1]
    if len(h) < 3:
        return 0.0
    return float(np.abs(h[1:-1] - (h[:-2] + h[2:]) / 2).sum() / h.sum())


def laplacian(grey: np.ndarray) -> float:
    import cv2
    return float(cv2.Laplacian(grey.astype(np.float32), cv2.CV_32F).var())


def auc(good: list[float], bad: list[float]) -> float:
    """P(a good take scores above a bad one), ties half."""
    wins = sum((g > b) + 0.5 * (g == b) for g in good for b in bad)
    return round(wins / (len(good) * len(bad)), 3)


def frames(video: Path, shares=SHARES) -> list[np.ndarray]:
    import cv2
    cap = cv2.VideoCapture(str(video))
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    out = []
    for s in shares:
        cap.set(cv2.CAP_PROP_POS_FRAMES, min(n - 1, int(s * n)))
        ok, bgr = cap.read()
        if ok:
            out.append(bgr[:, :, ::-1].copy())
    cap.release()
    return out


def face_mask(rgb: np.ndarray, detect) -> tuple[np.ndarray, list[list[float]]]:
    mask = np.zeros(rgb.shape[:2], bool)
    boxes = [f["box"] for f in detect(rgb)] if detect else []
    for x1, y1, x2, y2 in boxes:
        mask[max(0, int(y1)):int(y2), max(0, int(x1)):int(x2)] = True
    return mask, boxes


def face_flat(grey: np.ndarray, boxes: list[list[float]]) -> float | None:
    """Flat 8x8 share inside faces at least 64 px tall; None when no such face."""
    shares = [flat_share(grey[int(y1):int(y2), int(x1):int(x2)], block=8)
              for x1, y1, x2, y2 in boxes if y2 - y1 >= 64 and x1 >= 0 and y1 >= 0]
    return float(np.mean(shares)) if shares else None


def measure(video: Path, detect=None) -> dict:
    """Every ruler on one take, medians over the sampled frames."""
    rows = []
    for rgb in frames(video):
        grey = rgb.astype(np.float32) @ np.array([0.299, 0.587, 0.114], np.float32)
        mask, boxes = face_mask(rgb, detect)
        rows.append({"texture": texture(grey, mask), "flat": flat_share(grey), "face_flat": face_flat(grey, boxes),
                     "banding": banding(grey), "lap": laplacian(grey), "faces": len(boxes),
                     "face_h": max([(b[3] - b[1]) / grey.shape[0] for b in boxes], default=0.0)})
    out = {k: (float(np.median([r[k] for r in rows if r[k] is not None]))
               if any(r[k] is not None for r in rows) else None) for k in rows[0]}
    out["tail"] = round(rows[-1]["texture"] / rows[0]["texture"], 3) if rows[0]["texture"] else None
    return {k: (round(v, 4) if isinstance(v, float) else v) for k, v in out.items()}


# ---- arm judgement (C1_verdict #2): the control's own seed spread, not a pixel wall ----
SAME_DRAW_DB = 3.0      # PSNR(arm, ctl) must clear PSNR(ctl seed 2, ctl) by this to be "the same draw"
ID_SIGMAS = 2.0         # per-shot identity floor, in seed-spread sigmas
ID_MEAN_FLOOR = -0.02   # mean identity delta over the dialogue shots
BAND_MEAN, BAND_SHOT = 0.005, 0.03


def same_draw(psnr_arm: float, psnr_seed: float) -> bool:
    """The arm moved the numerics, not the draw. Never a fault: below it the arm is a new draw."""
    return psnr_arm - psnr_seed >= SAME_DRAW_DB


def sigma_seed(pairs: list[tuple[float, float]]) -> float:
    """Pooled RMS of (seed 1 - seed 2) over every shot with a seed-2 control."""
    return float(np.sqrt(np.mean([(a - b) ** 2 for a, b in pairs])))


def _id_pairs(shots: dict, control: str) -> list[tuple[float, float]]:
    return [(r["id"][control], r["id"]["seed2"]) for r in shots.values()
            if r["id"].get(control) is not None and r["id"].get("seed2") is not None]


def identity_faults(arm: str, shots: dict, control: str, dialogue) -> list[str]:
    """Shots under -2 sigma_seed, plus 'mean' when the dialogue mean drops past -0.02."""
    floor = -ID_SIGMAS * sigma_seed(_id_pairs(shots, control))
    deltas = {s: r["id"][arm] - r["id"][control] for s, r in shots.items()
              if r["id"].get(arm) is not None and r["id"].get(control) is not None}
    bad = [s for s, d in deltas.items() if d < floor]
    talk = [deltas[s] for s in dialogue if s in deltas]
    return bad + (["mean"] if talk and np.mean(talk) < ID_MEAN_FLOOR else [])


def banding_faults(arm: str, shots: dict, control: str) -> list[str]:
    deltas = {s: r["banding"][arm] - r["banding"][control] for s, r in shots.items()
              if arm in r["banding"] and control in r["banding"]}
    bad = [s for s, d in deltas.items() if d > BAND_SHOT]
    return bad + (["mean"] if deltas and np.mean(list(deltas.values())) > BAND_MEAN else [])


def clone_faults(arm: str, shots: dict, production: str) -> list[str]:
    """More clone frames than the production take drew on the same shot."""
    return [s for s, r in shots.items()
            if arm in r["clones"] and r["clones"][arm] > r["clones"].get(production, 0)]


def speech_faults(arm: str, shots: dict, control: str, asked: set) -> list[str]:
    """Words in the arm's tail where the control's own tail, same seed, had none; asked mouths exempt."""
    return [s for s, r in shots.items() if s not in asked
            and r["words"].get(arm) and not r["words"].get(control)]


def judge_arm(arm: str, shots: dict, control: str, production: str, asked: set, dialogue) -> dict:
    """Rules (a)-(e). (a) only classifies the arm; it never refuses one."""
    psnr = [(r["psnr"][arm], r["psnr"]["seed2"]) for r in shots.values() if arm in r["psnr"]]
    return {"same_draw": bool(psnr) and all(same_draw(a, s) for a, s in psnr),
            "faults": {"identity": identity_faults(arm, shots, control, dialogue),
                       "banding": banding_faults(arm, shots, control),
                       "clones": clone_faults(arm, shots, production),
                       "speech": speech_faults(arm, shots, control, asked)}}


def detector():
    from studio.measure.faces import embedder
    return embedder()[0]


def main(argv: list[str]) -> None:
    if argv[0] == "measure":
        det = detector()
        res = {v: measure(Path(v), det) for v in argv[2:]}
        Path(argv[1]).write_text(json.dumps(res, indent=1), "utf-8")


if __name__ == "__main__":
    main(sys.argv[1:])
