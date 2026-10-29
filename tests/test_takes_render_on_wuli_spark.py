"""The take model is routed by the planned shot size (main session 2026-10-18, on measured
evidence; owner 2026-10-17 liked Wuli V4's faces).

- close / medium_close / medium / insert (and extreme_close): Wuli 8-step HQ int8 -- about 2x
  face sharpness, equal warp on T19/T04 and the Kawajiri C/M cards;
- wide / full, a take with any wide or full segment, or a card with no sizes: the 8-step
  Singularity + turbo LoRA base -- Wuli's line work boils on a 4 % face
  (docs/audit/2026-10-18_warping/WARPING.md: T22 warp excess +2.4/+3.3 against about -0.6).

Both ran on Spark-H3 attention until ComfyUI 0.43 (owner 2026-10-29), which cannot load the Spark
kitchen; both now hold CK int8 attention, the same speed measured (the file keeps its old name).
The run queues each model's takes together, so each loads once (owner 2026-09-12, 2026-10-17).
Rollback: ROLLBACK_BASE for every take.
"""
from scripts.episode import takes_r2v

WULI = "video_minimax_h3_r2v_wuli8_hqint8_sandpies"
WIDE = "video_minimax_h3_r2v_turbo_ref8_crf_visurena_ckattn_comfyorg"


def test_the_two_take_models_are_pinned_by_name():
    assert takes_r2v.WULI_BASE == WULI
    assert takes_r2v.WIDE_BASE == WIDE == takes_r2v.ROLLBACK_BASE


def test_a_close_take_renders_on_wuli():
    assert takes_r2v.workflow_for({"lane": "dialogue", "sizes": ["close"]}) == WULI


def test_a_medium_close_take_renders_on_wuli():
    assert takes_r2v.workflow_for({"lane": "narration", "sizes": ["medium_close"]}) == WULI


def test_a_medium_take_renders_on_wuli():
    assert takes_r2v.workflow_for({"lane": "narration", "sizes": ["medium"]}) == WULI


def test_an_insert_renders_on_wuli():
    assert takes_r2v.workflow_for({"lane": "narration", "sizes": ["insert", "extreme_close"]}) == WULI


def test_a_wide_take_renders_on_the_wide_model():
    assert takes_r2v.workflow_for({"lane": "narration", "sizes": ["wide"]}) == WIDE


def test_a_full_take_renders_on_the_wide_model():
    assert takes_r2v.workflow_for({"lane": "dialogue", "sizes": ["full"]}) == WIDE


def test_a_take_with_one_wide_segment_renders_on_the_wide_model():
    assert takes_r2v.workflow_for({"lane": "narration", "sizes": ["medium", "wide"]}) == WIDE


def test_a_card_without_sizes_renders_on_the_wide_model():
    assert takes_r2v.workflow_for({"lane": "narration"}) == WIDE


def test_wuli_is_wuli_with_ck_attention_and_no_turbo_lora():
    from studio.comfy import load_workflow
    graph, _ = load_workflow(WULI)
    assert graph["1"]["inputs"]["unet_name"].startswith("wuli_h3_turbo_8step")
    assert graph["attn"] == {"class_type": "ModelAttentionBackend",
                             "inputs": {"model": ["3", 0], "attention": "comfy kitchen attention"}}
    assert not [k for k, n in graph.items() if n["class_type"] == "LoraLoaderModelOnly"]


def test_each_model_s_takes_are_queued_together():
    jobs = [({"index": 1, "sizes": ["wide"]}, {}), ({"index": 2, "sizes": ["close"]}, {}),
            ({"index": 3, "sizes": ["full"]}, {}), ({"index": 4, "sizes": ["medium"]}, {})]
    assert [c["index"] for c, _ in takes_r2v.by_model(jobs)] == [2, 4, 1, 3]


def test_the_card_names_the_graph_it_renders_on():
    assert takes_r2v.card_workflow({"lane": "narration", "sizes": ["wide"]}) == WIDE + " + anchors"
    assert takes_r2v.MODELS[WULI].startswith("MiniMax-H3 ref2va, Wuli 8-step HQ int8")
