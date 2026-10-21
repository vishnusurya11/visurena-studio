#!/usr/bin/env python
"""Every gate added since 2026-10-14, replayed on delivered records (2026-10-21_ep02_proof DESIGN 4.6, P6).

    uv run --no-sync python scripts/proof/gate_replay.py freeze <slug> <n>     # one episode, a NEW folder
    uv run --no-sync python scripts/proof/gate_replay.py freeze-all            # each missing one, one at a time
    uv run --no-sync python scripts/proof/gate_replay.py scrub                 # absolute paths made relative
    uv run --no-sync python scripts/proof/gate_replay.py run [--out=<dir>]     # results/gates.json

A delivered episode is frozen ONCE into tests/fixtures/delivered/<slug>_ep<NN>/ by
scripts/episode/regress_delivered.freeze (the deciders' records and stat.json: sizes, mtimes, each kept
take's sha8, never a video), plus the named records the gates read (plan, placed timeline, youtube
record, cards, refine.json, panel_dq) and the book's publish/standing.json under `_book/`, every absolute
path in them written relative to its episode (the repo stores no absolute path).  A folder that exists is
never written again; Jekyll's ep01 is frozen as jekyll_ep01, and the older `ep01` fixture with its
actions.baseline.json is the regress baseline's, read only.  The real library is opened for read, by name,
one episode at a time (never walked).

`run` asks each gate of scripts/proof/gates_under_test.yaml -- its REAL callable, through its reader --
about every unit of every frozen episode: `refused`, `passed` or `unread` (the record it needs is not
in the fixture).  Per gate: refusals over n readable units, unread units counted apart, and each refusal
in one of four places: `confirmed` (an owner ruled it a true fault), `ruled_false` (an owner ruled it
false), `expected` (an owner ruling the spec cites already explains it) or `unruled` (no ruling yet).
No refusal is called false without an owner's ruling.  One DESIGN 5 row per gate, passed only with
none unruled and none ruled false.  $0, no GPU."""
from __future__ import annotations

import importlib
import json
import re
import shutil
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.episode import regress_delivered as rd  # noqa: E402
from studio.rehearsal import instrument_gate as ig  # noqa: E402

SPEC = Path(__file__).with_name("gates_under_test.yaml")
FIXTURES = rd.FIXTURES
RESULTS = ROOT / "docs" / "audit" / "2026-10-21_ep02_proof" / "results"
BOOK_DIR = "_book"
EXTRAS = ("plan.json", "placed.json", "youtube.json", "takes/r2v/prompts.json", "takes/r2v/refine.json",
          "storyboard/panel_dq.json")
BOOK_EXTRAS = ("publish/standing.json",)
SLUGS = ("wotw", "scarlet", "jekyll")
"""The books whose episodes this replay freezes, each into a new <slug>_epNN folder."""
ABSOLUTE = re.compile(r"^(?:[A-Za-z]:[\\/]|\\\\)")
"""A Windows absolute path (drive or UNC): never stored in a fixture."""
ROOM = "takes/r2v"
COUNTS = ("refusals", "flags", "rewords")
"""What a gate's `refused` verdict is: a refusal (counted false unless confirmed), an advisory flag (log
only, never a refusal), or a row the change rewords (a wording change refuses nothing)."""


# ---- the spec and the fixtures ----------------------------------------------------------------------

def load_spec(path: Path = SPEC) -> dict:
    import yaml
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def resolve(dotted: str):
    """`module:attribute` -> the object (the gate's real callable)."""
    module, _, name = dotted.partition(":")
    return getattr(importlib.import_module(module), name)


def numbers(text: str) -> list[int]:
    """`1-27` or `1,3,5` -> the episode numbers."""
    out = []
    for part in str(text).split(","):
        a, _, b = part.strip().partition("-")
        out += list(range(int(a), int(b or a) + 1))
    return out


def fixture_name(slug: str, number: int) -> str:
    if slug not in SLUGS:
        raise ValueError(f"{slug!r}: this replay freezes new {SLUGS} folders only")
    return f"{slug}_ep{number:02d}"


def episodes(spec: dict, root: Path = FIXTURES) -> list[tuple[str, Path, int]]:
    """(fixture name, its folder, episode number) for every episode the spec names."""
    out = []
    for book in spec["episodes"]:
        for n in numbers(book["numbers"]):
            name = book.get("fixture") or fixture_name(book["slug"], n)
            out.append((name, Path(root) / name, n))
    return out


