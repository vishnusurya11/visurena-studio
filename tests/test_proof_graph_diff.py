"""The brick's test (2026-10-21_ep02_proof DESIGN 0, R1): a take graph S0a builds is diffed field by
field against the recorded graph of the SAME index and try count, and every difference is explained
by a commit that touched the field's literal in the take code, or by the try count; what is left is
the regression measure, unexplained differences over n takes, each listed with its field."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from studio.rehearsal import graph_diff as gd


def graph(seed=82102, strength=0.7, prompt="Mr. Utterson stands at the LEFT third.", frames=141):
    return {"1": {"class_type": "UNETLoader", "inputs": {"unet_name": "h3.safetensors"}},
            "lora_second": {"class_type": "LoraLoaderModelOnly",
                            "inputs": {"model": ["1", 0], "lora_name": "turbo.safetensors", "strength_model": strength}},
            "8": {"class_type": "MiniMaxH3ReferenceToVideo",
                  "inputs": {"clip": ["5", 0], "prompt": prompt, "length": frames}},
            "12": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed}},
            "scaled_to": [768, 768]}


def no_git(*args):
    return ""


def test_fields_keep_literals_and_the_class_set_and_drop_links():
    fields = gd.fields_of(graph())
    assert fields["12.RandomNoise.noise_seed"] == 82102
    assert fields["lora_second.LoraLoaderModelOnly.strength_model"] == 0.7
    assert "lora_second.LoraLoaderModelOnly.model" not in fields       # a link is wiring, not a field
    assert fields["classes"] == sorted(["UNETLoader", "LoraLoaderModelOnly", "MiniMaxH3ReferenceToVideo", "RandomNoise"])
    assert not any(k.startswith("scaled_to") for k in fields)


def test_the_diff_names_only_the_fields_that_changed():
    found = gd.diff(gd.fields_of(graph()), gd.fields_of(graph(strength=0.6)))
    assert found == [{"field": "lora_second.LoraLoaderModelOnly.strength_model", "old": 0.7, "new": 0.6}]


def test_the_recorded_graph_of_the_same_try_comes_from_attempts_or_the_kept_take(tmp_path):
    room = tmp_path / "r2v"
    (room / "attempts").mkdir(parents=True)
    for name in ("T02.graph.json", "attempts/T02_fail1.graph.json", "attempts/T02_fail2.graph.json"):
        (room / name).write_text("{}")
    assert gd.recorded_for(room, 2, tries=0, kept_tries=2) == (room / "attempts" / "T02_fail1.graph.json", 0)
    assert gd.recorded_for(room, 2, tries=1, kept_tries=2) == (room / "attempts" / "T02_fail2.graph.json", 1)
    assert gd.recorded_for(room, 2, tries=2, kept_tries=2) == (room / "T02.graph.json", 2)
    assert gd.recorded_for(room, 2, tries=5, kept_tries=2) == (room / "T02.graph.json", 2)    # nearest: the kept one
    assert gd.recorded_for(room, 9, tries=0, kept_tries=0) == (None, None)


def test_a_seed_moved_by_101_per_try_is_explained_by_the_try_count():
    d = {"field": "12.RandomNoise.noise_seed", "old": 82102, "new": 82304}
    assert gd.attribute(d, "2026-10-13", (0, 2), no_git)["by"] == "tries"
    assert gd.attribute(d, "2026-10-13", (1, 1), no_git)["by"] is None             # same try: tries explain nothing


def test_a_prompt_phrase_a_commit_introduced_is_explained_by_that_commit():
    seen = []

    def git(*args):
        seen.append(args)
        return "abc1234\n" if "-Sthe RIGHT" in args else ""
    old, new = graph(prompt="Mr. Utterson stands at the LEFT third."), graph(prompt="Mr. Utterson stands at the RIGHT third.")
    row = gd.attribute(gd.diff(gd.fields_of(old), gd.fields_of(new))[0], "2026-10-13", (0, 0), git)
    assert row["by"] == "commit" and row["commits"] == ["abc1234"]
    assert all(a[0] == "log" and "--" in a and "scripts/episode/takes_r2v.py" in a for a in seen)   # read-only, take code


def test_a_number_or_a_boolean_is_searched_only_on_a_line_that_names_its_field():
    terms = gd.terms("9.KSampler.steps", 8, 6)
    assert all(flag == "-G" for flag, _ in terms)
    assert "[sS][tT][eE][pP][sS]" in terms[0][1] and "[kK][sS][aA]" in terms[0][1]
    assert not any(flag == "-S" for flag, _ in gd.terms("40.LoadImage.upload", True, False))
    assert gd.terms("12.RandomNoise.noise_seed", 82102, None)[0][0] == "-G"
    assert gd.terms("[0]", 7, 8) == []                     # a field with no name: nothing can explain it


def test_a_short_string_is_bound_to_its_field_and_a_long_phrase_is_searched_alone():
    assert gd.terms("3.CLIPTextEncode.mode", "fast", "slow")[0][0] == "-G"
    flag, text = gd.terms("8.X.prompt", "stands at the LEFT third", "stands at the RIGHT third")[0]
    assert flag == "-S" and "RIGHT" in text


def test_the_take_report_lists_each_unexplained_field_and_the_summary_counts_over_n():
    built = graph(seed=82102, strength=0.6)
    one = gd.take_report(1, graph(), built, "2026-10-13", (1, 1), no_git)
    two = gd.take_report(2, graph(), graph(), "2026-10-13", (0, 0), no_git)
    assert one["unexplained"] == ["lora_second.LoraLoaderModelOnly.strength_model"]
    assert two["unexplained"] == []
    total = gd.summary([one, two])
    assert total["n"] == 2 and total["unexplained"] == 1
    assert total["listed"] == [{"index": 1, "field": "lora_second.LoraLoaderModelOnly.strength_model"}]


def test_a_document_is_flattened_to_paths_so_shots_and_prompts_diff_the_same_way():
    flat = gd.flatten([{"index": 0, "seed": 7, "refs": ["a.png"]}])
    assert flat == {"[0].index": 0, "[0].seed": 7, "[0].refs[0]": "a.png"}
    found = gd.doc_report("shots.json", [{"seed": 7}], [{"seed": 8}], "2026-10-13", no_git)
    assert found["unexplained"] == ["[0].seed"]


def test_a_real_commit_in_a_repo_explains_its_literal(tmp_path):
    repo = tmp_path / "repo"
    code = repo / "scripts" / "episode" / "takes_r2v.py"
    code.parent.mkdir(parents=True)
    ident = ["-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false"]
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    code.write_text("LORA_SECOND = 0.7\n")
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repo), *ident, "commit", "-qm", "first"], check=True)
    code.write_text("LORA_SECOND = 0.65\n")
    subprocess.run(["git", "-C", str(repo), *ident, "commit", "-qam", "turbo second pass 0.65"], check=True)
    d = {"field": "lora_second.LoraLoaderModelOnly.strength_model", "old": 0.7, "new": 0.65}
    row = gd.attribute(d, "2000-01-01", (0, 0), gd.repo_git(repo))
    assert row["by"] == "commit" and len(row["commits"]) == 1


def test_a_recorded_take_room_reports_every_built_take(tmp_path):
    room = tmp_path / "r2v"
    room.mkdir()
    (room / "T01.graph.json").write_text(json.dumps(graph()))
    (room / "shots.json").write_text(json.dumps([{"index": 1, "tries": 1}]))
    reports = gd.room_report(room, {1: (graph(strength=0.6), 1)}, "2026-10-13", no_git)
    assert [r["index"] for r in reports] == [1]
    assert reports[0]["unexplained"] == ["lora_second.LoraLoaderModelOnly.strength_model"]
    missing = gd.room_report(room, {7: (graph(), 0)}, "2026-10-13", no_git)
    assert missing[0]["unexplained"] == ["<no recorded graph>"]


def commit_in(repo: Path, rel: str, text: str, message: str) -> None:
    ident = ["-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false"]
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    subprocess.run(["git", "-C", str(repo), "add", rel], check=True)
    subprocess.run(["git", "-C", str(repo), *ident, "commit", "-qm", message], check=True)


@pytest.fixture
def take_repo(tmp_path):
    repo = tmp_path / "repo"
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    commit_in(repo, "studio/take_ladder.py", lines("RETRIES = 1", "FLAG = False", "SIZE = 8", "PAD = 768"), "first")
    commit_in(repo, "studio/take_ladder.py", lines("RETRIES = 2", "FLAG = True", "SIZE = 6", "PAD = 1024"),
              "unrelated literals")
    return repo


def lines(*rows: str) -> str:
    return "".join(f"{r}\n" for r in rows)


@pytest.mark.parametrize("field,old,new", [("12.KSampler.cfg", 1, 2), ("40.LoadImage.upload", True, False),
                                           ("7.EmptyLatent.width", 768, 1024), ("9.Foo.steps", 8, 6)])
def test_a_commit_that_moved_the_literal_but_never_names_the_field_explains_nothing(take_repo, field, old, new):
    row = gd.attribute({"field": field, "old": old, "new": new}, "2000-01-01", (0, 0), gd.repo_git(take_repo))
    assert row["by"] is None, row


def test_a_commit_whose_line_names_the_field_with_the_literal_explains_it(take_repo):
    commit_in(take_repo, "scripts/episode/takes_r2v.py", lines("graph['12']['inputs']['cfg'] = 2", "upload=False"), "cfg 2")
    git = gd.repo_git(take_repo)
    assert gd.attribute({"field": "12.KSampler.cfg", "old": 1, "new": 2}, "2000-01-01", (0, 0), git)["by"] == "commit"
    assert gd.attribute({"field": "40.LoadImage.upload", "old": True, "new": False}, "2000-01-01", (0, 0), git)["by"] == "commit"
    assert gd.attribute({"field": "7.EmptyLatent.width", "old": 768, "new": 1024}, "2000-01-01", (0, 0), git)["by"] is None
