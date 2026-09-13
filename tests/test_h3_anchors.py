"""Anchors are added to a ComfyUI graph as a chain of MiniMaxH3AddGuide nodes."""
import copy

from studio import h3_anchors as ha

GRAPH = {
    "6": {"class_type": "VAELoader", "inputs": {}},
    "7": {"class_type": "VAELoader", "inputs": {}},
    "8": {"class_type": "MiniMaxH3ReferenceToVideo", "inputs": {"prompt": "x"}},
    "10": {"class_type": "BasicGuider", "inputs": {"conditioning": ["8", 0]}},
    "13": {"class_type": "SamplerCustomAdvanced", "inputs": {"latent_image": ["8", 1]}},
}


def test_each_image_anchor_becomes_a_loader_and_a_guide_in_a_chain():
    g = ha.anchored(copy.deepcopy(GRAPH), [("S00.png", 0), ("S01.png", 72)], audio=None)
    guides = [n for n in g.values() if n["class_type"] == "MiniMaxH3AddGuide"]
    loaders = [n for n in g.values() if n["class_type"] == "LoadImage"]
    assert len(guides) == 2 and len(loaders) == 2
    assert [n["inputs"]["frame_idx"] for n in guides] == [0, 72]
    first, second = guides
    assert first["inputs"]["positive"] == ["8", 0]
    assert second["inputs"]["positive"][0] != "8"          # chained on the first guide
    assert g["10"]["inputs"]["conditioning"][0] != "8"     # the guider reads the last guide


def test_the_audio_anchor_closes_the_chain():
    g = ha.anchored(copy.deepcopy(GRAPH), [("S00.png", 0)], audio=("l00.wav", 6))
    last = g[g["10"]["inputs"]["conditioning"][0]]
    assert last["class_type"] == "MiniMaxH3AddGuide"
    assert last["inputs"]["frame_idx"] == 6 and "audio" in last["inputs"]
    assert g[last["inputs"]["audio"][0]]["class_type"] == "LoadAudio"


def test_the_latent_still_comes_from_the_base_node():
    g = ha.anchored(copy.deepcopy(GRAPH), [("S00.png", 0)], audio=None)
    assert g["13"]["inputs"]["latent_image"] == ["8", 1]
    for n in g.values():
        if n["class_type"] == "MiniMaxH3AddGuide":
            assert n["inputs"]["latent"] == ["8", 1]
