"""Step 10 -- deliver: the manifest, then the Telegram send.

The manifest is what the retrospect reads: every rung the run took and
every number it measured, in one file beside the master, written BEFORE
the send so a dead network still leaves a complete record.  The send is
a subprocess to the studio's existing notifier and climbs x3; after that
the file stays in the library and the manifest says `undelivered`.  The
step never publishes -- the orchestrator does.
"""
from __future__ import annotations

import json
import os
import subprocess
from collections import Counter
from pathlib import Path

from studio import db
from studio.ladder import Ladder, Rung, climb
from studio.learnings import load
from studio.trailer_stage_spec import QCReport

STEP_ID = "10"
NAME = "deliver"
NOTIFIER = Path(os.environ.get(
    "TRAILER_NOTIFIER",
    "D:/Projects/KingdomOfViSuReNa/alpha/comfy_studio/poc/2026-08-25_2k-video-pipeline/"
    "scripts/notify_bench.py"))
LADDER = Ladder([Rung("send", cost_seconds=30, tries=3)], terminal="undelivered")
TELEGRAM_LIMIT = 50 * 1024 * 1024
"""The Bot API's upload cap.  A master 45 KB over it died three times with a
TLS EOF and no other word (Scarlet run 6b); the library keeps the master
and Telegram gets a copy that fits."""
SHRINK_CRF = 20


def shrink(master: Path, dest: Path) -> Path:
    """A smaller re-encode of the master for the send, audio untouched."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(master), "-c:v", "libx264",
                    "-preset", "medium", "-crf", str(SHRINK_CRF), "-c:a", "copy",
                    "-movflags", "+faststart", str(dest)], check=True)
    return dest


def deliverable(master: Path, work: Path) -> Path:
    """The master itself when it fits the Bot API, else a shrunk copy."""
    if master.stat().st_size <= TELEGRAM_LIMIT:
        return master
    return shrink(master, work / "telegram.mp4")


def qc_of(ctx) -> QCReport | None:
    path = ctx.out_dir / "qc.json"
    return QCReport.model_validate_json(path.read_text(encoding="utf-8")) if path.exists() else None


def master_of(ctx) -> Path:
    found = sorted(ctx.out_dir.glob("TRAILER-*.mp4"))
    if not found:
        raise RuntimeError(f"no master under {ctx.out_dir}")
    return found[-1]


def caption_for(title: str, qc: dict | None, flags: list[str], rungs: dict[str, int]) -> str:
    numbers = ("no QC" if qc is None else
               f"{qc['integrated_lufs']:.1f} LUFS, {qc['true_peak']:.1f} dBTP, "
               f"{qc['cuts']} cuts ({qc['cuts_on_beat']:.0%} on beat)")
    taken = ", ".join(f"{step}: {n}" for step, n in sorted(rungs.items())) or "none"
    flagged = ", ".join(flags) or "none"
    return f"{title} -- trailer\n{numbers}\nflags: {flagged}\nrungs: {taken}"


def send(master: Path, caption: str) -> int:
    """Post the file through the studio's notifier; its exit code is the verdict."""
    done = subprocess.run(["uv", "run", "python", str(NOTIFIER), "video", "--file", str(master),
                           "--caption", caption], capture_output=True, text=True)
    return done.returncode


def deliver(ctx, master: Path, caption: str) -> dict:
    attempts = {"n": 0}
    file = deliverable(master, ctx.out_dir / "work")

    def attempt(rung, i):
        attempts["n"] += 1
        return send(file, caption)

    outcome = climb(LADDER, STEP_ID, attempt, lambda code: (code == 0, code, 0),
                    ctx.budget, ctx.learn, gate_name="telegram")
    return {"status": "undelivered" if outcome.terminal else "delivered",
            "attempts": attempts["n"], "file": file.relative_to(ctx.out_dir).as_posix()}


def manifest(ctx, master: Path, qc: QCReport | None) -> dict:
    learnings = [row.model_dump() for row in load(ctx.learnings_path)]
    flags = ["qc_missing"] if qc is None else list(qc.flags)
    return {"codex_id": ctx.codex_id, "trailer_id": ctx.trailer_id,
            "master": master.relative_to(ctx.book_dir).as_posix(),
            "qc": None if qc is None else qc.model_dump(),
            "floor_pass": None if qc is None else qc.floor_pass, "flags": flags,
            "learnings": learnings,
            "rungs_by_step": dict(Counter(row["step"] for row in learnings))}


def write_manifest(ctx, doc: dict) -> Path:
    path = ctx.out_dir / "manifest.json"
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def run(codex_id: str, ctx) -> None:
    master, qc = master_of(ctx), qc_of(ctx)
    doc = manifest(ctx, master, qc)
    write_manifest(ctx, doc)
    title = db.get_codex(ctx.conn, codex_id)["name"]
    caption = caption_for(title, doc["qc"], doc["flags"], doc["rungs_by_step"])
    doc["delivery"] = deliver(ctx, master, caption)
    doc["learnings"] = [row.model_dump() for row in load(ctx.learnings_path)]
    write_manifest(ctx, doc)
    print(f"[{STEP_ID}] {master.name} {doc['delivery']['status']} after "
          f"{doc['delivery']['attempts']} send(s); flags {doc['flags']}")
