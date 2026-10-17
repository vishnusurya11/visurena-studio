"""The Qwen3-TTS clone renders on a NEW graph (2026-10-17).

TTS Audio Suite's CharacterVoicesNode now requires `customized`, `trim_start`
and `trim_end`; the shipped `audio_qwen3tts_clone` lacks them and ComfyUI
answers 400 at submit (2026-10-16 battery part 2). Existing workflows are never
edited (owner 2026-10-10), so the clone moved to a copy that carries them at the
node's defaults: no trim, no override."""
from studio import comfy, voice

OLD = "audio_qwen3tts_clone"


def voices_node(graph: dict) -> dict:
    return next(n["inputs"] for n in graph.values() if n.get("class_type") == "CharacterVoicesNode")


def test_the_clone_uses_the_new_graph():
    assert voice.CLONE_WORKFLOW == "audio_qwen3tts_clone_ttsaudiosuite"


def test_the_new_graph_carries_the_three_required_inputs_at_their_defaults():
    graph, _ = comfy.load_workflow(voice.CLONE_WORKFLOW)
    node = voices_node(graph)
    assert (node["customized"], node["trim_start"], node["trim_end"]) == (False, 0.0, 0.0)


def test_the_new_graph_is_the_old_one_plus_only_those_inputs():
    new, new_inject = comfy.load_workflow(voice.CLONE_WORKFLOW)
    old, old_inject = comfy.load_workflow(OLD)
    for key in ("customized", "trim_start", "trim_end"):
        voices_node(new).pop(key)
    assert new == old
    assert new_inject == old_inject
