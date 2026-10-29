"""Wide/full takes may render with more sampling work on the face (face-blur PLAN fix #4,
docs/audit/2026-10-19_face_blur/prevent_at_render.md section D), behind a switch that is OFF
until the GPU bench (arm A3, T01/T06) measures it.

The brick: H3 draws a 768 take on a 24x24 token grid; a 25-60 px face is one or two tokens,
and the 8-step distilled sampler loses the highest-frequency detail first.  The new graph is
the wide/full graph with 15 steps and the second turbo LoRA at 0.4 instead of 0.7; `beta` is
already its scheduler.  Both ran on Spark-H3 attention until ComfyUI 0.43 (2026-10-29), now CK.

ep01 (Jekyll Kawajiri) put 4 of 28 takes on the wide/full graph (T01, T06, T08, T18); their
sampling measured 45 + 59 + 58 + 44 = 206 s at 8 steps (takes/r2v/phases.jsonl), so 15 steps
add about 7/8 of that: about 3 min per episode, about 6 min with one retake each.
"""
from scripts.episode import takes_r2v

BASE = "video_minimax_h3_r2v_turbo_ref8_crf_visurena_ckattn_comfyorg"
WIDE = BASE + "_wide15_visurena"


def test_the_wide_detail_graph_is_pinned_by_name():
    assert takes_r2v.WIDE_DETAIL_BASE == WIDE


def test_the_switch_is_off_unless_the_environment_turns_it_on():
    assert takes_r2v.wide_detail_on({}) is False
    assert takes_r2v.wide_detail_on({"TAKE_WIDE_DETAIL": "0"}) is False
    assert takes_r2v.wide_detail_on({"TAKE_WIDE_DETAIL": "1"}) is True


def test_with_the_switch_off_a_wide_take_stays_on_the_base(monkeypatch):
    monkeypatch.setattr(takes_r2v, "WIDE_DETAIL", False)
    assert takes_r2v.workflow_for({"sizes": ["wide"]}) == BASE


def test_with_the_switch_on_wide_and_full_takes_render_on_the_wide_graph(monkeypatch):
    monkeypatch.setattr(takes_r2v, "WIDE_DETAIL", True)
    assert takes_r2v.workflow_for({"sizes": ["wide"]}) == WIDE
    assert takes_r2v.workflow_for({"sizes": ["full"]}) == WIDE
    assert takes_r2v.workflow_for({"sizes": ["medium", "wide"]}) == WIDE


def test_with_the_switch_on_close_takes_and_unsized_cards_do_not_move(monkeypatch):
    monkeypatch.setattr(takes_r2v, "WIDE_DETAIL", True)
    assert takes_r2v.workflow_for({"sizes": ["close"]}) == takes_r2v.WULI_BASE
    assert takes_r2v.workflow_for({}) == BASE


def test_the_wide_graph_samples_fifteen_steps_and_the_others_eight():
    assert takes_r2v.steps_for(WIDE) == 15
    assert takes_r2v.steps_for(BASE) == takes_r2v.STEPS == 8
    assert takes_r2v.steps_for(takes_r2v.WULI_BASE) == 8


def test_the_wide_graph_is_the_base_with_more_steps_and_a_lighter_second_lora():
    from studio.comfy import load_workflow
    base, _ = load_workflow(BASE)
    wide, _ = load_workflow(WIDE)
    changed = {k for k in base if base[k] != wide[k]}
    assert set(wide) == set(base) and changed <= {"9", "attn", "lora_second", "17"}
    assert wide["lora_second"]["inputs"]["strength_model"] == 0.4
    assert wide["2"]["inputs"]["strength_model"] == 1.0
    assert wide["9"]["inputs"]["scheduler"] == "beta"


def test_the_wide_graph_samples_the_steps_it_is_injected_with():
    from studio.comfy import load_workflow
    wide, _ = load_workflow(WIDE)
    assert wide["9"]["inputs"]["steps"] == takes_r2v.steps_for(WIDE)
    assert wide["attn"]["class_type"] == "ModelAttentionBackend"


def test_the_wide_graph_takes_every_value_the_take_renderer_injects():
    from studio.comfy import load_workflow
    _, base = load_workflow(BASE)
    _, wide = load_workflow(WIDE)
    assert wide == base


def test_the_wide_graph_has_a_model_line_and_queues_after_the_base(monkeypatch):
    monkeypatch.setattr(takes_r2v, "WIDE_DETAIL", True)
    assert "15-step" in takes_r2v.MODELS[WIDE]
    jobs = [({"index": 1, "sizes": ["wide"]}, {}), ({"index": 2, "sizes": ["close"]}, {})]
    assert [c["index"] for c, _ in takes_r2v.by_model(jobs)] == [2, 1]
