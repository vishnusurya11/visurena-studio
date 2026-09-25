"""Dense optical flow and the camera move it agrees on: the substrate under
the pass-through, rotation and warp-residual rows.

DIS (`cv2.DISOpticalFlow`, CPU, ~1 s a take at 256 px) gives a displacement
per pixel.  A camera move is a SIMILARITY about the frame centre c:

    d(p) = (s R(theta) - I)(p - c) + t

which is linear in (A, B, ty, tx) with A = s cos(theta) - 1, B = s sin(theta):

    dy = A ry + B rx + ty
    dx = A rx - B ry + tx

so two sampled points fix the four numbers, RANSAC keeps the largest set of
grid points that agree on one move, and least squares on the inliers is the
camera.  `take_zoom` fits the same model with theta held at zero over a
window lattice; this is the fourth parameter over a dense field.  Every
function here returns numbers; the rows that judge them live with the take
measures (`take_lock`, `take_zoom`).
"""
from __future__ import annotations

import numpy as np

GRID_STEP = 8
"""Flow is sampled every GRID_STEP px for the fit: 1024 points at 256 px."""
INLIER_PX = 1.0
MIN_INLIERS = 8
RANSAC_ITERS = 300


def dis(a: np.ndarray, b: np.ndarray):
    """The DIS flow from grey frame a to grey frame b, (h, w, 2) as (dx, dy)."""
    import cv2

    engine = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
    return engine.calc(np.ascontiguousarray(a, dtype=np.uint8), np.ascontiguousarray(b, dtype=np.uint8), None)


def grid_points(shape: tuple[int, int], step: int = GRID_STEP, mask: np.ndarray | None = None) -> np.ndarray:
    """(N, 2) sample points as (y, x), outside `mask` (True = excluded) when given."""
    h, w = shape[:2]
    ys, xs = np.mgrid[step // 2:h:step, step // 2:w:step]
    pts = np.stack([ys.ravel(), xs.ravel()], axis=1)
    if mask is not None:
        pts = pts[~mask[pts[:, 0], pts[:, 1]]]
    return pts.astype(float)


def sample(flow: np.ndarray, pts: np.ndarray) -> np.ndarray:
    """The flow at integer points, (N, 2) as (dy, dx)."""
    y, x = pts[:, 0].astype(int), pts[:, 1].astype(int)
    return np.stack([flow[y, x, 1], flow[y, x, 0]], axis=1).astype(float)


def design(pts: np.ndarray, centre: np.ndarray) -> np.ndarray:
    """The (2N, 4) matrix of the linear model in (A, B, ty, tx)."""
    rel = pts - centre
    rows = np.zeros((2 * len(pts), 4))
    rows[0::2, 0], rows[0::2, 1], rows[0::2, 2] = rel[:, 0], rel[:, 1], 1.0
    rows[1::2, 0], rows[1::2, 1], rows[1::2, 3] = rel[:, 1], -rel[:, 0], 1.0
    return rows


def fit4(pts: np.ndarray, disp: np.ndarray, centre: np.ndarray) -> np.ndarray:
    """Least squares (A, B, ty, tx) over the points."""
    sol, *_ = np.linalg.lstsq(design(pts, centre), disp.reshape(-1), rcond=None)
    return sol


def residuals4(pts: np.ndarray, disp: np.ndarray, centre: np.ndarray, sol: np.ndarray) -> np.ndarray:
    pred = (design(pts, centre) @ sol).reshape(-1, 2)
    return np.linalg.norm(disp - pred, axis=1)


def ransac4(pts: np.ndarray, disp: np.ndarray, centre: np.ndarray, tol: float = INLIER_PX,
            iters: int = RANSAC_ITERS) -> np.ndarray:
    """The largest set of points that agree on one similarity, as a boolean mask."""
    rng = np.random.default_rng(0)
    best = np.zeros(len(pts), bool)
    if len(pts) < 2:
        return best
    for _ in range(iters):
        pick = rng.choice(len(pts), 2, replace=False)
        mask = residuals4(pts, disp, centre, fit4(pts[pick], disp[pick], centre)) < tol
        if mask.sum() > best.sum():
            best = mask
    return best


def unpack(sol: np.ndarray) -> dict:
    """(A, B, ty, tx) -> scale, theta in degrees (positive = clockwise on screen), ty, tx."""
    a, b = float(sol[0]) + 1.0, float(sol[1])
    return {"scale": float(np.hypot(a, b)), "theta": float(np.degrees(np.arctan2(b, a))),
            "ty": float(sol[2]), "tx": float(sol[3])}


def similarity(pts: np.ndarray, disp: np.ndarray, centre: np.ndarray, tol: float = INLIER_PX,
               min_inliers: int = MIN_INLIERS) -> dict:
    """The one camera move the field agrees on; `measured` False under `min_inliers`."""
    inliers = ransac4(pts, disp, centre, tol)
    n = int(inliers.sum())
    if n < min_inliers:
        return {"scale": 1.0, "theta": 0.0, "ty": 0.0, "tx": 0.0, "inliers": n, "measured": False, "sol": None}
    sol = fit4(pts[inliers], disp[inliers], centre)
    return unpack(sol) | {"inliers": n, "measured": True, "sol": sol}


def camera(flow: np.ndarray, mask: np.ndarray | None = None, tol: float = INLIER_PX) -> dict:
    """The camera fit of a dense field over the grid outside the person `mask`."""
    pts = grid_points(flow.shape, mask=mask)
    centre = np.array(flow.shape[:2], float) / 2
    return similarity(pts, sample(flow, pts), centre, tol)


def agreement(flow: np.ndarray, sol: np.ndarray, region: np.ndarray, tol: float = INLIER_PX) -> float | None:
    """The share of `region` pixels whose flow is within `tol` of the fit; None on an empty region."""
    ys, xs = np.nonzero(region)
    if len(ys) == 0:
        return None
    pts = np.stack([ys, xs], axis=1).astype(float)
    centre = np.array(flow.shape[:2], float) / 2
    return float((residuals4(pts, sample(flow, pts), centre, sol) < tol).mean())


def warp_residual(a: np.ndarray, b: np.ndarray, flow: np.ndarray, mask: np.ndarray | None = None) -> float:
    """p90 of |a warped by its flow - b| outside `mask`: a morph is a high
    residual at low flow, a pan a low residual at any flow."""
    import cv2

    h, w = a.shape[:2]
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    warped = cv2.remap(np.ascontiguousarray(b, dtype=np.float32), xs + flow[..., 0], ys + flow[..., 1],
                       cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    diff = np.abs(warped - a.astype(np.float32))
    keep = diff if mask is None else diff[~mask]
    return float(np.percentile(keep, 90)) if keep.size else 0.0
