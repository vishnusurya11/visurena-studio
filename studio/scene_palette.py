"""Within-scene weather and palette continuity, CPU, advisory (owner item 8, 2026-10-15).

Jekyll ep01 iter4: pavement_day's T11 was grey overcast and T12 a sunny blue sky with teal
shutters, in one scene; sunday_street went blue and teal against the plan's soot, bone, amber and
oxblood. No gate compared takes of one scene with each other. This reads one frame per take: the
sky band's blueness (blue minus red over the top third) and the frame's saturation, and names a take
that sits far from its scene's median. Thresholds are first guesses, uncalibrated: ADVISORY."""
from __future__ import annotations

import numpy as np

SKY_BLUE_GAP = 15.0
"""Percent of the top third that is open blue sky (blue over red by 40 and bright), against the
scene median: a building in the band dilutes a mean, a share of sky pixels it does not."""
SATURATION_GAP = 0.12


def stats(rgb) -> dict:
    """{sky_blue, saturation} of one frame (H x W x 3, uint8)."""
    a = np.asarray(rgb, dtype=float)
    sky = a[: max(1, a.shape[0] // 3)]
    hi, lo = a.max(axis=2), a.min(axis=2)
    sat = float(np.mean((hi - lo) / np.maximum(hi, 1.0)))
    blue = (sky[..., 2] - sky[..., 0] > 40) & (sky[..., 2] > 120)
    return {"sky_blue": float(100.0 * np.mean(blue)), "saturation": sat}


def why_off(s: dict, median: dict) -> str:
    """'' when a take sits with its scene, else the reason."""
    if abs(s["sky_blue"] - median["sky_blue"]) > SKY_BLUE_GAP:
        return f"sky blue {s['sky_blue']:.0f} against the scene's {median['sky_blue']:.0f}"
    if abs(s["saturation"] - median["saturation"]) > SATURATION_GAP:
        return f"saturation {s['saturation']:.2f} against the scene's {median['saturation']:.2f}"
    return ""


def outliers(by_take: dict[int, dict], scene_of: dict[int, str]) -> list[tuple[int, str]]:
    """(take, reason) for every take far from its scene's median; a scene of one has none."""
    out = []
    for scene in sorted(set(scene_of.values())):
        takes = [t for t in sorted(by_take) if scene_of.get(t) == scene]
        if len(takes) < 2:
            continue
        median = {k: float(np.median([by_take[t][k] for t in takes])) for k in ("sky_blue", "saturation")}
        out += [(t, f"{scene}: {why}") for t in takes if (why := why_off(by_take[t], median))]
    return out
