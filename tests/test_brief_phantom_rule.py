"""The writer hears G-PHANTOM up front (ep18, 2026-10-05): the gates each
learned their rule from an owner audit, the writer never did -- so the brief's
PICTURE RULES carry the empty-stage rule and the writer stops producing the
sentences the battery would strip.  No API."""
from __future__ import annotations

from studio import plan_brief


def test_exactly_one_picture_rule_names_the_phantom_gate():
    hits = [r for r in plan_brief.PICTURE_RULES if "G-PHANTOM" in r]
    assert len(hits) == 1
    assert "described" in hits[0] and "geometry" in hits[0]
    assert "crowd" in hits[0]        # where people legitimately live


def test_render_carries_the_rule_under_the_picture_rules_heading():
    text = plan_brief.render({"picture_rules": plan_brief.PICTURE_RULES})
    head = text.index(plan_brief.SECTIONS["picture_rules"])
    assert "G-PHANTOM" in text[head:]
