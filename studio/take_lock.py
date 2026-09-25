"""A person held at one screen position while the set slides past them.

ep09 T02 (owner, 2026-09-23: "he walked with the fence ... ai slop, dq missed
it"): the camera trucks along a fence and H3 keeps the leaning neighbour where
the cell put him, sliding the fence through him. Every take_dq row judged the
frame; none asked whether what is fixed in the world stayed fixed.

lock = 1 - (the face's horizontal travel) / (the scenery's beside the body).
Near 1: the person rode with the camera. Near 0 or below: the person held his
place in the world. MEASURED (take-gate audit): T02 1.01 over 1055 px of
fence, T10 1.05 over 632 px; eligible passes top out at -0.42 (ep09 T20, ep08
T07, T10). Two fires against three passes -- a thin margin, and said so.

Whether a held person is a FAULT is the plan's call: a walker the camera
tracks WITH is locked and correct (ep08 T05 reads 1.06).
"""
from __future__ import annotations

import re

import numpy as np

S = 256
WALL, TRAVEL = 0.75, 100.0
"""Hard at lock >= WALL when the set moved at least TRAVEL px (at 768)."""
FITTED_ON = ("take-gate audit 2026-09-23, one book: 2 eligible fires (1.01 over 1055 px, 1.05 over 632 px) "
             "against 3 eligible passes topping out at -0.42; margin one take wide")
PASS_WALL = 0.5
"""Pass-through: at least this share of the body band rode with the camera fit
while the face held (lock >= WALL) over TRAVEL px.  Synthetic only so far: the
band reads ~1.0 with the set drawn through the man and ~0 when he is on it."""
BAND_W, BAND_H = 1.6, 3.0
"""The body band under the face box: BAND_W face heights either side of the
face centre, BAND_H face heights down from the chin (the torso the rails cross)."""

MOVES = re.compile(r"\b(?:truck|tracks? sideways|pans?)\b", re.I)
WITH = re.compile(r"\bwith (?:him|her|them)\b|\bkeeping (?:him|her|them)\b|\bfollows?\b"
                  r"|\bat (?:his|her|their) own pace\b|\bmoves? off\b", re.I)
WALKS = re.compile(r"\b(?:walks|walking|runs|running|strides|striding|crawls|crawling|rides|riding|"
                   r"moves? off)\b", re.I)
"""Read in the SUBJECT clauses only: the camera head's 'travelling one short
stride' is the camera's travel, and reading it as a walker excused ep09 T02."""


def eligible(motion: str) -> bool:
    """A sideways move over a subject the plan keeps in place."""
    head, _, rest = motion.partition(";")
    return bool(MOVES.search(head)) and not WITH.search(head) and not WALKS.search(rest)


def face_track(frames: list[np.ndarray], every: int = 6) -> dict[int, dict]:
    from studio import face_end
    out = {}
    for i in range(0, len(frames), every):
        found = [f for f in (face_end.faces(frames[i]) or []) if f["score"] >= 0.8 and f["h"] >= 0.05]
        if found:
            out[i] = found[0]
    return out


def band_travel(band: np.ndarray, body: np.ndarray, left: np.ndarray) -> float:
    """One band's horizontal step either side of the body, read only when both
    sides move the same way (a zoom moves them apart)."""
    l_px, r_px = band[:, (~body) & left], band[:, (~body) & ~left]
    l = float(np.median(l_px)) if l_px.size > 200 else None
    r = float(np.median(r_px)) if r_px.size > 200 else None
    if l is None or r is None:
        return l if r is None and l is not None else (r or 0.0)
    return float(np.sign(l) * min(abs(l), abs(r))) if np.sign(l) == np.sign(r) else 0.0


def side_travel(flow: np.ndarray, cx: float, cy: float, h: float) -> tuple[float, float]:
    """(below the face, above the face): the fence T02 slides past is BELOW the
    neighbour's face and the heath above it barely moves, so the two bands are
    read apart and the one that travels further stands for the set."""
    xs = np.arange(S)
    body, left = np.abs(xs - cx) <= 1.6 * h, xs < cx
    low = flow[int(min(cy + h, S - 8)):S]
    high = flow[0:int(max(cy - h, 8))]
    return band_travel(low, body, left), band_travel(high, body, left)


def lock(frames: list[np.ndarray], track=face_track) -> dict | None:
    """{'lock', 'scen', 'subj'} in px at 768, or None when no face holds the take."""
    import cv2
    faces = track(frames)
    if len(faces) < 0.5 * len(range(0, len(frames), 6)):
        return None
    grey = [cv2.resize(cv2.cvtColor(f, cv2.COLOR_RGB2GRAY), (S, S)) for f in frames]
    subj, low, high = [], [], []
    for i in range(1, len(grey)):
        f = faces[max((j for j in faces if j <= i), default=min(faces))]
        cx, cy, h = f["cx"] * S, f["cy"] * S, f["h"] * S
        flow = cv2.calcOpticalFlowFarneback(grey[i - 1], grey[i], None, 0.5, 4, 21, 3, 5, 1.2, 0)[..., 0]
        box = flow[int(max(cy - h / 2, 0)):int(min(cy + h / 2, S)), int(max(cx - h / 2, 0)):int(min(cx + h / 2, S))]
        subj.append(float(np.median(box)))
        below, above = side_travel(flow, cx, cy, h)
        low.append(below); high.append(above)
    k = 768 / S
    s, lo, hi = float(np.sum(subj)) * k, float(np.sum(low)) * k, float(np.sum(high)) * k
    b = lo if abs(lo) >= abs(hi) else hi
    return {"lock": round(1 - s / b, 2) if abs(b) > 1 else None, "scen": round(b, 1), "subj": round(s, 1),
            "fitted_on": FITTED_ON}


