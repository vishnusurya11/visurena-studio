"""Six of Crows exam hall, 2026-11-02: G-WHO's figure list on a crowded frame ran past its 512-token budget and was
cut off mid-JSON (char ~1580) on 16 of 18 takes, three asks each, so the who-check never judged them.  The panel
read had the same fault and was given 1024; the who read lists every figure too and needs no less."""
from scripts.episode import panel_content_check as pcc
from studio import figure_who as fw


def test_the_who_read_asks_for_at_least_the_panel_budget(monkeypatch, tmp_path):
    asked = {}

    def answer(name, values, readable):
        asked.update(values)
        return "[]"

    monkeypatch.setattr(pcc.comfy, "stage_image", lambda path: "staged.png")
    monkeypatch.setattr(pcc.comfy, "cached_text", answer)
    monkeypatch.setattr(fw, "parse", lambda said: [])
    pcc.read_who(tmp_path / "frame.png")
    assert asked["max_new_tokens"] >= pcc.TOKENS
