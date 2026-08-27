"""The audit runner. Fake judges throughout — no test may call a paid API."""

from __future__ import annotations

from scripts.screenplay import audit_locations as al
from studio.screenplay_spec import Scene, SceneRef, Slug

SLUG = Slug(int_ext="INT", location_id="221b", location_name="221B Baker Street",
            time="DAY", text="INT. 221B BAKER STREET - DAY")

DOSSIER = {
    "locations": [{"id": "221b", "name": "221B Baker Street"},
                  {"id": "lauriston", "name": "3 Lauriston Gardens"}],
    "scenes": [{"chapter": 1, "scene": 1, "synopsis": "They talk in the sitting room.",
                "dialogue": [{"speech": "You have been in Afghanistan."}]}],
}


def _scene(number=1, location="221b"):
    return Scene(number=number, beat_id="b1",
                 slug=SLUG.model_copy(update={"location_id": location}),
                 source=[SceneRef(chapter=1, scene=1)])


class _Judges:
    """Returns a scripted answer per call, so a scene can be given disagreeing judges."""

    def __init__(self, answers):
        self.answers, self.calls, self.prompts = list(answers), 0, []

    def __call__(self, prompt, structured_output_model=None):
        from types import SimpleNamespace
        self.prompts.append(prompt)
        answer = self.answers[self.calls % len(self.answers)]
        self.calls += 1
        return SimpleNamespace(
            structured_output=structured_output_model.model_validate(
                {"location_id": answer, "confidence": "high",
                 "evidence": "they sat in the room", "evidence_kind": "stated_presence"}),
            metrics=SimpleNamespace(accumulated_usage={
                "inputTokens": 50, "outputTokens": 10, "totalTokens": 60}))


def _audit(answers, pipeline="221b", judges=3, monkeypatch=None):
    from agents import location_auditor
    fake = _Judges(answers)
    original = location_auditor.judge
    location_auditor.judge = lambda p, l, previous_location=None, usage=None: \
        original(p, l, previous_location=previous_location, _agent=fake)
    try:
        return al.audit_scene(_scene(location=pipeline), DOSSIER, None, judges), fake
    finally:
        location_auditor.judge = original


def test_three_judges_are_asked():
    _, fake = _audit(["221b"])
    assert fake.calls == 3


def test_unanimous_agreement_with_the_pipeline_confirms():
    row, _ = _audit(["221b"])
    assert row["verdict"] == "confirmed" and row["level"] == "unanimous"


def test_unanimous_disagreement_names_the_pipeline_wrong():
    row, _ = _audit(["lauriston"], pipeline="221b")
    assert row["verdict"] == "wrong" and row["should_be"] == "lauriston"


def test_a_split_is_reported_as_unknowable_not_as_a_pipeline_error():
    row, _ = _audit(["221b", "lauriston", "ambiguous"])
    assert row["verdict"] == "unknowable"


def test_every_judgment_is_kept_for_inspection():
    """A consensus nobody can audit is just another opinion."""
    row, _ = _audit(["221b", "lauriston", "221b"])
    assert len(row["judgments"]) == 3
    assert {j["location_id"] for j in row["judgments"]} == {"221b", "lauriston"}


def test_no_judge_is_shown_the_pipeline_answer():
    """The whole method rests on this. If the prompt leaked the pipeline's choice, the
    agreement would be an echo and would measure nothing."""
    _, fake = _audit(["221b"], pipeline="lauriston")
    assert all("lauriston" not in p or "3 Lauriston Gardens" in p
               for p in fake.prompts)


def test_no_judge_is_shown_another_judges_answer():
    _, fake = _audit(["221b", "lauriston", "221b"])
    assert all("stated_presence" not in p for p in fake.prompts)


def test_the_brief_carries_the_book_text_and_the_location_list():
    from agents.location_auditor import brief
    payload = brief(["some prose"], DOSSIER["locations"], previous_location="221b")
    assert payload["scene_source_text"] == ["some prose"]
    assert {loc["id"] for loc in payload["canonical_locations"]} == {"221b", "lauriston"}


def test_the_previous_location_is_labelled_as_previous_not_proposed():
    from agents.location_auditor import brief
    payload = brief([], [], previous_location="221b")
    assert payload["previous_scene_location"] == "221b"
    assert "proposed" not in json_keys(payload)


def json_keys(payload):
    return " ".join(payload.keys())


# --- the analysis-level audit ------------------------------------------------------

def test_a_small_book_is_sampled_whole():
    from scripts.analysis.audit_locations import stratified
    scenes = [{"n": i} for i in range(10)]
    assert stratified(scenes, 25) == scenes


def test_the_sample_spans_the_whole_book():
    """Evenly spaced, not random: location errors cluster positionally - a flashback
    block, the last chapter - and a random sample can miss a whole run of them."""
    from scripts.analysis.audit_locations import stratified
    scenes = [{"n": i} for i in range(100)]
    got = stratified(scenes, 5)
    assert got[0]["n"] == 0 and got[-1]["n"] == 99 and len(got) == 5


def test_the_sample_is_the_requested_size():
    from scripts.analysis.audit_locations import stratified
    assert len(stratified([{"n": i} for i in range(100)], 25)) == 25


def test_scene_text_carries_the_named_place_as_a_claim_not_an_answer():
    """The text NAMING a place is the weakest evidence and the commonest source of a
    wrong answer, so it is labelled rather than presented as fact."""
    from scripts.analysis.audit_locations import scene_text
    lines = scene_text({"synopsis": "They talk.", "location_text": "Utah"})
    assert any("the text names" in line for line in lines)


def test_scene_text_survives_a_scene_with_nothing():
    from scripts.analysis.audit_locations import scene_text
    assert scene_text({}) == []