# ---- the dense read: the set drawn THROUGH the held man --------------------------

def face_region(cx: float, cy: float, h: float, shape: tuple[int, int] = (S, S)) -> np.ndarray:
    """The face box as a boolean mask."""
    ys, xs = np.mgrid[0:shape[0], 0:shape[1]]
    return (np.abs(ys - cy) <= h / 2) & (np.abs(xs - cx) <= h / 2)


def body_band(cx: float, cy: float, h: float, shape: tuple[int, int] = (S, S)) -> np.ndarray:
    """The torso under the face: where a set drawn through the man shows."""
    ys, xs = np.mgrid[0:shape[0], 0:shape[1]]
    return (ys > cy + h / 2) & (ys <= cy + h / 2 + BAND_H * h) & (np.abs(xs - cx) <= BAND_W * h)


def grey_frames(frames: list[np.ndarray]) -> list[np.ndarray]:
    import cv2
    return [cv2.resize(cv2.cvtColor(f, cv2.COLOR_RGB2GRAY), (S, S)) for f in frames]


def step_pass(field: np.ndarray, face: dict, person: np.ndarray | None) -> tuple[float, float, float | None] | None:
    """One step: (face flow, camera tx, share of the band on the camera fit)."""
    from studio.measure import flow as fl
    cx, cy, h = face["cx"] * S, face["cy"] * S, face["h"] * S
    box, band = face_region(cx, cy, h), body_band(cx, cy, h)
    mask = (person | box) if person is not None else (band | box)
    cam = fl.camera(field, mask=mask)
    if not cam["measured"]:
        return None
    region = ((person & ~box) if person is not None else band)
    share = fl.agreement(field, cam["sol"], region) if abs(cam["tx"]) >= 0.5 else None
    return float(np.median(field[..., 0][box])), cam["tx"], share


def pass_through(frames: list[np.ndarray], track=face_track, mask=None) -> dict | None:
    """{'pass_through', 'lock', 'scen', 'subj', 'steps', 'fitted_on'} or None
    with no face.  `mask(i, shape)` is a person mask per frame (v2); without
    one the body band under the face stands for the person."""
    from studio.measure import flow as fl
    faces = track(frames)
    if len(faces) < 0.5 * len(range(0, len(frames), 6)):
        return None
    grey = grey_frames(frames)
    subj, cam, shares = [], [], []
    for i in range(1, len(grey)):
        f = faces[max((j for j in faces if j <= i), default=min(faces))]
        got = step_pass(fl.dis(grey[i - 1], grey[i]), f, mask(i, (S, S)) if mask else None)
        if got:
            subj.append(got[0]); cam.append(got[1]); shares += [got[2]] if got[2] is not None else []
    k = 768 / S
    s, c = float(np.sum(subj)) * k, float(np.sum(cam)) * k
    return {"pass_through": round(float(np.mean(shares)), 2) if shares else None,
            "lock": round(1 - s / c, 2) if abs(c) > 1 else None, "scen": round(c, 1), "subj": round(s, 1),
            "steps": len(shares), "fitted_on": FITTED_ON}


def pass_through_row(got: dict | None, motion: str):
    """HARD when the plan keeps the subject in place (`eligible`, the held
    row's own rule), the face held (lock >= WALL), the set travelled TRAVEL
    px and PASS_WALL of the body band rode with the camera fit."""
    from studio.take_verdict import Gate
    if not got or got.get("pass_through") is None or got.get("lock") is None:
        return Gate("pass-through", None, True, True, "not measured")
    if not eligible(motion):
        return Gate("pass-through", None, True, True, "n/a by the plan")
    share = got["pass_through"]
    fault = share >= PASS_WALL and got["lock"] >= WALL and abs(got["scen"]) >= TRAVEL
    note = f"{share:.2f} of the body rode with the camera over {abs(got['scen']):.0f}px"
    note += " HARD: the set slides through the person" if fault else ""
    return Gate("pass-through", share, not fault, True, note, 40.0 if fault else 0.0)


def row(got: dict | None, motion: str):
    from studio.take_verdict import Gate
    if not got or got.get("lock") is None or not eligible(motion):
        return Gate("held", None, True, True, "not measured" if not got else "n/a by the plan")
    fault = got["lock"] >= WALL and abs(got["scen"]) >= TRAVEL
    note = f"{got['lock']:.2f} over {abs(got['scen']):.0f}px" + (" HARD: the set slides through the person" if fault else "")
    return Gate("held", got["lock"], not fault, True, note, 40.0 if fault else 0.0)


def frames(video, seconds: float | None) -> list[np.ndarray]:
    """RGB frames at the take's native size, the placed seconds only."""
    import cv2
    cap, out = cv2.VideoCapture(str(video)), []
    limit = int(round(seconds * cap.get(cv2.CAP_PROP_FPS))) if seconds else None
    while limit is None or len(out) < limit:
        ok, f = cap.read()
        if not ok:
            break
        out.append(cv2.cvtColor(f, cv2.COLOR_BGR2RGB))
    return out
