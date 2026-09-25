"""A harvested candidate nobody confirmed weighs nothing and never loads.

`harvest_labels` emits every prose hit as `verdict_by: unverified`; until a
person (or an agent, then `agent`) opens the artefact and confirms it, the row
stays out of every metric.  `load` drops it; `weight` gives it zero.
"""
import json

from studio import casebook


def row(**over):
    base = dict(codex="00000000000000", unit="ep02", kind="take", path="episodes/ep02/takes/r2v/T05.mp4",
                sha8="0badcafe", verdict="fault", fault_class="lettering", verdict_by="unverified",
                verdict_at="2026-09-23", source="episodes/ep02/story.md#L5")
    return casebook.Row(**(base | over))


def write_labels(folder, rows):
    folder.mkdir(parents=True, exist_ok=True)
    (folder / casebook.LABELS).write_text("".join(json.dumps(r.model_dump()) + "\n" for r in rows), encoding="utf-8")


def test_an_unverified_row_weighs_nothing():
    assert casebook.weight(row()) == 0.0
    assert not casebook.counted(row())


def test_load_drops_the_unverified_row(tmp_path):
    kept = row(path="episodes/ep02/takes/r2v/T06.mp4", verdict="pass", fault_class=None, verdict_by="default")
    write_labels(tmp_path, [row(), kept])
    loaded = casebook.load(tmp_path)
    assert [r.path for r in loaded] == [kept.path]


def test_load_reads_nothing_from_an_empty_folder(tmp_path):
    assert casebook.load(tmp_path / "nowhere") == []
