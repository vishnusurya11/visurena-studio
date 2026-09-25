"""An owner's word outweighs an agent's, which outweighs a publish-by-default.

Weights: owner 1, agent 0.75, default 0.5; synthetic and unverified 0 (their
own column, or not counted).  When the owner writes a row for a path the
harvest labelled `default`, `load` keeps the owner's row and drops the default.
"""
import json

from studio import casebook


def row(**over):
    base = dict(codex="00000000000000", unit="ep02", kind="take", path="episodes/ep02/takes/r2v/T05.mp4",
                sha8="0badcafe", verdict="pass", fault_class=None, verdict_by="default",
                verdict_at="2026-09-23", source="episodes/ep02/takes/r2v/T05.dq.json")
    return casebook.Row(**(base | over))


def jsonl(folder, name, rows):
    folder.mkdir(parents=True, exist_ok=True)
    (folder / name).write_text("".join(json.dumps(r.model_dump()) + "\n" for r in rows), encoding="utf-8")


def test_the_weights_rank_owner_agent_default():
    w = [casebook.weight(row(verdict_by=who)) for who in ("owner", "agent", "default")]
    assert w == [1.0, 0.75, 0.5]
    assert casebook.weight(row(verdict_by="synthetic")) == 0.0


def test_an_owner_row_shadows_the_default_row_on_its_path(tmp_path):
    other = row(path="episodes/ep02/takes/r2v/T06.mp4")
    owner = row(verdict="fault", fault_class="anchored_slide", verdict_by="owner", source="owner.jsonl")
    jsonl(tmp_path, casebook.LABELS, [row(), other])
    jsonl(tmp_path, casebook.OWNER, [owner])
    loaded = casebook.load(tmp_path)
    by_path = {r.path: r for r in loaded}
    assert len(loaded) == 2
    assert by_path[owner.path].verdict_by == "owner"
    assert by_path[other.path].verdict_by == "default"
