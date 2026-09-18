"""Turn a book's character, location and prop designs into reference-image jobs.

The designs live under library/<book>/analysis/{characters,locations,props}/
as `profile.design`.  Each job is one picture: ONE sheet per character (its
wardrobe states -- soaked, scalded, grey -- are said in the ref2v take prompt,
never drawn as extra sheets), a location's views, ONE sheet per prop.  Only the
props words cannot pin (the Martian machines, the red weed…) are drawn at all;
the runner is given that short list with --only.
Paths are relative to the book folder -- never absolute.
"""
from __future__ import annotations

import zlib
from dataclasses import dataclass

STYLE_LEAD = ("A 3d, clean ultra hd, AAA game quality graphics, computer generated CGI image, "
              "great detail, high contrast, highly accurate character model and texture, "
              "realistic lighting. A heavily angular 3d art style with brush stroke colour "
              "texture. Cinematic film still of ")
T2I = "image_krea2_cinematic_2x"


@dataclass(frozen=True)
class Job:
    kind: str
    entity: str
    name: str
    workflow: str
    prompt: str
    width: int
    height: int


def styled(body: str) -> str:
    """The house look leads every prompt; the subject follows."""
    return STYLE_LEAD + body


def seed_for(key: str) -> int:
    """A stable seed per picture, so a rerun redraws the same image."""
    return zlib.crc32(key.encode("utf-8"))


def relpath(job: Job) -> str:
    return f"refs/{job.kind}/{job.entity}/{job.name}.png"


def character_jobs(cid: str, profile: dict) -> list[Job]:
    design = profile.get("design") or {}
    sheet = design.get("sheet_prompt")
    if not sheet or design.get("render") is False:
        return []
    return [Job("characters", cid, "sheet", T2I, sheet, 1536, 1024)]


def view_jobs(kind: str, eid: str, views: list[dict]) -> list[Job]:
    return [Job(kind, eid, v["id"], T2I, v["prompt"], 1536, 1024) for v in views]


def location_jobs(lid: str, profile: dict) -> list[Job]:
    return view_jobs("locations", lid, (profile.get("design") or {}).get("views") or [])


def prop_jobs(pid: str, profile: dict) -> list[Job]:
    """One sheet per prop, like a character; its states are said in the take prompt."""
    sheet = (profile.get("design") or {}).get("sheet_prompt")
    return [Job("props", pid, "sheet", T2I, sheet, 1536, 1024)] if sheet else []


def jobs_for(kind: str, eid: str, profile: dict) -> list[Job]:
    build = {"characters": character_jobs, "locations": location_jobs, "props": prop_jobs}[kind]
    return build(eid, profile)


def pending(jobs: list[Job], exists) -> list[Job]:
    """Jobs whose picture is not yet on disk; `exists` takes a relpath."""
    return [j for j in jobs if not exists(relpath(j))]


def values_for(job: Job) -> dict:
    """The manifest inject values for one job."""
    return {"prompt": styled(job.prompt), "width": job.width, "height": job.height,
            "seed": seed_for(relpath(job)),
            "filename_prefix": f"wotw_refs/{job.kind}_{job.entity}_{job.name}"}


def only_views(jobs: list[Job], views: set[str] | None) -> list[Job]:
    """Keep only the named location views; characters and props pass through.

    OWNER 2026-09-18: draw only what a chapter uses.  A location has 3-6 views
    and an episode may use two of them, so the filter is by view, not by place."""
    if not views:
        return jobs
    return [j for j in jobs if j.kind != "locations" or j.name in views]
