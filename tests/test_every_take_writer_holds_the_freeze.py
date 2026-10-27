"""Every writer of takes/**/T<nn>.mp4 holds the freeze (deadline retro 2026-10-20, item 6, lint half).

INCIDENT 4 (2026-10-19 12:29 PDT, Jekyll HEL ep01): the freeze an owner's repair puts on the delivered
takes guarded 2 of the 7 places that render or replace a take, and the other 5 were found one launch at a
time (7cdb216, 52e90bc, d5d5587, 837d1d9).  LESSONS brick 4 lists them; this test finds them by reading the
code, so the next new writer cannot bypass the freeze in silence.

How it reads the code (AST over studio/ and scripts/, no import, no GPU, no library/ read):
  1. BYTE WRITERS: every function in a module that names a take file and moves bytes (rename, a
     one-argument Path.replace, os.replace/rename, shutil.move/copy*, write_bytes, open() in a binary
     write mode, an argv list carrying `-y` wherever it is built).
     Each is either one of the five that put bytes on (or take them off) T<nn>.mp4, or names what it
     writes instead.  A new byte writer fails until it is sorted.
  2. THE CLOSURE: from those five, every caller, and its callers, up to a SITE that asks the freeze
     (take_dq.py's `--attempts` is a subprocess: every caller that passes it is a caller of its main).
     A caller that is neither a pass-through, a site nor a recorded gap fails: it writes a take and no
     one asked whether the repair froze it.
  3. THE SITES: each site's freeze is read where it sits, link by link, down to take_currency.
  4. THE SEVEN KNOWN SITES of LESSONS brick 4 (first pass, early round, batched rung, terminal, take_dq
     --attempts, master retake, the repair's own work) are each found in the code with their freeze.
The two writers that skip the freeze today are recorded as strict xfails (GAPS): fixing one turns its
xfail into a failure, which removes it from the list.  A gap does not stop the walk, so a new caller of
a gap fails the closure like any other unguarded writer.

What it cannot see: a call through getattr or a passed-in callback (harvest_labels hands
rejudge_attempts over as one), an argv whose `-y` is not a literal in a list, an open() whose mode is
not a literal, and a take module that names no take file by any TAKE pattern.  A writer imported
under another name is refused by its own test below."""
from __future__ import annotations

import ast
import re
import warnings
from pathlib import Path
from typing import NamedTuple

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCANNED = ("studio", "scripts")
TAKE = re.compile(r"T\{[^}]*:02d\}|T<NN>|T<nn>|T\?\?\.mp4|takes_dir\(|takes_under\(|\bTAKES\b")
"""A module that names a take file, or the take room, can write one."""
MOVERS = {"os": {"replace", "rename"}, "shutil": {"move", "copy", "copy2", "copyfile"}}
ATTEMPTS = re.compile(r"""["']--attempts["']""")
"""A spawn of take_dq.py with --attempts, in either quote."""
TAKE_DQ_MAIN = "scripts/episode/take_dq.py:main"

TAKE_BYTES = {
    "studio/episode_home.py:keep_aside": "the take renamed to the next T<nn>_failN.mp4 (bytes off)",
    "studio/episode_home.py:swap_in": "a kept draw renamed onto T<nn>.mp4",
    "studio/take_ladder.py:swap_in": "the best draw .replace()d onto T<nn>.mp4, the last one archived",
    "scripts/episode/takes_r2v.py:collect": "the render's video written as T<nn>.mp4 (write_bytes)",
    "scripts/episode/takes_r2v.py:fit_into": "ffmpeg -y beside the take, then tmp.replace(T<nn>.mp4)",
}
"""The five functions whose own bytes land on (or leave) T<nn>.mp4."""

