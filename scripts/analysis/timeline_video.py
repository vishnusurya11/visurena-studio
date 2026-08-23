"""Timeline video — characters moving between locations as story time advances.

THE acceptance test for the analysis stage (owner, 2026-08-23): if the timeline can
drive this, the analysis is real. Renders analysis/timeline.json as a 2D map animation:
locations are labeled points at real lat/lon, character dots sit at them and travel
between them as the story clock runs.

Design follows docs/analysis/research/11_narrative_map_animation.md:
  - act-based region switch (London frame / Utah flashback) — no wasted split screen
  - direct moving labels, not a detached legend
  - eased interpolation + fading comet trails
  - honest uncertainty: inferred transits are dashed/translucent
  - persistent story clock (day + chapter + track)

Zero cost, fully local. mp4 via bundled ffmpeg, GIF fallback on Windows.

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
from matplotlib.lines import Line2D

# --- configuration (hardcoded; no CLI args by convention) ---
CODEX_ID = "20260822113400"
FPS = 24
SECONDS_PER_STORY_DAY = 2.2      # time-warp: the book's tempo is wildly uneven
MAX_CHARACTERS = 8               # legibility ceiling from storyline-vis practice
TRAIL_DAYS = 1.6                 # comet-trail memory
OUT_STEM = "timeline_video"

PALETTE = ["#e6194b", "#4363d8", "#3cb44b", "#f58231", "#911eb4",
           "#42d4f4", "#f032e6", "#bfef45"]


def load_timeline(book_dir: Path) -> dict:
    return json.loads((book_dir / "analysis" / "timeline.json").read_text(encoding="utf-8"))


def pick_characters(timeline: dict) -> list[str]:
    """The most-travelled characters — those whose worldlines carry the story."""
    scored = sorted(timeline["worldlines"].items(),
                    key=lambda kv: (-len({s["location_id"] for s in kv[1]}), -len(kv[1])))
    return [cid for cid, _ in scored[:MAX_CHARACTERS]]


def act_cast(timeline: dict, act: dict, candidates: list[str]) -> set[str]:
    """Only characters actually OBSERVED in this act appear in it — a flashback cast
    must never ghost through the frame act at a stale position."""
    lo, hi = act["chapters"]
    cast = set()
    for cid in candidates:
        for segment in timeline["worldlines"].get(cid, []):
            if (segment["kind"] == "observed" and segment["track"] == act["track"]
                    and lo <= segment.get("chapter", -1) <= hi):
                cast.add(cid)
                break
    return cast


def build_track_plan(timeline: dict) -> list[dict]:
    """Telling order = acts. Each act is a contiguous run of chapters on one track."""
    scenes = sorted(timeline["scenes"], key=lambda s: (s["chapter"], s["scene"]))
    acts, current = [], None
    for scene in scenes:
        if current is None or scene["track"] != current["track"]:
            current = {"track": scene["track"], "chapters": [], "t_min": scene["t"],
                       "t_max": scene["t"], "regions": set()}
            acts.append(current)
        current["chapters"].append(scene["chapter"])
        current["t_min"] = min(current["t_min"], scene["t"])
        current["t_max"] = max(current["t_max"], scene["t"])
        current["regions"].add(scene.get("region", "other"))
    for act in acts:
        act["chapters"] = (min(act["chapters"]), max(act["chapters"]))
    return acts


def frame_schedule(acts: list[dict]) -> list[dict]:
    """One entry per rendered frame: which act, and the story time inside it."""
    frames = []
    for index, act in enumerate(acts):
        span = max(0.6, act["t_max"] - act["t_min"])
        count = max(FPS, int(span * SECONDS_PER_STORY_DAY * FPS))
        for i in range(count):
            frames.append({"act": index,
                           "t": act["t_min"] + span * (i / max(1, count - 1))})
    return frames


def ease(x: float) -> float:
    """Smoothstep — natural motion between locations."""
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def project(location: dict, region_bounds: dict) -> tuple[float, float]:
    """Equirectangular projection, scaled per region so each act fills the frame."""
    lat0, lat1, lon0, lon1 = region_bounds
    span_lat = max(0.02, lat1 - lat0)
    span_lon = max(0.02, lon1 - lon0)
    x = (location["lon"] - lon0) / span_lon
    y = (location["lat"] - lat0) / span_lat
    return x, y


def _median(values: list[float]) -> float:
    ordered = sorted(values)
    mid = len(ordered) // 2
    return ordered[mid] if len(ordered) % 2 else (ordered[mid - 1] + ordered[mid]) / 2


def core_locations(locations: list[dict]) -> list[dict]:
    """Drop far outliers so the map frames where the story ACTUALLY happens.
    (Watson's Afghanistan backstory must not squash London into a dot.)"""
    if len(locations) < 4:
        return locations
    clat = _median([loc["lat"] for loc in locations])
    clon = _median([loc["lon"] for loc in locations])
    spread = [(abs(loc["lat"] - clat) + abs(loc["lon"] - clon), loc) for loc in locations]
    typical = _median([d for d, _ in spread]) or 0.05
    kept = [loc for d, loc in spread if d <= max(typical * 4, 0.08)]
    return kept or locations


def bounds_for(locations: list[dict]) -> tuple[float, float, float, float]:
    locations = core_locations(locations)
    lats = [loc["lat"] for loc in locations] or [0]
    lons = [loc["lon"] for loc in locations] or [0]
    pad_lat = max(0.012, (max(lats) - min(lats)) * 0.22)
    pad_lon = max(0.012, (max(lons) - min(lons)) * 0.22)
    return (min(lats) - pad_lat, max(lats) + pad_lat,
            min(lons) - pad_lon, max(lons) + pad_lon)


def position_at(segments: list[dict], t: float, track: str, locations: dict,
                bounds) -> tuple[tuple[float, float] | None, str]:
    """Where is this character at story time t on this track? Returns (xy, kind)."""
    active = [s for s in segments if s["track"] == track
              and s["t_start"] - 0.01 <= t <= s["t_end"] + 0.01]
    if not active:
        past = [s for s in segments if s["track"] == track and s["t_end"] < t]
        if not past:
            return None, "absent"
        last = max(past, key=lambda s: s["t_end"])
        loc = locations.get(last.get("to_location_id") or last["location_id"])
        return (project(loc, bounds) if loc else None), "stale"
    segment = active[0]
    origin = locations.get(segment["location_id"])
    if not origin:
        return None, "absent"
    if segment["kind"] == "in-transit" and segment.get("to_location_id"):
        target = locations.get(segment["to_location_id"])
        if target:
            span = max(1e-6, segment["t_end"] - segment["t_start"])
            progress = ease((t - segment["t_start"]) / span)
            ax_, ay = project(origin, bounds)
            bx, by = project(target, bounds)
            return (ax_ + (bx - ax_) * progress, ay + (by - ay) * progress), "transit"
    return project(origin, bounds), segment["kind"]


def scene_at(scenes: list[dict], t: float, track: str) -> dict | None:
    candidates = [s for s in scenes if s["track"] == track and s["t"] <= t + 0.05]
    return max(candidates, key=lambda s: s["t"]) if candidates else None


def render(book_dir: Path, title: str) -> Path:
    timeline = load_timeline(book_dir)
    locations = timeline["locations"]
    characters = pick_characters(timeline)
    names = {cid: timeline["characters"].get(cid, {}).get("name", cid) for cid in characters}
    acts = build_track_plan(timeline)
    frames = frame_schedule(acts)

    act_casts = [act_cast(timeline, act, characters) for act in acts]
    act_locations, act_bounds = [], []
    for index, act in enumerate(acts):
        used = {s["location_id"] for s in timeline["scenes"]
                if s["track"] == act["track"] and s["location_id"]
                and act["chapters"][0] <= s["chapter"] <= act["chapters"][1]}
        in_act = [locations[i] for i in used if i in locations]
        in_act = core_locations(in_act) or list(locations.values())
        act_locations.append(in_act)
        act_bounds.append(bounds_for(in_act))

    fig, ax = plt.subplots(figsize=(16, 9), dpi=110)
    fig.patch.set_facecolor("#0e1117")
    ax.set_facecolor("#0e1117")
    ax.set_xlim(-0.08, 1.08)
    ax.set_ylim(-0.08, 1.08)
    ax.set_xticks([]); ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)

    place_dots = ax.scatter([], [], s=70, c="#39424e", marker="o", zorder=2)
    place_labels = [ax.text(0, 0, "", color="#8b98a8", fontsize=8, ha="center",
                            va="top", zorder=2) for _ in range(40)]
    artists: dict[str, dict] = {}
    for i, cid in enumerate(characters):
        color = PALETTE[i % len(PALETTE)]
        artists[cid] = {
            "trail": ax.plot([], [], color=color, lw=1.6, alpha=0.35, zorder=3)[0],
            "dot": ax.plot([], [], "o", color=color, ms=13, zorder=5,
                           markeredgecolor="white", markeredgewidth=0.8)[0],
            "tag": ax.text(0, 0, names[cid], color=color, fontsize=10, zorder=6,
                           ha="center", va="bottom", fontweight="bold"),
            "history": [],
            "color": color,
        }

    title_text = fig.text(0.5, 0.955, title, color="#e8eef6", fontsize=19,
                          ha="center", fontweight="bold")
    clock_text = fig.text(0.5, 0.915, "", color="#9fb3c8", fontsize=13, ha="center")
    scene_text = fig.text(0.5, 0.045, "", color="#7f8fa4", fontsize=11, ha="center")
    act_text = fig.text(0.035, 0.93, "", color="#c9d6e4", fontsize=12, ha="left",
                        fontweight="bold")
    night = plt.Rectangle((-0.1, -0.1), 1.3, 1.3, color="#0a1c3d", alpha=0.0, zorder=1)
    ax.add_patch(night)

    state = {"act": -1}

    def update(frame_index: int):
        frame = frames[frame_index]
        act = acts[frame["act"]]
        if frame["act"] != state["act"]:          # act change = new map, new bounds
            state["act"] = frame["act"]
            for art in artists.values():
                art["history"] = []
                art["trail"].set_data([], [])
        bounds = act_bounds[frame["act"]]
        track = act["track"]
        here = act_locations[frame["act"]]

        xs, ys = [], []
        placed: list[tuple[float, float]] = []
        for i, label in enumerate(place_labels):
            if i < len(here):
                x, y = project(here[i], bounds)
                xs.append(x); ys.append(y)
                drop = 0.030
                while any(abs(px - x) < 0.11 and abs(py - (y - drop)) < 0.022
                          for px, py in placed):
                    drop += 0.026
                placed.append((x, y - drop))
                label.set_position((x, y - drop))
                label.set_text(here[i]["name"][:26])
                label.set_alpha(0.85)
            else:
                label.set_alpha(0)
        place_dots.set_offsets(list(zip(xs, ys)) or [(0, 0)])

        scene = scene_at(timeline["scenes"], frame["t"], track)
        cast = act_casts[frame["act"]]
        for cid, art in artists.items():
            if cid not in cast:
                art["dot"].set_alpha(0); art["tag"].set_alpha(0)
                art["trail"].set_alpha(0)
                art["history"] = []
                continue
            xy, kind = position_at(timeline["worldlines"].get(cid, []), frame["t"],
                                   track, locations, bounds)
            if xy is None:
                art["dot"].set_alpha(0); art["tag"].set_alpha(0)
                art["trail"].set_alpha(0)
                continue
            slot = sorted(cast).index(cid) if cid in cast else 0
            angle = 2 * math.pi * slot / max(1, len(cast))
            x = xy[0] + 0.055 * math.cos(angle)
            y = xy[1] + 0.048 * math.sin(angle)
            art["dot"].set_data([x], [y])
            above = math.sin(angle) >= 0
            art["tag"].set_position((x, y + (0.026 if above else -0.040)))
            art["tag"].set_va("bottom" if above else "top")
            alpha = {"observed": 1.0, "transit": 0.95, "presumed": 0.5,
                     "stale": 0.0, "absent": 0.0}.get(kind, 0.6)
            art["dot"].set_alpha(alpha); art["tag"].set_alpha(min(1.0, alpha + 0.1))
            art["dot"].set_markersize(15 if kind == "observed" else 11)
            art["history"].append((frame["t"], x, y))
            recent = [(hx, hy) for ht, hx, hy in art["history"]
                      if frame["t"] - ht <= TRAIL_DAYS]
            art["trail"].set_data([p[0] for p in recent], [p[1] for p in recent])
            art["trail"].set_alpha(0.32 if kind != "stale" else 0.12)

        if scene:
            night.set_alpha(0.32 if scene.get("time_of_day") == "NIGHT" else 0.0)
            scene_text.set_text(f"Ch {scene['chapter']} · {scene['summary'][:110]}")
        label = "PART I — LONDON, 1881" if track == "main" else \
                "PART II — THE COUNTRY OF THE SAINTS (told by Jefferson Hope)"
        act_text.set_text(label)
        clock_text.set_text(f"Story day {int(frame['t']):>2}   ·   chapters "
                            f"{act['chapters'][0]}–{act['chapters'][1]}")
        return []

    anim = animation.FuncAnimation(fig, update, frames=len(frames), blit=False,
                                   interval=1000 / FPS)
    out_dir = book_dir / "analysis"
    try:
        import imageio_ffmpeg
        plt.rcParams["animation.ffmpeg_path"] = imageio_ffmpeg.get_ffmpeg_exe()
        out = out_dir / f"{OUT_STEM}.mp4"
        anim.save(out, writer=animation.FFMpegWriter(fps=FPS, bitrate=3600))
    except Exception as exc:                                   # Windows-safe fallback
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
