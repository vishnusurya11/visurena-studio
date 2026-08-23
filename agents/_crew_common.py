"""Shared helpers for the step-02 analysis crew (underscore prefix = not an agent)."""

from __future__ import annotations

import json


def render_chapter(chapter: dict) -> str:
    """Chapter text with paragraph numbers — the shared way every crew member
    sees the source, so paragraph anchors always agree."""
    lines = [f"CHAPTER {chapter['n']}: {chapter['title']}"]
    lines += [f"[para {p['n']}] {p['text']}" for p in chapter["paragraphs"]]
    return "\n".join(lines)


def render_call_sheet(call_sheet) -> str:
    """The 1st AD's scene list, as JSON, for specialists to work from."""
    return json.dumps(call_sheet.model_dump(), ensure_ascii=False, indent=1)


def crew_prompt(skill: str, chapter: dict, call_sheet=None) -> str:
    parts = [skill, "\n\n--- CHAPTER TEXT ---\n", render_chapter(chapter)]
    if call_sheet is not None:
        parts += ["\n\n--- SCENE BREAKDOWN (use these scene numbers) ---\n",
                  render_call_sheet(call_sheet)]
    return "".join(parts)