NOT_A_TAKE = {
    "studio/episode_home.py:put_in_place": "write_json's temp JSON moved onto its target (fleet E A3)",
    "scripts/episode/assemble.py:quiet_bed": "the episode bed wav",
    "scripts/episode/assemble.py:generate": "one bed roll wav",
    "scripts/episode/assemble.py:refuse": "a refused bed roll, renamed for why",
    "scripts/episode/assemble.py:level": "a bed wav levelled in place",
    "scripts/episode/assemble.py:bed": "the instrumental bed wav",
    "scripts/episode/assemble.py:guard": "the gutter guard's frame crops (it reads the take)",
    "scripts/episode/assemble.py:still_segment": "a still segment of the cut",
    "scripts/episode/assemble.py:conform_card": "the title card in the episode's format",
    "scripts/episode/assemble.py:black_chip": "a black chip of the cut",
    "scripts/episode/assemble.py:trim": "the trimmed master",
    "scripts/episode/assemble.py:main": "cut/master_iter<k>.mp4",
    "scripts/episode/assemble.py:publish_master": "cut/master_iter<k>.mp4, the one upscale of the judged cut",
    "scripts/episode/face_refine.py:write_video": "a face crop under refine/",
    "scripts/episode/face_refine.py:silence": "a silent wav for a crop",
    "scripts/episode/face_refine.py:collect": "refine/T<nn>_p<k>.mp4, never T<nn>.mp4",
    "scripts/episode/qc.py:window": "one line's audio from the master",
    "scripts/episode/qc.py:speech_band": "the master's speech band wav",
    "scripts/episode/runcards.py:final_clip": "a shot's clip and strip cut from the master",
    "scripts/episode/storyboard.py:draw": "a storyboard sheet png",
    "scripts/episode/storyboard.py:repanel": "a panel png set aside as .prev.png",
    "scripts/episode/storyboard.py:still": "a still frame from a take (it reads the take)",
    "scripts/episode/take_dq.py:frame_at": "one frame png from a take (it reads the take)",
    "scripts/episode/take_dq.py:audio_dq": "a take's audio wav (it reads the take)",
    "scripts/episode/take_dq.py:judged_file": "work/T<nn>_head.mp4, the take from its head",
    "studio/judges/master_eye.py:put": "the master eye's cache json",
    "studio/script_mix.py:premix": "the bed-plus-lines premix",
    "studio/script_mix.py:master": "the mixed master",
    "studio/take_currency.py:carry_graph": "T<nn>.graph.json, the take's graph, not its bytes",
    "scripts/episode/takes_r2v.py:fit_argv": "the argv only: ffmpeg -y onto T<nn>_fit.mp4, which fit_into lands",
    "scripts/episode/takes_r2v.py:composite": "the take's audio wav (dialogue over silence), not the take",
}
"""Byte movers in a take module that write something else, and what."""

SANDBOX_ONLY = {
    "scripts/proof/face_replay.py:restore_take": "ep01's first-master take copied into the replay's sandbox room",
    "scripts/proof/face_replay.py:copy_named": "named episode records copied into the sandbox",
    "scripts/proof/face_replay.py:copy_if": "one record copied into the sandbox",
    "scripts/proof/face_replay.py:refine_workflows": "the refine workflows copied into the sandbox",
    "scripts/proof/face_replay.py:staged_picture": "a face crop png under the proof's review/ folder",
    "scripts/proof/face_replay.py:render": "the replay's recorded tiny-face draw onto a SANDBOX take, under the fence",
}
"""Proof-harness writers (2026-10-21_ep02_proof DESIGN 4.1): they write only into a rehearsal sandbox, where
no owner's repair has frozen anything.  `render` runs under the write fence (studio/rehearsal/fence.py),
which refuses a write under the real library; the copies run before the fence is armed, each into a path
under the sandbox it was handed.  Only a function under scripts/proof/ may be listed here."""

