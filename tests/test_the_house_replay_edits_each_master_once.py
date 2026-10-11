"""The house replay (GPU, prepared): each case is ONE edit of its place's master,
written only under --out, with a master | variant | shipped strip."""
from __future__ import annotations

from PIL import Image

from scripts.refs import place_replay


def test_each_case_edits_its_master_once_into_the_out_folder(tmp_path):
    book, out, calls = tmp_path / "book", tmp_path / "out", []
    for loc in ("narrators_home", "narrators_study"):
        (book / "refs" / "locations" / loc).mkdir(parents=True)
        for v in ("wide_establishing", "reverse"):
            Image.new("RGB", (16, 8)).save(book / "refs" / "locations" / loc / f"{v}.png")
    out.mkdir()

    def edit(prompt, source, target):
        calls.append((source.name, prompt))
        Image.new("RGB", (16, 8)).save(target)
    made = place_replay.run_case(book, "ep26_villa_abandoned", out, edit)
    assert made.parent == out and calls == [("wide_establishing.png", calls[0][1])]
    assert "Change only: the front door stands forced open" in calls[0][1]
    assert (out / "ep26_villa_abandoned_strip.png").exists()
