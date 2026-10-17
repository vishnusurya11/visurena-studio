"""The face refine's gate measures (CPU): one refined crop against the take it came
from.  The walls and the decision live in studio/face_refine.py; this module only
measures.  `detect` / `embed` are facenet's (studio/measure/faces.embedder) in a run
and fakes in a test.

- seam: the level difference in the feather band, at window scale, where the paste
  meets the take;
- flicker: the face region's frame-to-frame change, the take's own against the
  pasted result (F2 0.81-0.95 of the take's, F3's boiling noise 1.15-1.32);
- faces: counted on the 768 crops, unrefined against refined (a clone or a lost
  face changes it);
- identity: facenet cosine to the person's sheet, read where the 768 crop makes the
  face big enough to read.
"""
from __future__ import annotations

import numpy as np

from studio import face_paste, face_refine

SEAM_EVERY = 8


def windows_of(take: list[np.ndarray], wins: list, span: tuple[int, int]) -> list[np.ndarray]:
    """The take cut to the track's window, frame by frame over its life."""
    out = []
    for t in range(span[0], min(span[1], len(take) - 1) + 1):
        x, y, s = wins[t]
        out.append(take[t][y:y + s, x:x + s])
    return out


def shrunk(crop: list[np.ndarray], start: int, span: tuple[int, int], side: int) -> list[np.ndarray]:
    """The refined crop's frames over the life, shrunk to the window's side."""
    import cv2
    ks = [t - start for t in range(span[0], span[1] + 1) if 0 <= t - start < len(crop)]
    return [cv2.resize(np.ascontiguousarray(crop[k]), (side, side), interpolation=cv2.INTER_AREA) for k in ks]


def seam_and_flicker(src: list[np.ndarray], ref: list[np.ndarray]) -> tuple[float, float, float]:
    """(seam, the take's flicker, the pasted flicker), at window scale."""
    n, side = min(len(src), len(ref)), src[0].shape[0]
    f = max(2, round(side * face_paste.FEATHER_SHARE))
    mask = face_paste.feather(side, f)
    pasted = [(r * mask + s * (1 - mask)).astype(np.uint8) for s, r in zip(src[:n], ref[:n])]
    seam = float(np.mean([face_paste.ring_diff(s, r, f) for s, r in zip(src[:n:SEAM_EVERY], ref[:n:SEAM_EVERY])]))
    return seam, face_paste.region_flicker(src[:n]), face_paste.region_flicker(pasted)


def read_faces(crops: list[np.ndarray], sheet_vec, detect, embed) -> tuple[int, float | None]:
    """(faces counted over the crops, mean cosine of each crop's largest face to the sheet)."""
    from studio.measure import faces
    count, cos = 0, []
    for rgb in crops:
        found = detect(rgb)
        count += len(found)
        if found and sheet_vec is not None:
            cos.append(faces.cosine(embed(rgb, faces.largest(found)["box"]), sheet_vec))
    return count, (float(np.mean(cos)) if cos else None)


def faces_and_identity(src768, ref768, sheet_vec, detect, embed):
    """(faces unrefined, faces refined, identity unrefined, identity refined)."""
    cs, ids = read_faces(src768, sheet_vec, detect, embed)
    cr, idr = read_faces(ref768, sheet_vec, detect, embed)
    return cs, cr, ids, idr


def measure(src_w, ref_w, src768, ref768, sheet_vec, detect, embed) -> face_refine.Measures:
    """Every measure the decision reads, for one person's refined crop."""
    seam, f_src, f_ref = seam_and_flicker(src_w, ref_w)
    cs, cr, ids, idr = faces_and_identity(src768, ref768, sheet_vec, detect, embed)
    return face_refine.Measures(id_src=ids, id_ref=idr, seam=round(seam, 2), flick_src=round(f_src, 3),
                                flick_ref=round(f_ref, 3), faces_src=cs, faces_ref=cr)