PASS_THROUGH = {
    "studio/episode_home.py:displace": "keep_aside plus the graph; its callers decide",
    "scripts/episode/takes_r2v.py:make_room": "displaces the take a render replaces",
    "scripts/episode/takes_r2v.py:land_scaled": "fit_into, or give_back on a failed scale",
    "scripts/episode/takes_r2v.py:give_back": "the displaced take swapped back in",
    "scripts/episode/takes_r2v.py:claim_one": "collect for one submitted take",
    "scripts/episode/takes_r2v.py:collect_all": "claim_one over a run",
    "scripts/episode/takes_r2v.py:collect_twice": "collect_all, once more for the transient losses",
    "scripts/episode/take_dq.py:settle": "swap_in of the best attempt under --attempts",
    TAKE_DQ_MAIN: "settle under --attempts; its callers (and every --attempts spawn) decide",
    "studio/take_ladder.py:best_draw": "take_ladder.swap_in of pick_best",
    "scripts/episode/tiny_face.py:restore": "the old take swapped back in after a draw",
}
"""Writers that carry the bytes to their callers: the freeze is asked above them."""


class Site(NamedTuple):
    how: str
    links: tuple[tuple[str, str], ...]
    """(function, the text in its source that asks the freeze), read in order down to take_currency."""


FROZEN_HERE = (("studio/take_ladder.py:frozen_here", "take_currency.frozen_in("),)
SITES = {
    "scripts/episode/takes_r2v.py:main": Site(
        "every render lands here: a first pass renders only what is not held, a named retake of a frozen "
        "take is refused (the backstop under the early round, the rung and the master retake)",
        (("scripts/episode/takes_r2v.py:main", "if not wants_render("),
         ("scripts/episode/takes_r2v.py:wants_render", "not refused_frozen(out)"),
         ("scripts/episode/takes_r2v.py:wants_render", "current()"),
         ("scripts/episode/takes_r2v.py:current_to", "take_currency.held("),
         ("scripts/episode/takes_r2v.py:refused_frozen", "take_currency.frozen("))),
    "studio/take_ladder.py:keep_best_draws": Site(
        "the terminal keeps a frozen take's bytes: no best-draw swap",
        (("studio/take_ladder.py:keep_best_draws", "kept_frozen(ctx.home, index) or best_draw("),
         ("studio/take_ladder.py:kept_frozen", "frozen_here("), *FROZEN_HERE)),
    "studio/take_ladder.py:measure_late": Site(
        "a frozen take is checked alone, never with --attempts",
        (("studio/take_ladder.py:measure_late", "if frozen_here(room, i)"),
         ("studio/take_ladder.py:measure_late", "if i not in frozen"), *FROZEN_HERE)),
    "studio/take_overlap.py:feed_cpu": Site(
        "the CPU lane passes --attempts only for the takes `ranked` allows, never a frozen one",
        (("studio/take_overlap.py:feed_cpu", "ranked(self.room"),
         ("studio/take_overlap.py:ranked", "not take_ladder.frozen_here(room, i)"), *FROZEN_HERE)),
    "scripts/episode/tiny_face.py:draw": Site(
        "the repair's own draw (takes_r2v --tiny-face); a dead render gives back the old take it set aside",
        (("scripts/episode/tiny_face.py:draw", "restore(room, i, saved[i])"),
         ("scripts/episode/tiny_face.py:restore", 'episode_home.swap_in(room, index, snap["fail"])'))),
    "scripts/episode/tiny_face.py:settle": Site(
        "a worse draw gives back the old take it set aside (keep_best)",
        (("scripts/episode/tiny_face.py:settle", "restore(room, i, snap)"),
         ("scripts/episode/tiny_face.py:restore", 'episode_home.swap_in(room, index, snap["fail"])'))),
}
"""Where the freeze is asked before the bytes of a take change."""

GAPS = {
    "scripts/calibration/harvest_labels.py:rejudge_attempts":
        "--rejudge runs take_dq.main(..., attempts=True) over every take with a dq record: settle can swap an "
        "archived draw over a take an owner's repair froze (it never asks take_ladder.frozen_here)",
    "scripts/episode/takes_r2v.py:render":
        "collects one take onto `out` with no wants_render; nothing in studio/ or scripts/ calls it today",
}
"""Writers that skip the freeze today, reported 2026-10-20 (package B1); each is a strict xfail."""