def copy_extras(src: Path, dest: Path, names: tuple[str, ...]) -> list[str]:
    done = []
    for rel in names:
        if (Path(src) / rel).is_file():
            rd.copy_record(Path(src) / rel, Path(dest) / rel)
            done.append(rel)
    return done


def relative_text(text: str) -> str:
    """An absolute path as the fixture keeps it: relative to its episode, else to its book, else its name."""
    if not ABSOLUTE.match(text):
        return text
    slashed = text.replace("\\", "/")
    found = re.search(r"/episodes/ep\d+/(.+)$", slashed) or re.search(r"/library/[^/]+/(.+)$", slashed)
    return found.group(1) if found else slashed.rsplit("/", 1)[-1]


def absolute_strings(doc) -> set[str]:
    """Every absolute path string in a record, at any depth."""
    if isinstance(doc, dict):
        return {s for v in doc.values() for s in absolute_strings(v)}
    if isinstance(doc, list):
        return {s for v in doc for s in absolute_strings(v)}
    return {doc} if isinstance(doc, str) and ABSOLUTE.match(doc) else set()


def scrubbed_text(text: str) -> str:
    """A record's text with each absolute path string written relative (relative_text), every other byte
    as it was (the record's own layout kept)."""
    for value in sorted(absolute_strings(json.loads(text))):
        for said in {json.dumps(value), json.dumps(value, ensure_ascii=False)}:
            text = text.replace(said, json.dumps(relative_text(value), ensure_ascii=False))
    return text


def scrub(folder: Path) -> list[str]:
    """Rewrite each JSON record of a fixture that holds an absolute path; the records rewritten."""
    done = []
    for path in sorted(Path(folder).rglob("*.json")):
        text = path.read_text(encoding="utf-8")
        if (clean := scrubbed_text(text)) != text:
            path.write_text(clean, encoding="utf-8", newline="\n")
            done.append(path.relative_to(folder).as_posix())
    return done


def freeze(home: Path, book: Path, dest: Path) -> dict:
    """One delivered episode into a NEW fixture folder: regress_delivered.freeze, the gate records, the
    book's standing file, every absolute path made relative.  A folder that exists is refused."""
    if Path(dest).exists():
        raise FileExistsError(f"{dest} exists: a delivered fixture is frozen once, never written again")
    doc = rd.freeze(Path(home), Path(dest))
    extras = copy_extras(home, dest, EXTRAS) + [f"{BOOK_DIR}/{r}" for r in copy_extras(book, Path(dest) / BOOK_DIR, BOOK_EXTRAS)]
    return {"records": len(doc["files"]), "takes": len(doc["kept"]), "draws": len(doc["draws"]), "extras": extras,
            "scrubbed": scrub(dest)}


def freeze_named(spec: dict, slug: str, number: int) -> tuple[Path, dict]:
    from studio import episode_home
    book_id = next(b["book"] for b in spec["episodes"] if b["slug"] == slug)
    book = episode_home.book_dir(book_id)
    dest = FIXTURES / fixture_name(slug, number)
    return dest, freeze(episode_home.home(book, number), book, dest)


# ---- reading a fixture ------------------------------------------------------------------------------

def read(fixture: Path, rel: str, default=None):
    path = Path(fixture) / rel
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else default


def number_of(fixture: Path) -> int:
    return int(re.search(r"ep(\d+)$", Path(fixture).name).group(1))


def item(unit: str, verdict: str, why: str = "") -> dict:
    return {"unit": unit, "verdict": verdict, "why": why}


def ns(doc: dict):
    """A plan's dicts as attribute objects: the gates read fields by getattr."""
    return SimpleNamespace(**{k: v for k, v in doc.items()})


def plan_ns(plan: dict):
    """The plan's setups and shots as attribute objects (no contract: a historical plan still reads)."""
    setups = {k: ns(v) for k, v in (plan.get("setups") or {}).items()}
    return SimpleNamespace(setups=setups, shots=[ns(s) for s in plan.get("shots") or []])


