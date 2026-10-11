"""Round-2 bench (R2_verdict §0.7, §2.3): the overlay copied only the model nodes
and `steps`, so a `simple` arm ran `beta`, a 992 arm ran 768 and a CK-attention
arm lost its node -- three 'no difference' results from the instrument itself.
Every knob an arm claims is laid over the shipped graph and read back; an arm
claiming a knob the graph does not carry is refused, one test per knob."""
import pytest

from scripts.bench import h3_arms as arms
from tests.test_bench_arm_graphs_carry_their_knobs import four_step_arm, shipped


def with_panel(g: dict) -> dict:
    g["8"]["inputs"].update({"width": 768, "height": 768, "ref_image_size": "match"})
    g["20"] = {"class_type": "LoadImage", "inputs": {"image": "shot_12_abcd.png"}}
    g["11"] = {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler"}}
    g["9"]["inputs"]["scheduler"] = "beta"
    return g


def arm(edit: dict | None = None) -> dict:
    g = with_panel(four_step_arm())
    g["8"]["inputs"].update({"width": 1280, "height": 736})   # a template default, never a claim
    for (node, key), value in (edit or {}).items():
        g[node]["inputs"][key] = value
    return g


def ck_arm() -> dict:
    g = arm()
    g["attn"] = {"class_type": "ModelAttentionBackend",
                 "inputs": {"model": ["3", 0], "attention": "comfy kitchen attention"}}
    g["4"]["inputs"]["model"] = ["attn", 0]
    return g


def laid(a: dict, **kw) -> dict:
    return arms.knobs(arms.arm_graph(with_panel(shipped()), a, prefix="bench_x", **kw))


def test_the_scheduler_is_the_arms():
    assert laid(arm({("9", "scheduler"): "simple"}))["scheduler"] == "simple"


def test_the_sampler_is_the_arms():
    assert laid(arm({("11", "sampler_name"): "er_sde"}))["sampler"] == "er_sde"


def test_the_shift_is_the_arms():
    k = laid(arm({("4", "shift_video"): 6}))
    assert k["shift_video"] == 6 and k["shift_audio"] == 3.0


def test_the_ref_image_size_is_the_arms():
    assert laid(arm({("8", "ref_image_size"): "max"}))["ref_image_size"] == "max"


def test_the_canvas_is_the_jobs_and_the_templates_default_never_leaks():
    assert (laid(arm())["width"], laid(arm())["height"]) == (768, 768)
    k = laid(arm(), canvas=(992, 992))
    assert (k["width"], k["height"]) == (992, 992)


def test_the_attention_node_is_carried_and_wired():
    out = arms.arm_graph(with_panel(shipped()), ck_arm(), prefix="bench_x")
    assert arms.knobs(out)["attention_backend"] == "comfy kitchen attention"
    assert out["4"]["inputs"]["model"] == ["attn", 0] and out["attn"]["inputs"]["model"] == ["3", 0]


def test_a_graph_without_the_attention_node_reads_none():
    assert laid(arm())["attention_backend"] is None


def test_a_restaged_panel_is_the_jobs():
    k = laid(arm(), images={"20": "shot_12_992.png"})
    assert k["panel"] == "shot_12_992.png"


def test_the_panel_pixel_size_is_read_when_a_sizer_is_given():
    g = arms.arm_graph(with_panel(shipped()), arm(), prefix="bench_x")
    assert arms.knobs(g, sizer=lambda name: (992, 992))["panel_px"] == [992, 992]


@pytest.mark.parametrize("claim", [{"scheduler": "simple"}, {"sampler": "er_sde"}, {"shift_video": 6},
                                   {"width": 992}, {"ref_image_size": "max"},
                                   {"attention_backend": "comfy kitchen attention"}])
def test_an_arm_claiming_a_knob_its_graph_lacks_is_refused(claim):
    with pytest.raises(AssertionError):
        arms.assert_knobs(laid(arm()), claim)


def test_the_rendered_size_must_be_the_canvas():
    arms.assert_size({"width": 992, "height": 992}, (992, 992))
    with pytest.raises(AssertionError):
        arms.assert_size({"width": 992, "height": 992}, (768, 768))


def test_a_job_stages_its_panel_and_asks_its_canvas(monkeypatch, tmp_path):
    import json
    (tmp_path / "g.json").write_text(json.dumps(with_panel(shipped())), "utf-8")
    monkeypatch.setattr(arms, "arm_template", lambda name: arm())
    monkeypatch.setattr(arms, "stage", lambda path: "shot_12_992.png")
    monkeypatch.setattr(arms, "staged_px", lambda name: (992, 992))
    g = arms.build({"graph": str(tmp_path / "g.json"), "arm": "a", "tag": "t", "canvas": [992, 992],
                    "stage": {"20": "p.png"}, "expect": {"width": 992, "panel_px": [992, 992]}})
    assert arms.knobs(g)["panel"] == "shot_12_992.png"


def test_a_job_whose_panel_is_not_its_canvas_is_refused(monkeypatch, tmp_path):
    import json
    (tmp_path / "g.json").write_text(json.dumps(with_panel(shipped())), "utf-8")
    monkeypatch.setattr(arms, "arm_template", lambda name: arm())
    monkeypatch.setattr(arms, "staged_px", lambda name: (768, 768))
    with pytest.raises(AssertionError):
        arms.build({"graph": str(tmp_path / "g.json"), "arm": "a", "tag": "t", "canvas": [992, 992]})


def test_a_wrong_size_render_is_kept_and_named():
    assert arms.size_fault({"width": 992, "height": 992}, [992, 992]) == ""
    assert "768" in arms.size_fault({"width": 992, "height": 992}, [768, 768])
