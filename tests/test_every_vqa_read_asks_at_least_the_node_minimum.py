"""Every Qwen3_VQA read asks for at least the node's max_new_tokens minimum (128).

ep12, 2026-09-24: the panel eye's size read asked for 64; ComfyUI refused the
workflow ("Value 64 smaller than min of 128") and step 08 died on every run.
The node's floor is fixed by ComfyUI, so any smaller ask is a crash, not a
shorter answer.
"""
from studio.judges import panel_eye

NODE_MIN = 128


def test_the_panel_eye_size_read_asks_at_least_the_node_minimum():
    sent = {}

    def run(name, values, timeout):
        sent.update(values)
        return '{"size": "wide", "pictures": 1}'

    panel_eye.size_read("x.png", run)
    assert sent["max_new_tokens"] >= NODE_MIN
