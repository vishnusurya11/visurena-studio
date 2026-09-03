"""Does this face belong to this character, and are these two men different?

Built because we had no way to ask.  The first run of it found Watson and
Holmes at cosine 0.420 in the shipped `a-study-in-scarlet` sheets -- above
insightface's own same-person line, meaning our two leads are literally the
same man to a recogniser, across a trailer nobody flagged.

Licence, and it is a real constraint: insightface's model zoo (`w600k_r50`,
`det_10g`) is released for non-commercial research only -- the MIT licence
covers the code, not the weights.  This feeds a monetised channel, so anything
that ships uses YuNet (MIT) for detection and SFace (Apache-2.0) for identity;
buffalo_l stays for internal calibration.  `DEFAULT_MODELS` names the pair
that is safe to publish behind.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

ARCFACE_TEMPLATE = np.array([
    [38.2946, 51.6963],   # right eye
    [73.5318, 51.5014],   # left eye
    [56.0252, 71.7366],   # nose
    [41.5493, 92.3655],   # right mouth corner
    [70.7299, 92.2041],   # left mouth corner
], dtype=np.float64)
"""insightface's canonical five points for a 112x112 crop, in its own order."""

CROP = 112
"""What the recogniser was trained on.  Feeding it anything else is guessing."""

FACE_FLOOR = 64
"""Below this the score is untrustworthy; MEASURED self-similarity by size:
>=112px 0.994, 64px 0.987, 48px 0.967, 32px 0.905, 24px 0.797."""

UNVERIFIABLE_BELOW = 48
"""Below this, refuse to answer.  A small face reads wrong in BOTH directions
-- the same sheet produced a spurious 0.98 and a spurious 0.07."""

@dataclass(frozen=True)
class Recogniser:
    """A backbone and the three things about it that are NOT interchangeable.

    Found the hard way.  Scoring SFace crops with ArcFace's `(x-127.5)/127.5`
    normalisation returned 0.887-0.987 for every pair in the cast -- a clean,
    confident, entirely degenerate result that would have failed all fifteen
    pairs and sent us regenerating sheets that were fine.  The same crops
    score 0.097-0.540 raw.  Normalisation belongs to the weights, and so does
    the threshold: SFace calls 0.363 the same person where ArcFace says 0.40.
    """

    name: str
    zero_centred: bool
    same_person_at: float
    unique_below: float
    licence: str
    ships: bool


SFACE = Recogniser("sface", False, 0.363, 0.27, "Apache-2.0", True)
"""Apache-2.0, 128-d, and the one that may ship.  0.363 is OpenCV's published
same-person cosine; 0.27 is ArcFace's unique/same RATIO carried across, which
is DERIVED, not measured -- treat a score just under it as review, not proof."""

ARCFACE = Recogniser("w600k_r50", True, 0.40, 0.30, "non-commercial", False)
"""512-d and stronger, but insightface's zoo is research-only.  Internal
calibration only; never behind anything that ships."""

DEFAULT_MODELS = ("yunet.onnx", "sface.onnx")
"""MIT + Apache-2.0.  The pair that may ship."""


def normalise_input(crop: np.ndarray, using: Recogniser) -> np.ndarray:
    """Put a 112x112 crop into the range its backbone was trained on."""
    values = crop.astype(np.float32)
    return (values - 127.5) / 127.5 if using.zero_centred else values


