#!/usr/bin/env python
"""Replay every screenplay check over every plan on disk, read-only (A3, craft ruling 2026-10-21).

    uv run python scripts/episode/screenplay_replay.py <codex> [<codex> ...] [--mutate=<codex>:<n>[,...]]
                                                       [--approved=<codex>:<n>[,...]] [--out=<file.json>]

One harness for the ruling's screenplay rows (G-MUTE, G-STOLEN, ORPHAN-REPLY, PARAGRAPH-HOLE,
G-REVEAL), modelled on `grammar_replay.py`.  Per plan it prints whether each check could READ the
plan and how many times it fired: a plan whose shots cite no span of its chapter is UNREADABLE for
a span check, never "0 fires" (old WotW and Scarlet plans carry no spans, so silence on them proves
nothing); `--approved` names the owner-approved plans, and each check says how many of them it read.
`--mutate` prints each check's recall, with its Wilson interval, pooled over code-made mutations of
the plans named: a prompt line deleted (orphan reply), a quote moved into narration (stolen line), a
dialogue paragraph dropped (paragraph hole).  It also prints the audience LOG rows (P6): the
longest window with no node, and every `plain` bed span in the intro or longer than 15 s.

A check is `fn(plan: dict, paragraphs: list[str]) -> list` (one item per fire), named in `CHECKS`
as "module:function"; one whose code is not built yet prints "not built".  Reads plan.json,
placed.json and the chapter by name only (the HDD rule).  $0, no write but `--out`.
"""
from __future__ import annotations

import copy
import importlib
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.episode.grammar_replay import plan_paths, targets  # noqa: E402,F401  (one plan walk)
from studio import plan_brief  # noqa: E402
from studio.judge_bench import wilson  # noqa: E402


@dataclass(frozen=True)
class Check:
    name: str
    target: object
    """A callable, or "module:function" imported when the replay runs."""
    needs: str
    """What a plan must carry to be read: `plan` (lines), `chapter` (its chapter too), `spans`
    (a shot source span that lands in its chapter)."""


CHECKS = {c.name: c for c in (
    Check("silent_speaker", "studio.screenplay_grammar:mute_faults", "plan"),      # A8 G-MUTE
    Check("stolen_line", "studio.story_layer:stolen_lines", "chapter"),           # A9 G-STOLEN
    Check("orphan_reply", "studio.screenplay_checks:orphan_replies", "spans"),     # A10
    Check("paragraph_hole", "studio.screenplay_checks:paragraph_holes", "spans"),  # A11
    Check("reveal_early", "studio.screenplay_grammar:reveal_faults", "plan"),      # A12 G-REVEAL
)}
NODE_SECTIONS = ("spike", "turn", "answer", "payoff", "act_out")
NODE_KINDS = ("dialogue", "tale")
INTRO_S, PLAIN_MAX_S = 30.0, 15.0
PROMPT = re.compile(r"\?|\b(?:let us|will you|shall we|promise)\b", re.I)
HOLE_WORDS = 40


def runner(check: Check):
    """The check's function, or None while its code is not built."""
    if callable(check.target):
        return check.target
    module, _, name = str(check.target).partition(":")
    try:
        return getattr(importlib.import_module(module), name)
    except (ImportError, AttributeError):
        return None


# ---- reading a plan against its chapter ------------------------------------------------------------

def normal(text: str) -> str:
    """Lower case, every non-word run (curly quotes included) one space."""
    return re.sub(r"[^a-z0-9']+", " ", str(text).lower().replace("’", "'")).strip()


def span_paragraph(span: str, paragraphs: list[str]) -> int | None:
    """The 0-based list index of the paragraph a source span comes from (its first 40 characters)."""
    key = normal(span)[:40].strip()
    return next((k for k, p in enumerate(paragraphs) if key and key in normal(p)), None)


def spans(plan: dict) -> list[str]:
    return [s for shot in plan.get("shots") or [] for s in shot.get("source") or []]


def readable(plan: dict, paragraphs: list[str], needs: str) -> bool:
    """Whether a plan carries what a check reads: lines, its chapter, or a span landing in it."""
    if not plan.get("lines"):
        return False
    if needs == "plan":
        return True
    if needs == "chapter":
        return bool(paragraphs)
    return any(span_paragraph(s, paragraphs) is not None for s in spans(plan))