def cards_of(fixture: Path) -> list[dict]:
    """The take cards: prompts.json, else the delivered shots.json."""
    return read(fixture, f"{ROOM}/prompts.json") or read(fixture, f"{ROOM}/shots.json") or []


def dq_rows(fixture: Path) -> dict[int, dict]:
    return {int(p.name[1:3]): json.loads(p.read_text(encoding="utf-8"))
            for p in sorted((Path(fixture) / ROOM).glob("T[0-9][0-9].dq.json"))}


# ---- the readers: one frozen episode -> [{unit, verdict, why}] ----------------------------------------

def standing(fixture: Path, ok) -> list[dict]:
    """G-STANDING: would step 13 upload this episode on the book's standing approval?"""
    book = Path(fixture) / BOOK_DIR
    if not (book / "publish" / "standing.json").is_file():
        return [item("episode", "unread", "no publish/standing.json frozen for the book")]
    return [item("episode", "passed" if ok(book, number_of(fixture)) else "refused", "the file does not list it")]


def credit(fixture: Path, faults) -> list[dict]:
    """G-META: the delivered description's credit line."""
    doc = read(fixture, "youtube.json")
    if doc is None:
        return [item("episode", "unread", "no youtube.json frozen")]
    said = faults(str(doc.get("description") or ""))
    return [item("episode", "refused" if said else "passed", "; ".join(said))]


def outside(fixture: Path, refusal) -> list[dict]:
    """The unread-outside wall on every kept paste of the delivered refine.json."""
    doc = read(fixture, f"{ROOM}/refine.json")
    if doc is None:
        return [item("episode", "unread", "no takes/r2v/refine.json frozen (no refine ran, or not frozen)")]
    out = []
    for take, entry in sorted((k, v) for k, v in doc.items() if k[:1] == "T" and k[1:].isdigit()):
        for p in (p for p in entry.get("people") or [] if p.get("kept")):
            said = refusal((p.get("measures") or {}).get("outside"))
            out.append(item(f"{take} {p.get('who')}", "refused" if said else "passed", said))
    return out


def face_list(fixture: Path, listing) -> list[dict]:
    """The face list over the delivered records: a listed take counts (log only)."""
    from studio import face_refine as fr
    cards, plan = cards_of(fixture), read(fixture, "plan.json")
    if plan is None:
        return [item("episode", "unread", "no plan.json frozen (the sizes decide what the refine can reach)")]
    sizes = {int(s["index"]): s.get("size", "") for s in plan.get("shots") or []}
    shas = {int(Path(k).name[1:3]): v["sha8"] for k, v in (read(fixture, rd.STAT) or {}).get("kept", {}).items()}
    said = listing(fr.face_rows(cards, sizes, dq_rows(fixture), read(fixture, f"{ROOM}/refine.json") or {}, shas))
    return [item(t, "refused" if t in said["listed"] else "passed", row.get("status", ""))
            for t, row in said["takes"].items()]


def tiny_face(fixture: Path, record) -> list[dict]:
    """The A28 column on every panel with a measured face."""
    rows = read(fixture, "storyboard/panel_dq.json")
    if rows is None or not any(r.get("face_h") is not None for r in rows):
        return [item("episode", "unread", "no storyboard/panel_dq.json frozen" if rows is None else "no panel measured face_h")]
    return [item(f"shot {r.get('shot')}", "refused" if record(r["face_h"])["tiny_face_advisory"] else "passed",
                 f"{record(r['face_h'])['face_px_768']} px") for r in rows if r.get("face_h") is not None]


def hole(fixture: Path, holes) -> list[dict]:
    """G-HOLE's ruler (HOLE_WALL_S + HOLE_SLACK_S) on the measured placed timeline."""
    from studio import speech_gap
    placed = read(fixture, "placed.json")
    if placed is None:
        return [item("episode", "unread", "no placed.json frozen")]
    found = holes(placed, speech_gap.HOLE_SLACK_S)
    return [item("episode", "refused" if found else "passed", "; ".join(f"{b - a:.2f} s at {a:.2f}" for a, b, _ in found))]