def similarity_transform(source: np.ndarray, target: np.ndarray) -> np.ndarray:
    """Umeyama: the rotation, scale and shift taking source onto target.

    Hand-rolled because `skimage` is a heavy dependency for fifteen lines, and
    because the one line that matters is easy to leave out: without the
    `det < 0` guard the fit is free to MIRROR the face and will happily do so
    on a near-symmetric set of five points.
    """
    source, target = np.asarray(source, float), np.asarray(target, float)
    src_mean, dst_mean = source.mean(axis=0), target.mean(axis=0)
    src_centred, dst_centred = source - src_mean, target - dst_mean
    covariance = dst_centred.T @ src_centred / len(source)
    u, singular, vt = np.linalg.svd(covariance)
    correction = np.eye(2)
    if np.linalg.det(u) * np.linalg.det(vt) < 0:
        correction[1, 1] = -1.0
    rotation = u @ correction @ vt
    variance = src_centred.var(axis=0).sum()
    scale = 1.0 if variance == 0 else (singular * np.diag(correction)).sum() / variance
    matrix = np.eye(3)
    matrix[:2, :2] = rotation * scale
    matrix[:2, 2] = dst_mean - (rotation * scale) @ src_mean
    return matrix


def align(image: np.ndarray, landmarks: np.ndarray) -> np.ndarray:
    """The 112x112 crop the recogniser expects, from five points.

    Channel order is left alone.  insightface reads BGR through cv2 and then
    sets `swapRB=True`, so the NETWORK sees RGB -- which is what PIL already
    hands you.  Swapping "to match insightface" costs a measured 0.931 cosine
    on the same face, which is enough to move a pair across a threshold
    without anything looking wrong.
    """
    from PIL import Image

    matrix = similarity_transform(np.asarray(landmarks, float), ARCFACE_TEMPLATE)
    inverse = np.linalg.inv(matrix)  # PIL maps DESTINATION -> source
    warped = Image.fromarray(image).transform(
        (CROP, CROP), Image.AFFINE, inverse[:2].ravel(), resample=Image.BILINEAR)
    return np.asarray(warped)


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity, normalising both sides so magnitude cannot leak in."""
    a, b = np.asarray(a, float).ravel(), np.asarray(b, float).ravel()
    denominator = np.linalg.norm(a) * np.linalg.norm(b)
    return 0.0 if denominator == 0 else float(a @ b / denominator)


def verdict(similarity: float, face_px: int,
            using: "Recogniser | None" = None) -> str:
    """pass / review / fail / unverifiable, size gating the score.

    Size is checked FIRST and on purpose.  A face too small to read produces a
    number, and the number is the problem: our shipped sheets are 57-66px wide
    and the old pipeline would have scored every one of them.
    """
    if face_px < UNVERIFIABLE_BELOW:
        return "unverifiable"
    backbone = using or ARCFACE
    if similarity >= backbone.same_person_at:
        return "fail"
    if similarity >= backbone.unique_below or face_px < FACE_FLOOR:
        return "review"
    return "pass"


def detect(session, image: np.ndarray) -> list[tuple[np.ndarray, np.ndarray]]:
    """YuNet: (bbox, five landmarks) per face, largest first.

    YuNet is chosen over RetinaFace for one reason beyond the licence -- its
    five landmarks come out in ArcFace's exact order, so no reordering step
    exists to get wrong.  (AutoCropFaces, the vendored RetinaFace we already
    have, throws the landmarks away entirely and returns only the box, which
    is why it can measure a face but never align one.)
    """
    height, width = image.shape[:2]
    session.set_input_size([width, height])  # type: ignore[attr-defined]
    found, faces = session.detect(image[..., ::-1])  # cv2 API wants BGR
    if faces is None:
        return []
    ordered = sorted(faces, key=lambda f: -(f[2] * f[3]))
    return [(f[:4].astype(float), f[4:14].reshape(5, 2).astype(float))
            for f in ordered]


def embed(session, crop: np.ndarray, using: "Recogniser | None" = None) -> np.ndarray:
    """A unit-length identity vector for one aligned 112x112 crop."""
    blob = normalise_input(crop, using or ARCFACE).transpose(2, 0, 1)[None]
    name = session.get_inputs()[0].name
    vector = np.asarray(session.run(None, {name: blob})[0]).ravel()
    norm = np.linalg.norm(vector)
    return vector if norm == 0 else vector / norm
