"""Timeline video — characters moving between locations as story time advances.

THE acceptance test for the analysis stage (owner, 2026-08-23): if the timeline can
drive this, the analysis is real.

DESIGN v2 (owner feedback: "locations should be big, scale doesn't need to be accurate"):
a SCHEMATIC map, not a survey map. Locations are large labeled nodes spread to fill the
frame (seeded from real geography, then relaxed apart so nothing clusters); characters
are dots that sit visibly INSIDE the node they occupy and travel along a drawn route
when they move. The active scene's location glows.

Zero cost, fully local. mp4 via bundled ffmpeg, GIF fallback.

Run: uv run python -m scripts.analysis.timeline_video
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import animation
from matplotlib.patches import Ellipse, FancyArrowPatch

# --- configuration (hardcoded; no CLI args by convention) ---
CODEX_ID = "20260822113400"
FPS = 24
SECONDS_PER_SCENE = 0.75      # even pacing; total length = scenes x this
MAX_CHARACTERS = 7
MAX_PLACES_PER_ACT = 9        # keep the map readable: the act's busiest places
OUT_STEM = "timeline_video"

BG = "#0b0f16"
NODE_FACE = "#1b2534"
NODE_EDGE = "#33465e"
NODE_ACTIVE = "#2c4a6e"
NODE_ACTIVE_EDGE = "#7fb2e5"

PALETTE = ["#ff4d6d", "#4cc9f0", "#80ed99", "#ffd166", "#c77dff",
           "#ff9f1c", "#00d4d8"]


def load_timeline(book_dir: Path) -> dict:
    return json.loads((book_dir / "analysis" / "timeline.json").read_text(encoding="utf-8"))


def pick_characters(timeline: dict) -> list[str]:
    scored = sorted(timeline["worldlines"].items(),
                    key=lambda kv: (-len({s["location_id"] for s in kv[1]}), -len(kv[1])))
    return [cid for cid, _ in scored[:MAX_CHARACTERS]]


def act_cast(timeline: dict, act: dict, candidates: list[str]) -> list[str]:
    """Only characters actually observed in this act appear in it."""
    lo, hi = act["chapters"]
    return [cid for cid in candidates
            if any(s["kind"] == "observed" and s["track"] == act["track"]
                   and lo <= s.get("chapter", -1) <= hi
                   for s in timeline["worldlines"].get(cid, []))]


def build_acts(timeline: dict) -> list[dict]:
    scenes = sorted(timeline["scenes"], key=lambda s: (s["chapter"], s["scene"]))
    acts, current = [], None
    for scene in scenes:
        if current is None or scene["track"] != current["track"]:
            current = {"track": scene["track"], "chapters": [], "t_min": scene["t"],
                       "t_max": scene["t"]}
            acts.append(current)
        current["chapters"].append(scene["chapter"])
        current["t_min"] = min(current["t_min"], scene["t"])
        current["t_max"] = max(current["t_max"], scene["t"])
    for act in acts:
        act["chapters"] = (min(act["chapters"]), max(act["chapters"]))
    return acts


def act_places(timeline: dict, act: dict) -> list[str]:
    """The act's busiest locations — a readable map, not every pin."""
    lo, hi = act["chapters"]
    counts: dict[str, int] = {}
    for scene in timeline["scenes"]:
        if (scene["track"] == act["track"] and lo <= scene["chapter"] <= hi
                and scene["location_id"]):
            counts[scene["location_id"]] = counts.get(scene["location_id"], 0) + 1
    return [lid for lid, _ in sorted(counts.items(), key=lambda kv: -kv[1])
            [:MAX_PLACES_PER_ACT]]


def layout(place_ids: list[str], locations: dict) -> dict[str, tuple[float, float]]:
    """SCHEMATIC layout: seed from real geography, then relax nodes apart so they fill
    the frame. Accurate distance is explicitly NOT a goal (owner) — legibility is."""
    if not place_ids:
        return {}
    lats = [locations[i]["lat"] for i in place_ids]
    lons = [locations[i]["lon"] for i in place_ids]
    span_lat = max(1e-6, max(lats) - min(lats))
    span_lon = max(1e-6, max(lons) - min(lons))
    points = {lid: [0.10 + 0.80 * (locations[lid]["lon"] - min(lons)) / span_lon,
                    0.14 + 0.72 * (locations[lid]["lat"] - min(lats)) / span_lat]
              for lid in place_ids}
    min_gap = 0.32 if len(place_ids) <= 6 else 0.25
    for _ in range(300):
        for a in place_ids:
            for b in place_ids:
                if a >= b:
                    continue
                dx = points[b][0] - points[a][0]
                dy = points[b][1] - points[a][1]
                dist = math.hypot(dx, dy) or 0.001
                if dist < min_gap:
                    push = (min_gap - dist) / 2
                    ux, uy = dx / dist, dy / dist
                    points[a][0] -= ux * push; points[a][1] -= uy * push
                    points[b][0] += ux * push; points[b][1] += uy * push
        for lid in place_ids:
            points[lid][0] = min(0.90, max(0.10, points[lid][0]))
            points[lid][1] = min(0.84, max(0.14, points[lid][1]))
    return {lid: (p[0], p[1]) for lid, p in points.items()}