KNOWN_SEVEN = {
    1: ("first pass", (("scripts/episode/takes_r2v.py:main", "if not wants_render("),
                       ("scripts/episode/takes_r2v.py:current_to", "take_currency.held("))),
    2: ("early round", (("studio/take_overlap.py:early_cures", "take_ladder.route("),
                        ("studio/take_ladder.py:route", "curable_faults(verdict, room, window)"),
                        ("studio/take_ladder.py:curable_faults", "not frozen_here(room, i, window)"))),
    3: ("batched rung", (("studio/take_ladder.py:take", "routed = route(verdict, room"),
                         ("studio/take_ladder.py:take", "batch_for(ctx, rung, routed,"),
                         ("studio/take_ladder.py:route", "curable_faults(verdict, room, window)"),
                         ("studio/take_ladder.py:curable_faults", "not frozen_here(room, i, window)"))),
    4: ("terminal", (("studio/take_ladder.py:keep_best_draws", "kept_frozen("),)),
    5: ("take_dq --attempts", (("studio/take_ladder.py:measure_late", "frozen_here(room, i)"),
                               ("studio/take_overlap.py:ranked", "frozen_here(room, i)"))),
    6: ("master retake", (("studio/master_ladder.py:retake_through_take_ladder", "if refuse_frozen(ctx, shot)"),
                          ("studio/master_ladder.py:refuse_frozen", "take_ladder.kept_frozen("))),
    7: ("the repair's own work", (("scripts/episode/tiny_face.py:restore", 'snap["fail"]'),
                                  ("scripts/episode/face_refine.py:collect", "room / OUT /"))),
}
"""LESSONS brick 4 / LESSONS_ARCHIVE 'A freeze holds at every place that renders', numbered as there.
Sites 1-6 are read down to the freeze itself: the batched rung's batch (site 3) only renders what
`route` let through, and `route` drops every frozen take (curable_faults -> frozen_here).  Site 7 holds
differently: tiny_face gives the old take back, and face_refine writes its crops under refine/, never
onto T<nn>.mp4 -- these are not-a-write checks, not freeze checks."""


# ---- reading the code -------------------------------------------------------------------------

def sources() -> dict[str, str]:
    """rel posix path -> text, every .py under studio/ and scripts/ (the two code roots, nothing else)."""
    files = [p for folder in SCANNED for p in (ROOT / folder).rglob("*.py") if "__pycache__" not in p.parts]
    return {p.relative_to(ROOT).as_posix(): p.read_text(encoding="utf-8") for p in sorted(files)}


def parse(text: str) -> ast.AST:
    """The module's tree; a stray escape in someone's string is not this test's warning."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", SyntaxWarning)
        return ast.parse(text)


def mover(call: ast.Call) -> str | None:
    """The byte move a call makes, else None."""
    f = call.func
    if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name) and f.attr in MOVERS.get(f.value.id, ()):
        return f"{f.value.id}.{f.attr}"
    if isinstance(f, ast.Attribute) and f.attr in ("rename", "write_bytes"):
        return f.attr
    if isinstance(f, ast.Attribute) and f.attr == "replace" and len(call.args) == 1 and not call.keywords:
        return "replace"
    return "open wb" if isinstance(f, ast.Name) and f.id == "open" and binary_write(call) else None


def binary_write(call: ast.Call) -> bool:
    """An open() whose mode writes bytes ('wb', 'ab', 'xb', 'r+b' ...); a take is never written as text."""
    mode = call.args[1] if len(call.args) > 1 else next((k.value for k in call.keywords if k.arg == "mode"), None)
    said = mode.value if isinstance(mode, ast.Constant) and isinstance(mode.value, str) else ""
    return "b" in said and any(c in said for c in "wax+")


def overwrite_argv(node: ast.AST) -> str | None:
    """An argv list that carries '-y' (ffmpeg overwrites its output), wherever the list is built."""
    hit = isinstance(node, ast.List) and any(isinstance(e, ast.Constant) and e.value == "-y" for e in node.elts)
    return "ffmpeg -y" if hit else None


def moves_in(node: ast.AST) -> frozenset[str]:
    """Every byte move under one node: a moving call, or an overwriting argv list."""
    found = (mover(n) if isinstance(n, ast.Call) else overwrite_argv(n) for n in ast.walk(node))
    return frozenset(m for m in found if m)


def moves(source: str) -> frozenset[str]:
    return moves_in(parse(source))


def calls_in(node: ast.AST, stem: str) -> frozenset[tuple[str, str]]:
    """(module stem, name) of every call under the node: `mod.name(...)`, and a bare `name(...)` as the
    function's own module."""
    out = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name):
            out.add((stem, n.func.id))
        elif isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name):
            out.add((n.func.value.id, n.func.attr))
    return frozenset(out)


