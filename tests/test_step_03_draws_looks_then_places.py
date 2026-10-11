"""Step 03 on a book with a look table: 03_04 looks first (Krea2 loads once),
then places; it is not done while a staged look or a place state is missing,
and 03_05 names each derived state as its setup's view through write_plan."""
from __future__ import annotations

import json

from studio import episode_home, look_timeline
from studio.continuity_spec import CharacterLooks
from tests import continuity_fixtures as fx
from tests.test_episode_steps_run_alone import CODEX, ctx  # noqa: F401  (the fixture)

from scripts.episode import step_03_places


def test_a_table_book_draws_looks_before_places(ctx):  # noqa: F811
    look_timeline.write_looks(ctx.book_dir, "narrator", CharacterLooks.model_validate(fx.CARD))
    step_03_places.run(ctx)
    assert [c[0] for c in ctx.launched][:2] == ["scripts/refs/looks.py", "scripts/refs/places.py"]


def test_a_place_state_not_yet_derived_keeps_the_step_open(ctx):  # noqa: F811
    loc = ctx.book_dir / "refs" / "locations" / "yard"
    loc.mkdir(parents=True)
    (loc / "wide_establishing.png").write_bytes(fx.PNG)
    doc = {"setups": {"yard": {"location": "yard", "view": "", "place_state": "trampled mud"}}}
    assert step_03_places.states_left(ctx.book_dir, doc) == [("yard", "yard", "wide_establishing",
                                                              "wide_establishing__trampled_mud")]
    (loc / "wide_establishing__trampled_mud.png").write_bytes(fx.PNG)
    assert step_03_places.states_left(ctx.book_dir, doc) == []


def test_a_derived_state_is_named_in_the_plan(ctx, monkeypatch):  # noqa: F811
    plan = ctx.home / "plan.json"
    doc = json.loads(plan.read_text(encoding="utf-8"))
    doc["setups"]["yard"]["place_state"] = "trampled mud"
    plan.write_text(json.dumps(doc), encoding="utf-8")
    (ctx.book_dir / "refs" / "locations" / "yard").mkdir(parents=True)
    (ctx.book_dir / "refs" / "locations" / "yard" / "wide_establishing__trampled_mud.png").write_bytes(fx.PNG)
    wrote = []
    monkeypatch.setattr(episode_home, "write_plan", lambda path, d: wrote.append(d))
    monkeypatch.setattr("studio.plan_provenance.record", lambda *a: None)
    step_03_places.name_variants(ctx)
    assert wrote[0]["setups"]["yard"]["view"] == "wide_establishing__trampled_mud"