def orphan_crowd(fixture: Path, faults) -> list[dict]:
    """G-CROWD-ORPHAN on every setup of the delivered plan; a fault is its setup's by the whole name
    (plan_gates.fault's "<gate> setup <name>: "), so walk_on_day never takes walk_on_day_2's."""
    plan = read(fixture, "plan.json")
    if plan is None:
        return [item("plan", "unread", "no plan.json frozen")]
    said = faults(plan_ns(plan))
    hits = {name: [f for f in said if f" setup {name}: " in f] for name in plan.get("setups") or {}}
    return [item(f"setup {name}", "refused" if hit else "passed", "; ".join(hit)) for name, hit in hits.items()]


def style_light(fixture: Path, lint) -> list[dict]:
    """L28 on every delivered take prompt, its setup's night read from the plan."""
    from studio import house_style
    setups = (read(fixture, "plan.json") or {}).get("setups") or {}
    cards = read(fixture, f"{ROOM}/shots.json") or cards_of(fixture)
    out = []
    for c in cards:
        setup = setups.get(c.get("setup"))
        said = lint(c.get("prompt") or "", {"night": house_style.is_night(ns(setup))}) if setup else None
        out.append(item(f"T{int(c['index']):02d}", "unread" if said is None else ("refused" if said else "passed"),
                        "; ".join(said or [])))
    return out


def wording(fixture: Path, note) -> list[dict]:
    """Every advisory frozen-whole dq row: one that printed HARD is what the new wording corrects."""
    from studio import stillness
    out = []
    for i, dq in dq_rows(fixture).items():
        for g in (g for g in dq.get("gates") or [] if g.get("name") == stillness.KIND and not g.get("hard") and not g.get("ok")):
            text = str(g.get("note") or "")
            fixed = "HARD" in text and "HARD" not in note(text)
            out.append(item(f"T{i:02d}", "refused" if fixed else "passed", text[:80]))
    return out


def dry_check(fixture: Path, replay) -> list[dict]:
    """The launch's dry check on regress_delivered's stand-in (with the frozen plan beside the deciders'
    records): a take whose `held` action is not keep would refuse the launch.  A dry check that raises
    on the records is unread, with its error: never a pass."""
    if not (Path(fixture) / rd.STAT).is_file() or not (Path(fixture) / ROOM / "shots.json").is_file():
        return [item("episode", "unread", "no stat.json or shots.json frozen")]
    home, doc = rd.stand_in(Path(fixture))
    try:
        copy_extras(fixture, home, ("plan.json",))
        rows = replay(home, doc)
    except Exception as failed:                 # the check could not answer on these records
        return [item("episode", "unread", f"the dry check raised {type(failed).__name__}: {str(failed)[:160]}")]
    finally:
        shutil.rmtree(home.parent, ignore_errors=True)
    return [item(t, "passed" if v["held"].startswith("keep") else "refused", v["held"][:120]) for t, v in rows.items()]


READERS = {"standing": standing, "credit": credit, "outside": outside, "face_list": face_list,
           "tiny_face": tiny_face, "hole": hole, "orphan_crowd": orphan_crowd, "style_light": style_light,
           "wording": wording, "dry_check": dry_check}


# ---- the tally and the report ------------------------------------------------------------------------

def tally(items: list[dict], confirmed: list[dict], counts: str = "refusals", expected: dict | None = None,
          ruled_false=()) -> dict:
    """refusals over n readable units, unread apart, each refusal confirmed, ruled false, expected (by the
    owner ruling `expected` cites) or unruled.  An advisory gate's `refused` units are FLAGS and a wording
    change's are REWORDS: neither is a refusal."""
    sure, wrong = {c["unit"] for c in confirmed or []}, {c["unit"] for c in ruled_false or []}
    hit = [r["unit"] for r in items if r["verdict"] == "refused"]
    refused = hit if counts == "refusals" else []
    rest = [u for u in refused if u not in sure | wrong]
    readable = [r for r in items if r["verdict"] != "unread"]
    return {"n": len(readable), "refused": len(refused), "flagged": len(hit) if counts == "flags" else 0,
            "reworded": len(hit) if counts == "rewords" else 0, "unread": len(items) - len(readable),
            "confirmed": [u for u in refused if u in sure], "ruled_false": len([u for u in refused if u in wrong]),
            "expected": len(rest) if expected else 0, "expected_by": expected, "unruled": 0 if expected else len(rest)}


