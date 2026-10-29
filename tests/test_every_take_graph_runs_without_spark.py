"""ComfyUI 0.43 (owner 2026-10-29: "Upgrade production to 0.43") needs comfy-kitchen 0.2.40, and the
Spark-H3 kitchen (0.2.37+spark) cannot load beside it: a take graph holding MiniMaxH3SparkAttention*
fails on the engine.  Every graph a take is routed to holds the CK int8 attention instead, the
same speed measured (T14 104.8 s cold / 92.4 s warm vs 107 s on Spark)."""
import pytest

from scripts.episode import takes_r2v as tr
from studio.comfy import WORKFLOWS, load_workflow

pytestmark = pytest.mark.skipif(not WORKFLOWS.exists(), reason="comfy_studio workflows not on this machine")


@pytest.mark.parametrize("base", sorted(tr.MODELS))
def test_no_take_graph_holds_a_spark_node(base):
    template, _inject = load_workflow(base)
    kinds = {n["class_type"] for n in template.values()}
    assert not any(k.startswith("MiniMaxH3SparkAttention") for k in kinds), base
    assert "ModelAttentionBackend" in kinds, base


def test_the_routes_name_the_ck_twins():
    assert tr.workflow_for({"sizes": ["close"]}) == tr.WULI_BASE
    assert tr.workflow_for({"sizes": ["wide"]}) == tr.WIDE_BASE == tr.ROLLBACK_BASE
    assert tr.TINY_FACE_BASE == tr.ROLLBACK_BASE + "_sq1024_visurena"
    assert tr.WIDE_DETAIL_BASE == tr.ROLLBACK_BASE + "_wide15_visurena"