def fires(plan: dict, paragraphs: list[str], check: Check) -> list | None:
    """The check's fires, or None when it is not built or cannot read this plan."""
    run = runner(check)
    return None if run is None or not readable(plan, paragraphs, check.needs) else list(run(plan, paragraphs))


def chapter_of(book: Path, path: Path) -> list[str]:
    return plan_brief.chapter_paragraphs(book, int(path.parent.name[2:4]))[1]


def replay(book: Path, path: Path, checks: dict = CHECKS) -> dict:
    """One plan's row: readable and fires per check (None = not read, never 0)."""
    plan = json.loads(Path(path).read_text(encoding="utf-8"))
    paragraphs = chapter_of(book, Path(path))
    return {"book": Path(book).name, "plan": str(Path(path).relative_to(book)), "number": number_of(Path(path)),
            "readable": {n: readable(plan, paragraphs, c.needs) for n, c in checks.items()},
            "fires": {n: fires(plan, paragraphs, c) for n, c in checks.items()}}


def number_of(path: Path) -> int:
    return int(Path(path).parent.name[2:4])


def is_approved(row: dict, approved: list[str]) -> bool:
    """Whether a row is one of the owner-approved plans named `<codex>:<n>` (a CLI input, never a list
    in code: the code tree names no book)."""
    return any(row["book"].startswith(c) and row.get("number") == int(n)
               for c, _, n in (a.partition(":") for a in approved))


def approved_said(rows: list[dict], name: str, approved: list[str] | None) -> str:
    """`approved: read 1 of 2, 0 fires` (ruling section 7, binding), or `approved: none named`."""
    if not approved:
        return "approved: none named"
    mine = [r for r in rows if is_approved(r, approved)]
    read = [r["fires"][name] for r in mine if r["fires"].get(name) is not None]
    return f"approved: read {len(read)} of {len(mine)}, {sum(len(f) for f in read)} fires"


def summary(rows: list[dict], checks: dict = CHECKS, approved: list[str] | None = None) -> dict[str, str]:
    """`orphan_reply: read 1 of 2 plans, 3 fires on 1 plans; approved: read 1 of 2, 0 fires`, or
    `not built; 1 of 2 plans readable`."""
    out = {}
    for name, check in checks.items():
        if runner(check) is None:
            out[name] = f"{name}: not built; {sum(bool(r['readable'].get(name)) for r in rows)} of {len(rows)} plans readable"
            continue
        read = [r["fires"][name] for r in rows if r["fires"].get(name) is not None]
        out[name] = (f"{name}: read {len(read)} of {len(rows)} plans, {sum(len(f) for f in read)} fires "
                     f"on {sum(bool(f) for f in read)} plans; {approved_said(rows, name, approved)}")
    return out


# ---- code-made mutations ---------------------------------------------------------------------------

def renumbered(plan: dict, lines: list[dict]) -> dict:
    out = copy.deepcopy(plan)
    out["lines"] = [{**copy.deepcopy(l), "index": k} for k, l in enumerate(lines)]
    return out


def delete_line(plan: dict, k: int) -> dict:
    """The plan without line k, the rest renumbered."""
    return renumbered(plan, [l for i, l in enumerate(plan["lines"]) if i != k])


def delete_prompt(plan: dict, k: int) -> dict:
    """The plan without prompt line k AND without the shot spans that show it (a span sharing a
    3-word run with the line): a prompt still cited on a shot is still shown, so its reply is no
    orphan under A10's own rule (wave 0 review, major 4)."""
    said = runs(plan["lines"][k]["text"], 3)
    out = delete_line(plan, k)
    for shot in out.get("shots") or []:
        shot["source"] = [s for s in shot.get("source") or [] if not runs(s, 3) & said]
    return out


def quote_to_narration(plan: dict, k: int) -> dict:
    """Line k given to the narrator, word for word: a stolen line."""
    lines = copy.deepcopy(plan["lines"])
    lines[k] = {**lines[k], "kind": "narration", "speaker": "narrator"}
    return renumbered(plan, lines)


def runs(text: str, n: int = 4) -> set[str]:
    words = normal(text).split()
    return {" ".join(words[i:i + n]) for i in range(len(words) - n + 1)}


