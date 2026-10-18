"""The render plan: style x subject x model jobs, grouped by model, outputs relative to the run root."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from prism.catalog import ModelGuide, Style, Subject, SubjectSet
from prism.compose import compose


@dataclass(frozen=True)
class Job:
    style: str
    subject: str
    model: str
    workflow: str
    prompt: str
    out: str
    values: dict = field(hash=False, default_factory=dict)


def out_path(style_id: str, subject_id: str, model_id: str) -> str:
    return f"renders/{style_id}/{subject_id}__{model_id}.png"


def job_for(style: Style, subject: Subject, guide: ModelGuide) -> Job:
    prompt = compose(style, guide, subject)
    values = {**guide.values, guide.prompt_key: prompt, guide.seed_key: subject.seed,
              guide.prefix_key: f"prism/{style.id}/{subject.id}__{guide.id}"}
    return Job(style.id, subject.id, guide.id, guide.workflow, prompt,
               out_path(style.id, subject.id, guide.id), values)


def jobs(styles: list[Style], subjects: SubjectSet, guides: dict[str, ModelGuide]) -> list[Job]:
    """Model-major: every job of one model before the next model loads."""
    return [job_for(s, subject, g) for g in guides.values() for s in styles for subject in subjects.subjects
            if planned_for(s, subject, g)]


def planned_for(style: Style, subject: Subject, guide: ModelGuide) -> bool:
    own = style.models.get(guide.id)
    if guide.own_words_only and not own:
        return False
    return not guide.captions_only or bool(own and subject.id in own.captions)


def pending(planned: list[Job], root: Path) -> list[Job]:
    return [j for j in planned if not (Path(root) / j.out).exists()]


def write_plan(planned: list[Job], path: Path) -> None:
    Path(path).write_text(json.dumps([asdict(j) for j in planned], indent=1, ensure_ascii=False), encoding="utf-8")


def read_plan(path: Path) -> list[Job]:
    return [Job(**row) for row in json.loads(Path(path).read_text(encoding="utf-8"))]
