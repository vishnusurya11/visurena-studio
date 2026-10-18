"""A Prism prompt: the model guide's template over (style, subject, camera).

The eval composes deterministically, so across styles only the style words move.
`writer_messages` is the other road: the guide's system prompt and the style card
handed to an LLM prompt writer (a future book's own shots, written in a held style).
"""
from __future__ import annotations

import json
import re

from prism.catalog import ModelGuide, Style, Subject


def style_text(style: Style, model_id: str) -> str:
    own = style.models.get(model_id)
    return own.style if own else style.style_words


def recap_text(style: Style, model_id: str) -> str:
    own = style.models.get(model_id)
    return own.recap if own else ""


def compose(style: Style, guide: ModelGuide, subject: Subject) -> str:
    """The template over the parts; a subject's own form for this model carries its camera;
    a whole caption from the vendor's upsampler is the prompt as written."""
    own = style.models.get(guide.id)
    if own and subject.id in own.captions:
        return own.captions[subject.id]
    form = subject.forms.get(guide.id)
    said = guide.template.format(style=style_text(style, guide.id), subject=form or subject.prose,
                                 camera="" if form else subject.camera, recap=recap_text(style, guide.id))
    return re.sub(r"\s+", " ", said).strip()


def too_long(prompt: str, guide: ModelGuide) -> bool:
    return len(prompt.split()) > guide.max_words


def writer_messages(style: Style, guide: ModelGuide, subject: Subject) -> tuple[str, str]:
    """(system, user) for the LLM prompt writer of this model."""
    card = style.model_dump(include={"id", "name", "summary", "traits", "style_words", "avoid", "lineage"})
    card["style_words"] = style_text(style, guide.id)
    ask = {"style": card, "subject": subject.prose, "camera": subject.camera}
    return guide.system_prompt, json.dumps(ask, ensure_ascii=False)