def drop_paragraph(plan: dict, paragraphs: list[str], j: int) -> dict:
    """The plan with every span from paragraph j and every line sharing a 4-word run with it gone."""
    book = runs(paragraphs[j])
    out = renumbered(plan, [l for l in plan["lines"] if not runs(l["text"]) & book])
    for shot in out.get("shots") or []:
        shot["source"] = [s for s in shot.get("source") or [] if span_paragraph(s, paragraphs) != j]
    return out


def prompt_lines(plan: dict) -> list[int]:
    """Lines a cast member SPEAKS that prompt the next speaker: a `?` or let us / will you / shall we /
    promise, followed by another cast member's dialogue or tale.  A narration or inner line is heard
    by nobody in the scene, so it prompts no reply (wave 0 review, finding 6)."""
    lines = plan.get("lines") or []
    return [k for k, (a, b) in enumerate(zip(lines, lines[1:])) if PROMPT.search(a["text"])
            and a["kind"] in NODE_KINDS and a["speaker"] != "narrator"
            and b["kind"] in NODE_KINDS and b["speaker"] not in (a["speaker"], "narrator")]


def dialogue_paragraphs(plan: dict, paragraphs: list[str]) -> list[int]:
    """Paragraphs the plan's spans reach that hold a quote and 40 words or more."""
    reached = {span_paragraph(s, paragraphs) for s in spans(plan)} - {None}
    return sorted(j for j in reached if len(paragraphs[j].split()) >= HOLE_WORDS
                  and re.search("[“\"]", paragraphs[j]))


def mutants(plan: dict, paragraphs: list[str]) -> list[dict]:
    """Every code-made mutation of a plan, each naming the check it should wake."""
    out = [{"name": f"delete prompt line {k}", "expect": "orphan_reply", "plan": delete_prompt(plan, k)}
           for k in prompt_lines(plan)]
    out += [{"name": f"quote {k} into narration", "expect": "stolen_line", "plan": quote_to_narration(plan, k)}
            for k, l in enumerate(plan.get("lines") or []) if l["kind"] == "dialogue"]
    return out + [{"name": f"drop paragraph {j}", "expect": "paragraph_hole",
                   "plan": drop_paragraph(plan, paragraphs, j)} for j in dialogue_paragraphs(plan, paragraphs)]


PLACE = re.compile(r"\b(lines?|shots?) \d+")


def keys(found: list) -> Counter:
    """A check's fires with their line and shot numbers blanked: a deletion renumbers the plan, so a
    fire that only moved is the same fire (wave 0 review, finding 12)."""
    return Counter(PLACE.sub(r"\1 #", str(f)) for f in found)


def tally(plan: dict, paragraphs: list[str], check: Check, meant: list[dict]) -> tuple[int, int, int]:
    """(hits, readable mutants, unreadable mutants): a hit is a mutant with a fire the clean plan lacks."""
    base = keys(fires(plan, paragraphs, check) or [])
    got = [fires(m["plan"], paragraphs, check) for m in meant]
    read = [g for g in got if g is not None]
    return sum(bool(keys(g) - base) for g in read), len(read), len(got) - len(read)


def recall(plan: dict, paragraphs: list[str], checks: dict = CHECKS) -> dict[str, dict]:
    """Per built check: of the readable mutants meant for it, how many wake a fire the clean plan lacks."""
    return pooled_recall([(plan, paragraphs)], checks)


def pooled_recall(pairs: list[tuple[dict, list[str]]], checks: dict = CHECKS) -> dict[str, dict]:
    """Recall over the mutants of every (plan, paragraphs) named, with its Wilson interval: one plan
    gives ep01 2 orphan mutants, and 2 of 2 has a Wilson low of 0.342 (wave 0 review, major 5)."""
    out = {}
    for name, check in checks.items():
        if runner(check) is None:
            continue
        rows = [tally(p, paras, check, [m for m in mutants(p, paras) if m["expect"] == name]) for p, paras in pairs]
        k, n, dark = (sum(r[i] for r in rows) for i in range(3))
        if n or dark:
            low, high = wilson(k, n) if n else (0.0, 1.0)
            out[name] = {"k": k, "n": n, "unreadable": dark, "wilson_low": low, "wilson_high": high}
    return out