def ease(x: float) -> float:
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def where(segments: list[dict], t: float, track: str, places: set[str]):
    """(origin, target, progress, kind) for a character at story time t."""
    active = [s for s in segments if s["track"] == track
              and s["t_start"] - 0.01 <= t <= s["t_end"] + 0.01]
    if not active:
        return None, None, 0.0, "absent"
    segment = active[0]
    origin = segment["location_id"]
    if origin not in places:
        return None, None, 0.0, "absent"
    if segment["kind"] == "in-transit" and segment.get("to_location_id") in places:
        span = max(1e-6, segment["t_end"] - segment["t_start"])
        return origin, segment["to_location_id"], \
            ease((t - segment["t_start"]) / span), "transit"
    return origin, None, 0.0, segment["kind"]


def scene_at(scenes: list[dict], t: float, track: str):
    candidates = [s for s in scenes if s["track"] == track and s["t"] <= t + 0.05]
    return max(candidates, key=lambda s: s["t"]) if candidates else None


def wrap(name: str, width: int = 15, max_lines: int = 3) -> str:
    lines, line = [], ""
    for word in name.split():
        if len(line) + len(word) > width:
            lines.append(line); line = word
        else:
            line = f"{line} {word}".strip()
    lines.append(line)
    return "\n".join(lines[:max_lines])


