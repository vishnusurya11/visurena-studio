"""The library as filed: every card, guide and the subject set validate, and the plan is whole."""
from __future__ import annotations

from pathlib import Path

from prism.catalog import load_guides, load_styles, load_subjects
from prism.compose import too_long
from prism.render import SUBJECTS, library_plan

STYLES, MODELS = Path("prism/styles"), Path("prism/models")


def test_the_subject_set_validates():
    assert len(load_subjects(SUBJECTS).subjects) == 5


def test_every_card_and_guide_validates():
    load_styles(STYLES)
    load_guides(MODELS)


def test_confusable_ids_name_held_styles():
    held = {s.id for s in load_styles(STYLES)}
    strays = {(s.id, c) for s in load_styles(STYLES) for c in s.confusable_with if c not in held}
    assert not strays


def test_the_plan_is_every_style_by_five_subjects_by_every_model():
    from prism.plan import planned_for
    planned, guides, subjects = library_plan(), load_guides(MODELS), load_subjects(SUBJECTS).subjects
    expected = sum(planned_for(s, subject, g) for g in guides.values() for s in load_styles(STYLES)
                   for subject in subjects)
    assert len(planned) == expected and len({(j.style, j.subject, j.model) for j in planned}) == expected


def test_no_planned_prompt_is_over_its_models_ceiling():
    guides = load_guides(MODELS)
    assert not [j.out for j in library_plan() if too_long(j.prompt, guides[j.model])]
