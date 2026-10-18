"""Prism fixtures built from the contract (prism.catalog), never hand-written JSON drift."""
from __future__ import annotations

from prism.catalog import Lineage, ModelGuide, Style, Subject, SubjectSet, Traits

WORDS = ("Hand-drawn 2D cel animation frame in the look of Hellsing Ultimate (2006): sharp angular "
         "black ink linework, jagged black shadow shapes, flat two-tone cel shading, a red and black "
         "palette with crimson shadows, grainy OVA film texture.")


def style(sid: str = "anime_hellsing_gothic", name: str = "Hellsing gothic", **over) -> Style:
    family = "live_action" if sid.startswith("live_") else "anime"
    card = dict(id=sid, name=name, family=family, summary="Angular gothic ink anime.",
                lineage=Lineage(titles=["Hellsing Ultimate (2006)"]),
                traits=Traits(line="sharp black ink", shading="hard two-tone", palette="red and black",
                              lighting="low key", faces="long angular", backgrounds="gothic stone",
                              texture="OVA grain", camera="low angles"),
                style_words=WORDS, avoid=["goes photoreal"], sources=["https://example.org/hellsing"],
                added="2026-10-17", run="r001")
    return Style(**{**card, **over})


def guide(gid: str = "krea2", template: str = "{style} {subject} {camera}", **over) -> ModelGuide:
    card = dict(id=gid, label=gid.title(), workflow=f"image_{gid}_t2i", values={"width": 1024},
                template=template, max_words=200, negative_supported=False,
                system_prompt="Write one prompt.", sources=["https://example.org/guide"])
    return ModelGuide(**{**card, **over})


def subjects() -> SubjectSet:
    rows = [("count", "character"), ("castle", "location"), ("arrival", "scene"),
            ("diary", "scene"), ("chase", "scene")]
    return SubjectSet(story="Dracula", subjects=[
        Subject(id=sid, kind=kind, title=sid.title(), prose=f"The {sid}.", camera="Wide shot.", seed=1000 + i)
        for i, (sid, kind) in enumerate(rows)])