def render(book_dir: Path, title: str) -> Path:
    timeline = load_timeline(book_dir)
    locations = timeline["locations"]
    candidates = pick_characters(timeline)
    acts = build_acts(timeline)
    plans = []
    for act in acts:
        ids = [i for i in act_places(timeline, act) if i in locations]
        plans.append({"places": ids, "pos": layout(ids, locations),
                      "cast": act_cast(timeline, act, candidates)})

    frames = []
    for index, act in enumerate(acts):
        lo, hi = act["chapters"]
        in_act = sorted((s for s in timeline["scenes"] if s["track"] == act["track"]
                         and lo <= s["chapter"] <= hi),
                        key=lambda s: (s["chapter"], s["scene"]))
        for scene in in_act:
            for step in range(max(2, int(SECONDS_PER_SCENE * FPS))):
                frames.append({"act": index, "t": scene["t"], "scene": scene,
                               "sub": step / max(1, int(SECONDS_PER_SCENE * FPS) - 1)})

    fig, ax = plt.subplots(figsize=(16, 9), dpi=110)
    fig.patch.set_facecolor(BG); ax.set_facecolor(BG)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.set_xticks([]); ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)

    node_r = 0.085                       # radius in Y; X is scaled for 16:9
    aspect = 9 / 16
    nodes, node_labels = [], []
    for _ in range(MAX_PLACES_PER_ACT):
        circle = Ellipse((0, 0), width=node_r * 2 * aspect, height=node_r * 2,
                         facecolor=NODE_FACE, edgecolor=NODE_EDGE,
                         lw=2.2, zorder=2, visible=False)
        ax.add_patch(circle)
        nodes.append(circle)
        node_labels.append(ax.text(0, 0, "", color="#c2d2e4", fontsize=12,
                                   ha="center", va="center", zorder=4,
                                   fontweight="bold", visible=False))

    artists = {}
    for i, cid in enumerate(candidates):
        color = PALETTE[i % len(PALETTE)]
        route = FancyArrowPatch((0, 0), (0.001, 0.001), arrowstyle="-", color=color,
                                lw=2.0, alpha=0.0, zorder=1)
        ax.add_patch(route)
        artists[cid] = {
            "dot": ax.plot([], [], "o", color=color, ms=18, zorder=6,
                           markeredgecolor=BG, markeredgewidth=2.2)[0],
            "tag": ax.text(0, 0, timeline["characters"].get(cid, {}).get("name", cid),
                           color=color, fontsize=11.5, zorder=7, ha="center",
                           va="center", fontweight="bold"),
            "color": color, "route": route,
        }

    fig.text(0.5, 0.955, title, color="#f2f6fb", fontsize=25, ha="center",
             fontweight="bold")
    act_text = fig.text(0.5, 0.902, "", color="#8fb4dd", fontsize=14.5, ha="center",
                        fontweight="bold")
    clock_text = fig.text(0.05, 0.902, "", color="#dbe6f3", fontsize=16, ha="left",
                          fontweight="bold")
    scene_text = fig.text(0.5, 0.035, "", color="#93a4b8", fontsize=13, ha="center")

    def update(index: int):
        frame = frames[index]
        act = acts[frame["act"]]
        plan = plans[frame["act"]]
        track = act["track"]
        positions, places = plan["pos"], set(plan["places"])
        scene = frame.get("scene") or scene_at(timeline["scenes"], frame["t"], track)
        active_place = scene["location_id"] if scene else None

        for slot, node in enumerate(nodes):
            label = node_labels[slot]
            if slot >= len(plan["places"]):
                node.set_visible(False); label.set_visible(False)
                continue
            lid = plan["places"][slot]
            x, y = positions[lid]
            live = lid == active_place
            node.set_center((x, y)); node.set_visible(True)
            grow = 1.12 if live else 1.0
            node.set_width(node_r * 2 * aspect * grow)
            node.set_height(node_r * 2 * grow)
            node.set_facecolor(NODE_ACTIVE if live else NODE_FACE)
            node.set_edgecolor(NODE_ACTIVE_EDGE if live else NODE_EDGE)
            node.set_linewidth(3.6 if live else 2.2)
            label.set_position((x, y)); label.set_text(wrap(locations[lid]["name"]))
            label.set_color("#eaf3ff" if live else "#c2d2e4")
            label.set_visible(True)

        cast = plan["cast"]
        for cid, art in artists.items():
            art["route"].set_alpha(0.0)
            if cid not in cast:
                art["dot"].set_alpha(0); art["tag"].set_alpha(0)
                continue
            origin, target, progress, kind = where(
                timeline["worldlines"].get(cid, []), frame["t"], track, places)
            if origin is None:
                art["dot"].set_alpha(0); art["tag"].set_alpha(0)
                continue
            slot = cast.index(cid)
            angle = 2 * math.pi * slot / max(1, len(cast)) - math.pi / 2
            ox_off = node_r * 1.0 * aspect * math.cos(angle)
            oy_off = node_r * 1.0 * math.sin(angle)
            ox, oy = positions[origin]
            x, y = ox + ox_off, oy + oy_off
            if target:
                tx, ty = positions[target]
                x += (tx + ox_off - x) * progress
                y += (ty + oy_off - y) * progress
                art["route"].set_positions((ox, oy), (tx, ty))
                art["route"].set_alpha(0.5)
            art["dot"].set_data([x], [y])
            visible = kind in ("observed", "transit")
            art["dot"].set_alpha(1.0 if visible else 0.4)
            art["dot"].set_markersize(20 if kind == "observed" else 16)
            # label pushed radially OUTWARD past the node edge — names never collide
            lx = ox + node_r * 1.95 * aspect * math.cos(angle)
            ly = oy + node_r * 1.62 * math.sin(angle)
            if target:
                tx, ty = positions[target]
                lx += (tx + node_r * 1.95 * aspect * math.cos(angle) - lx) * progress
                ly += (ty + node_r * 1.62 * math.sin(angle) - ly) * progress
            art["tag"].set_position((lx, ly))
            art["tag"].set_ha("left" if math.cos(angle) > 0.25 else
                              ("right" if math.cos(angle) < -0.25 else "center"))
            art["tag"].set_va("bottom" if math.sin(angle) >= 0 else "top")
            art["tag"].set_alpha(1.0 if visible else 0.4)

        act_text.set_text("PART I — LONDON, 1881" if track == "main"
                          else "PART II — UTAH  ·  Jefferson Hope's story")
        stamp = (scene or {}).get("date_display") or ""
        mark = {"stated": "", "stated-partial": "", "approx": " (approx.)",
                "approx-partial": " (approx.)"}.get((scene or {}).get("date_confidence"), "")
        clock_text.set_text(f"{stamp}{mark}" if stamp else "")
        if scene:
            scene_text.set_text(f"Chapter {scene['chapter']}  ·  {scene['summary'][:120]}")
        return []

    anim = animation.FuncAnimation(fig, update, frames=len(frames), blit=False,
                                   interval=1000 / FPS)
    out_dir = book_dir / "analysis"
    try:
        import imageio_ffmpeg
        plt.rcParams["animation.ffmpeg_path"] = imageio_ffmpeg.get_ffmpeg_exe()
        out = out_dir / f"{OUT_STEM}.mp4"
        anim.save(out, writer=animation.FFMpegWriter(fps=FPS, bitrate=4200))
    except Exception as exc:
        print(f"  mp4 writer unavailable ({exc}); writing GIF")
        out = out_dir / f"{OUT_STEM}.gif"
        anim.save(out, writer=animation.PillowWriter(fps=12))
    plt.close(fig)
    return out


def main() -> None:
    from studio import paths
    book_dir = paths.book_dir(CODEX_ID)
    manifest = json.loads((book_dir / "source" / "book.json").read_text(encoding="utf-8"))
    out = render(book_dir, manifest["title"])
    print(f"video written: {out}  ({out.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
