"""Turn a book's character, location and prop designs into reference-image jobs.

The designs live under library/<book>/analysis/{characters,locations,props}/
as `profile.design`.  Each job is one picture: ONE sheet per character (its
wardrobe states -- soaked, scalded, grey -- are said in the ref2v take prompt,
never drawn as extra sheets), ONE wide per location, ONE sheet per prop.  Only the
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
# ONE picture per location: its establishing wide.  Views drawn each from
# words came out as different rooms (ep01's observatory: a slim brass refractor
# on a tripod in the wide, a massive telescope on a pier in the reverse), and
# the cut jumped between them.  OWNER 2026-09-18: "just have a wide image ..
# ref2v can close up based on camera" -- the take's camera finds the medium or
# the insert inside the one room; no derived or edited views.
ANCHOR = "wide_establishing"


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


def anchor_view(views: list[dict]) -> dict:
    """The one view drawn from words: the establishing wide, else the first."""
    return next((v for v in views if v["id"] == ANCHOR), views[0])


def location_jobs(lid: str, profile: dict) -> list[Job]:
    """Exactly one picture per location: the establishing wide."""
    views = (profile.get("design") or {}).get("views") or []
    if not views:
        return []
    anchor = anchor_view(views)
    return [Job("locations", lid, anchor["id"], T2I, anchor["prompt"], 1536, 1024)]


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