class Def(NamedTuple):
    source: str
    calls: frozenset[tuple[str, str]]
    moves: frozenset[str]


def joined(a: Def | None, b: Def) -> Def:
    """Two defs of one name in one file (a method and a function, say) read as one."""
    return b if a is None else Def(a.source + "\n" + b.source, a.calls | b.calls, a.moves | b.moves)


def functions(rel: str, text: str) -> dict[str, Def]:
    """'rel:name' -> every def of that name in the file, nested ones and methods too."""
    stem, out = Path(rel).stem, {}
    for node in ast.walk(parse(text)):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            key = f"{rel}:{node.name}"
            one = Def(ast.get_source_segment(text, node) or "", calls_in(node, stem), moves_in(node))
            out[key] = joined(out.get(key), one)
    return out


class Code(NamedTuple):
    defs: dict[str, Def]
    """'rel:name' -> the def."""
    takes: set[str]
    """The modules (rel) that name a take file."""


def read_code(texts: dict[str, str]) -> Code:
    defs = {k: v for rel, text in texts.items() for k, v in functions(rel, text).items()}
    return Code(defs, {rel for rel, text in texts.items() if TAKE.search(text)})


def byte_writers(code: Code) -> dict[str, frozenset[str]]:
    """'rel:name' -> its byte moves, for every function of a take module that moves bytes."""
    return {k: d.moves for k, d in code.defs.items() if d.moves and k.split(":")[0] in code.takes}


def as_callee(key: str) -> tuple[str, str]:
    rel, name = key.split(":")
    return Path(rel).stem, name


def callers(code: Code, key: str) -> set[str]:
    """Every function that calls `key` (by module stem and name); take_dq's main also has every function
    that spawns it with --attempts."""
    want = as_callee(key)
    found = {k for k, d in code.defs.items() if k != key and want in d.calls}
    if key == TAKE_DQ_MAIN:
        found |= {k for k, d in code.defs.items()
                  if not k.startswith("scripts/episode/take_dq.py:") and ATTEMPTS.search(d.source)}
    return found


def closure(code: Code, start: set[str], stop: set[str]) -> set[str]:
    """Every function above `start` in the call graph, walking up until a `stop` function."""
    seen, todo = set(), list(start)
    while todo:
        for up in callers(code, todo.pop()) - seen:
            seen.add(up)
            if up not in stop:
                todo.append(up)
    return seen


@pytest.fixture(scope="module")
def code() -> Code:
    return read_code(sources())


def writers_above(code: Code) -> set[str]:
    """Every function above a take writer, up to a freeze site.  A gap does not stop the walk: a new
    caller of a gap writes a take with no freeze above it, and must fail like any other."""
    return closure(code, set(TAKE_BYTES), set(SITES))


def loose_writers(code: Code) -> set[str]:
    """Functions above a take writer that are neither a writer, a pass-through, a site nor a gap."""
    return writers_above(code) - set(TAKE_BYTES) - set(PASS_THROUGH) - set(SITES) - set(GAPS) - set(SANDBOX_ONLY)


# ---- 1. byte writers --------------------------------------------------------------------------

