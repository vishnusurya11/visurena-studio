"""The render plan: every style x subject x model, grouped by model (each model loads once),
each job naming its workflow values and a relative output; a re-run plans only the missing."""
from __future__ import annotations

from prism.plan import Job, jobs, out_path, pending, read_plan, write_plan
from tests.prism_fixtures import guide, style, subjects


def plan():
    guides = {"krea2": guide("krea2"), "flux3_klein": guide("flux3_klein")}
    return jobs([style(), style("anime_b", "B")], subjects(), guides)


def test_every_style_subject_and_model_is_one_job():
    assert len(plan()) == 2 * 5 * 2


def test_jobs_are_grouped_by_model_so_each_loads_once():
    models = [j.model for j in plan()]
    assert models == ["krea2"] * 10 + ["flux3_klein"] * 10


def test_a_job_carries_the_prompt_the_seed_and_the_guides_values():
    job = plan()[0]
    assert job.values["prompt"] == job.prompt and job.values["seed"] == 1000
    assert job.values["width"] == 1024 and job.workflow == "image_krea2_t2i"
    assert job.values["filename_prefix"] == "prism/anime_hellsing_gothic/count__krea2"


def test_one_subject_holds_one_seed_across_styles_and_models():
    seeds = {j.values["seed"] for j in plan() if j.subject == "chase"}
    assert seeds == {1004}


def test_an_own_words_model_plans_only_the_styles_it_has_words_for():
    from prism.catalog import ModelWords
    held = style(models={"v2": ModelWords(style="Own.", recap="Own.")})
    planned = jobs([held, style("anime_b", "B")], subjects(), {"v2": guide("v2", own_words_only=True)})
    assert {j.style for j in planned} == {"anime_hellsing_gothic"} and len(planned) == 5


def test_outputs_are_relative():
    assert out_path("anime_a", "count", "krea2") == "renders/anime_a/count__krea2.png"


def test_a_rendered_job_is_not_planned_again(tmp_path):
    done = plan()[0]
    (tmp_path / done.out).parent.mkdir(parents=True)
    (tmp_path / done.out).write_bytes(b"png")
    assert done not in pending(plan(), tmp_path) and len(pending(plan(), tmp_path)) == 19


def test_the_plan_file_round_trips(tmp_path):
    write_plan(plan(), tmp_path / "plan.json")
    assert read_plan(tmp_path / "plan.json") == plan()
    assert isinstance(read_plan(tmp_path / "plan.json")[0], Job)