# ---- the audience LOG rows (P6): printed here, never in the plan battery ------------------------------

def starts(placed: dict) -> dict[int, float]:
    return {int(s["index"]): float(s["t_start"]) for s in placed["shots"]}


def nodes(plan: dict, placed: dict) -> list[float]:
    """Seconds where something new happens: a dialogue or tale line, a sound, a node shot."""
    t0 = starts(placed)
    said = [float(l["at"]) for l in placed.get("lines") or [] if l.get("kind") in NODE_KINDS]
    heard = [t0[int(s["index"])] + float(e.get("at") or 0) for s in plan["shots"] for e in s.get("sounds") or []]
    return said + heard + [t0[int(s["index"])] for s in plan["shots"] if s.get("section") in NODE_SECTIONS]


def middle_node(plan: dict, placed: dict) -> tuple[float, float, float]:
    """(from, to, seconds) of the longest window with no node."""
    edges = sorted([0.0, float(placed["duration_s"])] + nodes(plan, placed))
    a, b = max(zip(edges, edges[1:]), key=lambda ab: ab[1] - ab[0])
    return round(a, 1), round(b, 1), round(b - a, 1)


def bed_floor(plan: dict, placed: dict) -> list[tuple[float, float, float]]:
    """(from, to, seconds) of every `plain` bed span starting inside the intro or longer than 15 s."""
    t0, beds, end = starts(placed), plan.get("beds") or [], float(placed["duration_s"])
    spans_ = [(t0[int(b["from_shot"])], t0[int(n["from_shot"])] if n else end, b["tone"])
              for b, n in zip(beds, beds[1:] + [None])]
    return [(round(a, 1), round(b, 1), round(b - a, 1)) for a, b, tone in spans_
            if tone == "plain" and (a < INTRO_S or b - a > PLAIN_MAX_S)]


def log_rows(path: Path) -> str:
    """The P6 LOG line for one plan, or why it was not measured."""
    placed = Path(path).with_name("placed.json")
    if not placed.is_file():
        return "LOG not measured (no placed.json)"
    plan, laid = (json.loads(p.read_text(encoding="utf-8")) for p in (Path(path), placed))
    try:
        (a, b, s), beds = middle_node(plan, laid), bed_floor(plan, laid)
    except (KeyError, ValueError, TypeError) as why:      # an older placed.json than its plan
        return f"LOG not measured (placed.json does not match the plan: {why!r})"
    return f"LOG middle node: longest window with no node {s} s ({a}-{b}); plain beds {beds}"


def flag_values(argv: list[str], flag: str) -> list[str]:
    """Every comma-separated value of every `--<flag>=` argument."""
    return [v for a in argv if a.startswith(f"--{flag}=") for v in a.split("=", 1)[1].split(",") if v]


def mutate_targets(argv: list[str]) -> list[tuple[str, int]]:
    """(codex, episode) for each `--mutate=<codex>:<n>[,<codex>:<n>...]`."""
    return [(c, int(n)) for c, _, n in (v.partition(":") for v in flag_values(argv, "mutate"))]


def mutated(argv: list[str]) -> list[tuple[dict, list[str]]]:
    """The (plan, paragraphs) of every `--mutate` target, read by name."""
    from studio import episode_home
    out = []
    for codex, n in mutate_targets(argv):
        book = episode_home.book_dir(codex)
        path = episode_home.home(book, n) / "plan.json"
        out.append((json.loads(path.read_text(encoding="utf-8")), chapter_of(book, path)))
    return out


def main(argv: list[str]) -> int:
    out = next((a.split("=", 1)[1] for a in argv if a.startswith("--out=")), "")
    pairs = targets([a for a in argv if not a.startswith("--")])
    rows = [replay(book, path) for book, path in pairs]
    for (book, path), r in zip(pairs, rows):
        print(r["plan"], {k: (None if v is None else len(v)) for k, v in r["fires"].items()}, "|", log_rows(path))
    print("\n".join(summary(rows, approved=flag_values(argv, "approved")).values()))
    if pool := mutated(argv):
        print(f"recall on mutations of {len(pool)} plans:", pooled_recall(pool))
    if out:
        Path(out).write_text(json.dumps(rows, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
