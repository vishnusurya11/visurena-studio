"""CK int8 attention is adopted for NARRATION takes (C1 bench block 3, 2026-10-11).

Measured on the 8-step BASE against its own seed-1 renders: same draw (PSNR
22.9-33.9 dB against the seed-to-seed 13.1-22.2), identity within -2 sigma_seed
on every shot (worst S4 -0.030, floor -0.042; dialogue mean -0.005), banding and
clones unchanged, no invented word on S4 x 2 seeds, sampling 39-45 % faster.
Dialogue stays on BASE until D1 and D2 also pass on a second seed (GATES arm rule).
"""
from scripts.episode import takes_r2v


def test_a_narration_take_renders_on_the_ck_arm():
    assert takes_r2v.workflow_for({"lane": "narration"}) == takes_r2v.NARRATION_BASE
    assert takes_r2v.NARRATION_BASE == takes_r2v.BASE + "_ckattn_comfyorg"


def test_a_dialogue_take_stays_on_base():
    assert takes_r2v.workflow_for({"lane": "dialogue"}) == takes_r2v.BASE


def test_the_ck_arm_differs_from_base_only_by_the_attention_node():
    from studio.comfy import load_workflow
    base, _ = load_workflow(takes_r2v.BASE)
    ck, _ = load_workflow(takes_r2v.NARRATION_BASE)
    assert ck["attn"]["inputs"]["attention"] == "comfy kitchen attention"
    assert ck["4"]["inputs"]["model"] == ["attn", 0]
    rest = {k: v for k, v in ck.items() if k not in ("attn", "4", "17")}
    assert rest == {k: v for k, v in base.items() if k not in ("4", "17")}