def test_every_byte_writer_in_a_take_module_is_sorted(code):
    found = set(byte_writers(code))
    unsorted = found - set(TAKE_BYTES) - set(NOT_A_TAKE) - set(SANDBOX_ONLY)
    assert not unsorted, ("a new byte writer in a take module: is it a writer of T<nn>.mp4 (TAKE_BYTES, and "
                          f"then it must reach a freeze site) or does it write something else (NOT_A_TAKE)? {sorted(unsorted)}")
    stale = (set(TAKE_BYTES) | set(NOT_A_TAKE) | set(SANDBOX_ONLY)) - found
    assert not stale, f"no longer a byte writer (drop it from the lists): {sorted(stale)}"


def test_only_proof_harness_code_is_sandbox_only():
    """A production writer can never hide from the freeze by calling itself a sandbox writer."""
    assert all(k.startswith("scripts/proof/") for k in SANDBOX_ONLY), sorted(SANDBOX_ONLY)


@pytest.mark.parametrize("key", sorted(TAKE_BYTES))
def test_each_take_byte_writer_still_moves_bytes(code, key):
    assert byte_writers(code).get(key), f"{key}: {TAKE_BYTES[key]} -- it moves no bytes now"


# ---- 2. the closure ---------------------------------------------------------------------------

def test_every_caller_of_a_take_writer_reaches_the_freeze(code):
    loose = loose_writers(code)
    assert not loose, ("these write takes/**/T<nn>.mp4 (through a take writer) and no freeze site sits above "
                       f"them: ask take_currency.frozen / take_ladder.frozen_here there, or register the site: {sorted(loose)}")


def test_no_registered_writer_is_stale(code):
    above = writers_above(code)
    stale = (set(PASS_THROUGH) | set(SITES) | set(GAPS)) - above
    assert not stale, f"registered but no longer above a take writer: {sorted(stale)}"


# ---- 3. the sites -----------------------------------------------------------------------------

def link_holds(code: Code, link: tuple[str, str]) -> bool:
    key, said = link
    return key in code.defs and said in code.defs[key].source


@pytest.mark.parametrize("key", sorted(SITES))
def test_each_site_asks_the_freeze(code, key):
    broken = [link for link in SITES[key].links if not link_holds(code, link)]
    assert not broken, f"{key} ({SITES[key].how}): the freeze link is gone: {broken}"


def test_take_currency_answers_the_freeze_from_the_repair(code):
    frozen = code.defs["studio/take_currency.py:frozen"].source
    held = code.defs["studio/take_currency.py:held_in"].source
    assert "frozen_in(governing(home), take, home)" in frozen
    assert "frozen_in(window, take, home) is not None" in held


@pytest.mark.parametrize("key", sorted(GAPS))
@pytest.mark.xfail(strict=True, reason="a writer that skips the freeze today (GAPS); fixing it flips this")
def test_a_gap_asks_the_freeze(code, key):
    src = code.defs[key].source
    assert any(t in src for t in ("frozen_here(", "take_currency.frozen(", "kept_frozen(", "wants_render(")), GAPS[key]


# ---- 4. the seven known sites -----------------------------------------------------------------

def test_there_are_seven_known_sites():
    assert sorted(KNOWN_SEVEN) == list(range(1, 8))


@pytest.mark.parametrize("number", sorted(KNOWN_SEVEN))
def test_each_known_site_is_found_with_its_freeze(code, number):
    what, links = KNOWN_SEVEN[number]
    missing = [k for k, _ in links if k not in code.defs]
    assert not missing, f"site {number} ({what}): no such function now: {missing}"
    broken = [link for link in links if not link_holds(code, link)]
    assert not broken, f"site {number} ({what}): the freeze is gone from {broken}"


def test_every_freeze_site_above_a_writer_is_one_of_the_seven(code):
    named = {k for _, links in KNOWN_SEVEN.values() for k, _ in links} | {"studio/take_overlap.py:feed_cpu",
                                                                          "scripts/episode/tiny_face.py:draw",
                                                                          "scripts/episode/tiny_face.py:settle"}
    sites = writers_above(code) & set(SITES)
    assert sites == set(SITES) and sites <= named, sorted(sites - named)


