"""Phase-0 bench (2026-10-10): an arm is the shipped RAN graph with the arm workflow's
model, LoRA, step, attention and save nodes laid over it, and its knobs are read back
from the graph that will be submitted -- a fix that changes nothing is caught here."""
import pytest

from scripts.bench import h3_arms as arms


def shipped() -> dict:
    return {
        "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "sing.safetensors"}},
        "2": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["1", 0], "lora_name": "l8", "strength_model": 1.0}},
        "lora_second": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["2", 0], "lora_name": "l8", "strength_model": 0.7}},
        "3": {"class_type": "PathchSageAttentionKJ", "inputs": {"model": ["lora_second", 0], "sage_attention": "disabled"}},
        "4": {"class_type": "MiniMaxH3SigmaShift", "inputs": {"model": ["3", 0], "shift_video": 12, "shift_audio": 3.0}},
        "8": {"class_type": "MiniMaxH3ReferenceToVideo", "inputs": {"length": 107, "prompt": "p"}},
        "9": {"class_type": "BasicScheduler", "inputs": {"model": ["4", 0], "steps": 8}},
        "12": {"class_type": "RandomNoise", "inputs": {"noise_seed": 105012}},
        "17": {"class_type": "SaveVideo", "inputs": {"filename_prefix": "ep_take_12", "format": "auto", "codec": "auto"}},
        "22": {"class_type": "MiniMaxH3AddGuide", "inputs": {"frame_idx": 0}},
    }


def four_step_arm() -> dict:
    g = shipped()
    g.pop("lora_second")
    g["2"]["inputs"]["lora_name"] = "l4"
    g["3"]["inputs"]["model"] = ["2", 0]
    g["9"]["inputs"]["steps"] = 4
    g["17"]["inputs"] = {"filename_prefix": "x", "format": "mp4", "format.codec": "h264",
                         "format.codec.encoding": "re-encode", "format.codec.encoding.crf": 10.0}
    return g


def test_the_arm_replaces_the_lora_stack_and_steps_and_keeps_the_shot():
    out = arms.arm_graph(shipped(), four_step_arm(), prefix="bench_x")
    k = arms.knobs(out)
    assert k["loras"] == [("l4", 1.0)]
    assert k["steps"] == 4 and k["crf"] == 10.0 and k["seed"] == 105012 and k["frames"] == 107
    assert out["22"] == shipped()["22"]


def test_a_second_seed_is_set_on_the_noise_node():
    out = arms.arm_graph(shipped(), four_step_arm(), prefix="bench_x", seed=7)
    assert arms.knobs(out)["seed"] == 7


def test_the_two_lora_chain_is_read_in_order():
    k = arms.knobs(shipped())
    assert k["loras"] == [("l8", 1.0), ("l8", 0.7)] and k["crf"] is None


def test_a_graph_whose_knobs_differ_from_the_claim_is_refused():
    with pytest.raises(AssertionError):
        arms.assert_knobs(arms.knobs(shipped()), {"steps": 4})
