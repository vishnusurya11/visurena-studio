"""Builders for the publish lane's tests: a tmp book with a delivered cut,
judged takes and a judge-filled eye rubric -- everything MEASURED on disk,
nothing rendered, nothing networked (house rule: no test spends anything).

The shapes mirror the real artifacts: source/book.json carries the series
fields `series_of` refuses without; qc_<engine>.json carries the sha8 of the
master's own bytes; every take has a dq and a content verdict naming its
take_sha8, so `judged.unjudged_takes` stays empty; the eye rubric answers all
five fields in the judge's pen the way `eye_review.refusals` demands.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

from scripts.episode import eye_review
from studio import episode_home, standing_approval
from studio import youtube_publish as yp
from studio.learnings import Learning, record

PLAN = {
    "number": 1, "title": "The Red Weed",
    "lines": [
        {"index": 0, "kind": "narration", "speaker": "narrator",
         "text": "I walk the Horsell common at dawn."},
        {"index": 1, "kind": "dialogue", "speaker": "ogilvy",
         "text": "Stay back from the pit, Ogilvy."},
    ],
    "shots": [
        {"index": 0, "size": "wide",
         "frame": "The narrator stands on Horsell common.",
         "motion": "The camera pushes in."},
    ],
}


class FakeCaller:
    """Scriptable structured caller: pops its answers, repeats the last one."""

    def __init__(self, answers):
        self.answers, self.prompts = list(answers), []

    def __call__(self, prompt, structured_output_model=None):
        self.prompts.append(prompt)
        obj = self.answers.pop(0) if len(self.answers) > 1 else self.answers[0]
        return SimpleNamespace(structured_output=obj)


class FakeCtx:
    """What step 13 reads off a context; run_script raises because the step
    must never shell out (guard_spend lives in THIS process)."""

    def __init__(self, book: Path, home: Path, number: int):
        self.book_dir, self.home, self.number = book, home, number
        self.book_id, self.unit = book.name, f"ep{number:02d}"

    def log(self, *args, **kwargs):
        pass

    def run_script(self, *args, **kwargs):
        raise AssertionError("step 13 must never shell out; everything runs in-process")


def book_with(root: Path, name: str = "20990101010101_test-book", **said) -> Path:
    """A tmp book whose source/book.json names its series fields."""
    book = root / name
    (book / "source").mkdir(parents=True, exist_ok=True)
    doc = {"title": "the test book", "author": "A. B. Author", "series": "A. B. Author",
           "display_title": "The Test Book", "episodes": 9, **said}
    (book / "source" / "book.json").write_text(
        json.dumps({k: v for k, v in doc.items() if v is not None}), encoding="utf-8")
    return book


def takes(home: Path, engine: str = "r2v", indices: tuple[int, ...] = (0, 1)) -> Path:
    """A takes room where every recorded take carries both current verdicts."""
    folder = episode_home.takes_under(home, engine)
    folder.mkdir(parents=True, exist_ok=True)
    episode_home.write_json(folder / "shots.json", [{"index": i} for i in indices])
    for i in indices:
        take = folder / f"T{i:02d}.mp4"
        take.write_bytes(b"take %d" % i)
        digest = hashlib.sha256(take.read_bytes()).hexdigest()[:8]
        episode_home.write_json(folder / f"T{i:02d}.dq.json",
                                {"passed": True, "score": 88.0, "take_sha8": digest})
        episode_home.write_json(folder / f"T{i:02d}.content.json",
                                {"passed": True, "take_sha8": digest})
    return folder


def rubric(home: Path, sha8: str) -> Path:
    """The eye rubric for this cut, every field answered in the judge's pen."""
    doc = eye_review.blank_rubric(sha8, "master_r2v.mp4", f"contact_{sha8}.png", 5.0, 24)
    for field in doc["rubric"]:
        doc["rubric"][field].update(answer="y", evidence={"measure": 1.0})
    doc.update(notes="measured clean", reviewed_by="judge:master_eye@1",
               reviewed_at="2026-10-05T00:00:00Z")
    return episode_home.write_json(eye_review.rubric_path(home, sha8), doc)


def episode_with(book: Path, number: int = 1, plan: dict = PLAN,
                 engine: str = "r2v") -> tuple[Path, str]:
    """A delivered cut with judged takes and a filled rubric: (home, sha8)."""
    home = episode_home.home(book, number)
    episode_home.write_json(home / "plan.json", {**plan, "number": number})
    (home / "cut").mkdir(parents=True, exist_ok=True)
    master = home / "cut" / f"master_{engine}.mp4"
    master.write_bytes(b"the finished master")
    sha8 = yp.sha8(master)
    episode_home.write_json(home / f"qc_{engine}.json",
                            {"passed": True, "sha8": sha8, "seconds": 120.5,
                             "planned_seconds": 118.0, "lufs": -14.2, "true_peak": -1.3,
                             "longest_gap_s": 4.7})
    takes(home, engine)
    rubric(home, sha8)
    episode_home.write_json(home / "review" / "speaker_check.json",
                            {"narrator": {"ok": True, "worst": 0.31}})
    record(home / "learnings.jsonl", Learning(step="09", gate="TAKE", action="pass"))
    return home, sha8


def publish_seeded(book: Path) -> None:
    """The one-time per-book publish artifacts metadata.py reads."""
    room = book / "publish"
    room.mkdir(parents=True, exist_ok=True)
    (room / "footer.txt").write_text("— The Test Lantern —\nEvery episode is one whole chapter.",
                                     encoding="utf-8")
    (room / "pipeline_note.txt").write_text("Local models end to end.", encoding="utf-8")


def prior_with(book: Path, number: int, *, description: str = "A prior episode.",
               tags: tuple[str, ...] = ("the test book", "serial")) -> Path:
    """A prior episode's youtube.json, the few-shot voice metadata.py learns from."""
    return episode_home.write_json(
        book / "episodes" / f"ep{number:02d}" / "youtube.json",
        {"title": f"Prior {number}", "description": description, "tags": list(tags),
         "privacy": "private", "synthetic": True, "_synthetic_note": "Local models. Cut 0badbeef: QC passed."})


def standing(book: Path, decision: str = standing_approval.DECISION, by: str = "owner") -> Path:
    """The owner's standing publish approval, as the owner would write it once."""
    return episode_home.write_json(book / "publish" / "standing.json",
                                   {"kind": "publish", "decision": decision,
                                    "by": by, "at": "2026-10-05"})
