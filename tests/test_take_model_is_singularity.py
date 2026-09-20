"""The episode's take workflow runs the Singularity fine-tune, with the turbo
LoRA stacked twice (1.0 then 0.7), as measured on WotW ep03."""
import json
from pathlib import Path

WORKFLOW = Path("D:/Projects/KingdomOfViSuReNa/alpha/comfy_studio/workflows/video"
                "/video_minimax_h3_r2v_turbo_ref8.json")
MODEL = "Minimax-h3_Singularity_ref2va_Pruned_v1.3_int8.safetensors"


def _graph() -> dict:
    return json.loads(WORKFLOW.read_text(encoding="utf-8"))


def test_the_take_workflow_loads_the_singularity_model():
    unet = [v for v in _graph().values() if v["class_type"] == "UNETLoader"]
    assert [n["inputs"]["unet_name"] for n in unet] == [MODEL]


def test_the_turbo_lora_is_stacked_twice_at_one_then_zero_seven():
    loras = [v for v in _graph().values() if v["class_type"] == "LoraLoaderModelOnly"]
    assert sorted(n["inputs"]["strength_model"] for n in loras) == [0.7, 1.0]
    assert len({n["inputs"]["lora_name"] for n in loras}) == 1


def test_the_second_lora_takes_the_first_ones_model():
    g = _graph()
    loras = {k: v for k, v in g.items() if v["class_type"] == "LoraLoaderModelOnly"}
    second = next(k for k, v in loras.items() if v["inputs"]["strength_model"] == 0.7)
    assert g[second]["inputs"]["model"][0] in loras