def renamed_imports(rel: str, text: str) -> list[str]:
    """Imports that would hide a take writer from `callers`: a writer module under another name, or a
    writer function imported bare from another module."""
    stems = {as_callee(k)[0] for k in (*TAKE_BYTES, *PASS_THROUGH)}
    names = {as_callee(k)[1] for k in (*TAKE_BYTES, *PASS_THROUGH)}
    out = []
    for node in ast.walk(parse(text)):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            out += [f"{rel}: {a.name} as {a.asname}" for a in node.names
                    if a.asname and a.name.split(".")[-1] in stems and a.asname != a.name.split(".")[-1]]
        if isinstance(node, ast.ImportFrom) and (node.module or "").split(".")[-1] in stems:
            out += [f"{rel}: from {node.module} import {a.name}" for a in node.names if a.name in names]
    return out


def test_no_take_writer_is_imported_under_another_name():
    hidden = [line for rel, text in sources().items() for line in renamed_imports(rel, text)]
    assert not hidden, f"the lint resolves calls by module and name; these hide a take writer: {hidden}"


# ---- guard the guard --------------------------------------------------------------------------

LOOSE_WRITER = '''
from studio import episode_home

def sneak(room, index, best):
    episode_home.swap_in(room, index, best)        # T{index:02d}.mp4, and nobody asked the freeze
'''


def test_the_lint_catches_a_writer_that_skips_the_freeze(code):
    texts = {"scripts/episode/new_rung.py": LOOSE_WRITER,
             "studio/episode_home.py": (ROOT / "studio" / "episode_home.py").read_text(encoding="utf-8")}
    fake = read_code(texts)
    above = closure(fake, {"studio/episode_home.py:swap_in"}, set())
    assert "scripts/episode/new_rung.py:sneak" in above


def test_the_lint_sees_each_kind_of_byte_move():
    said = moves("def f(a, b, out, tmp):\n    a.rename(b)\n    tmp.replace(out)\n    os.replace(a, b)\n"
                 "    shutil.move(a, b)\n    out.write_bytes(b'')\n    run(['ffmpeg', '-y', str(out)])\n"
                 "    'x'.replace('a', 'b')\n")
    assert said == {"rename", "replace", "os.replace", "shutil.move", "write_bytes", "ffmpeg -y"}


def test_the_lint_sees_an_argv_built_first_and_a_binary_open():
    said = moves("def f(out):\n    cmd = ['ffmpeg', '-y', str(out)]\n    subprocess.run(cmd)\n"
                 "    with open(out, 'wb') as fh:\n        fh.write(b'')\n    open(out, 'rb').read()\n"
                 "    open(out).read()\n")
    assert said == {"ffmpeg -y", "open wb"}


GAP_CALLER = '''
from scripts.episode import takes_r2v
from scripts.calibration import harvest_labels

def revive(c, prompt_id, out):
    takes_r2v.render(c, prompt_id, out)

def rejudge(book, n):
    harvest_labels.rejudge_attempts(book, n)
'''


@pytest.mark.parametrize("caller", ["revive", "rejudge"])
def test_a_new_caller_of_a_gap_fails_the_lint(caller):
    texts = {**sources(), "scripts/episode/gap_caller.py": GAP_CALLER}
    assert f"scripts/episode/gap_caller.py:{caller}" in loose_writers(read_code(texts))


def test_a_single_quoted_attempts_spawn_is_a_caller_of_take_dq_main():
    texts = {"scripts/episode/take_dq.py": "def main():\n    pass\n",
             "scripts/episode/spawner.py": "def go(n):\n    run(['take_dq.py', str(n), '--attempts'])\n"}
    assert "scripts/episode/spawner.py:go" in callers(read_code(texts), TAKE_DQ_MAIN)