def run_gate(gate: dict, fixtures: list[tuple[str, Path, int]]) -> dict:
    """One gate over every frozen episode that exists; a missing fixture is counted, never guessed."""
    fn, reader = resolve(gate["callable"]), READERS[gate["reader"]]
    items, missing = [], []
    for name, path, _ in fixtures:
        if not Path(path).is_dir():
            missing.append(name)
            continue
        items += [{**r, "unit": f"{name} {r['unit']}"} for r in reader(Path(path), fn)]
    said = tally(items, gate.get("confirmed") or [], gate.get("counts", "refusals"), gate.get("expected"),
                 gate.get("ruled_false") or [])
    return {**said, "missing_fixtures": missing,
            "refusals": [r for r in items if r["verdict"] == "refused"], "unread_units": [r for r in items if r["verdict"] == "unread"]}


def gate_row(gate: dict, said: dict) -> dict:
    passed = said["n"] > 0 and said["unruled"] == 0 and said["ruled_false"] == 0
    row = ig.proof_row(f"gate_replay.{gate['id']}", gate["question"], passed, said["n"], said["n"],
                       ["results/gates.json", "scripts/proof/gates_under_test.yaml"], {"recorded": said["n"]},
                       gate["callable"], "n/a (a gate, not an instrument)", "compliance")
    return {**row, "n_pass": said["n"] - said["unruled"] - said["ruled_false"]}


def report(spec: dict, fixtures: list[tuple[str, Path, int]]) -> dict:
    """Every gate's tally (or why it is not replayed) and one DESIGN 5 row per replayed gate."""
    gates, rows = {}, []
    for gate in spec["gates"]:
        if not gate.get("reader"):
            gates[gate["id"]] = {"replayed": False, "why": gate["why_not_replayed"], "commit": gate["commit"]}
            continue
        said = run_gate(gate, fixtures)
        gates[gate["id"]] = {"replayed": True, "since": gate["since"], "commit": gate["commit"],
                             "unit": gate.get("unit"), "counts": gate.get("counts", "refusals"), **said}
        rows.append(gate_row(gate, said))
    return {"fixtures": [name for name, path, _ in fixtures if Path(path).is_dir()], "gates": gates, "proof_rows": rows}


def headline(doc: dict) -> list[str]:
    out = [f"{len(doc['fixtures'])} frozen episodes"]
    for gid, g in doc["gates"].items():
        out.append(f"{gid}: " + (said_of(g) if g["replayed"] else f"not replayed: {g['why'][:90]}"))
    return out


def said_of(g: dict) -> str:
    if g["counts"] == "flags":
        return f"{g['flagged']}/{g['n']} flagged (advisory, never a refusal), {g['unread']} unread"
    if g["counts"] == "rewords":
        return f"{g['reworded']}/{g['n']} rows reworded (wording, never a refusal), {g['unread']} unread"
    return (f"{g['refused']}/{g['n']} refused ({len(g['confirmed'])} confirmed, {g['ruled_false']} ruled false, "
            f"{g['expected']} expected by ruling, {g['unruled']} unruled), {g['unread']} unread")


def freeze_all(spec: dict) -> list[str]:
    """Every missing new fixture, one episode at a time; an existing folder is left as it is."""
    out = []
    for name, path, n in episodes(spec):
        if Path(path).exists() or not name.startswith(SLUGS):
            continue
        dest, said = freeze_named(spec, name.split("_")[0], n)
        out.append(f"{dest.name}: {said['records']} records, {said['takes']} takes, extras {len(said['extras'])}")
        print(out[-1], flush=True)
    return out


def main(argv: list[str]) -> int:
    spec = load_spec()
    if argv[:1] == ["freeze"]:
        dest, said = freeze_named(spec, argv[1], int(argv[2]))
        print(f"{dest}\nfroze {said}")
        return 0
    if argv[:1] == ["freeze-all"]:
        freeze_all(spec)
        return 0
    if argv[:1] == ["scrub"]:
        for name, path, _ in episodes(spec):
            print(f"{name}: {len(scrub(path))} records made relative", flush=True)
        return 0
    out = next((Path(a.split("=", 1)[1]) for a in argv if a.startswith("--out=")), RESULTS)
    doc = report(spec, episodes(spec))
    out.mkdir(parents=True, exist_ok=True)
    (out / "gates.json").write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(out / "gates.json")
    print("\n".join(headline(doc)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
