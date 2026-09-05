"""Affirmative-prompt lint: every string a model receives names what IS.

THE MECHANISM, measured three times in this repo: a text encoder embeds
tokens, and a negated noun is still that noun in the prompt.

    "no vocals, no backing vocals"   -> humming            (trailer_music)
    "no signage, no lettering"       -> CRISTERION on a board (trailer SKILL)
    "no people, no figures"          -> a room full of drinkers (PLATE_FRAME)

So the rule is derived, not stylistic: FILL THE SLOT.  Name what occupies the
place the unwanted thing would occupy -- a roster ("the complete percussion
section is a pocket watch and a pizzicato bass"), an acoustic ("bone dry,
every note stopping the instant the bow lifts"), an occupant ("furniture,
walls, weather and light the only presences").

`negations(text)` is the whole check.  Words that merely SPELL a negation --
nocturne, unaccompanied, shadowless -- and words that name an EVENT rather
than a denial -- silence, rest, stop, alone -- pass, because a player can
read them as an instruction.

Scanning: a module declares the strings it sends to a model in `MODEL_TEXT`,
and `--scan` reports only those.  Every other string in the file is a log
line, an error message or a regex, and a lint that shouts about those is a
lint people switch off.
"""
from __future__ import annotations

import ast
import json
import re
import sys
import warnings
from pathlib import Path

NEGATION = re.compile(
    r"(?<![\w-])("
    r"no|not|never|none|nobody|nothing|nowhere|neither|nor"
    r"|without|avoid(?:s|ed|ing)?|absent|absence|lack(?:s|ing)?"
    r"|free of|devoid of|rather than|instead of|other than|except"
    r"|don'?t|doesn'?t|isn'?t|aren'?t|won'?t|cannot|can'?t"
    r"|omit(?:s|ted)?|exclude(?:s|d)?|remove(?:s|d)?|forbid(?:s|den)?"
    r"|gone|missing"
    r")(?![\w-])",
    re.IGNORECASE)
"""The look-arounds treat a hyphen as a word character on purpose.

`\\b` would split `pump-organ` into `pump` and `organ` and `close-miked` into
`close` and `miked`, and would then flag nothing useful while `-drums` -- a
negative WEIGHT, the one form that is pure syntax -- slipped through.  With
`(?<![\\w-])` the hyphenated compounds pass whole and `-drums` is caught by
LEADING_MINUS below.  `no-one` and `non-diegetic` pass for the same reason.
"""

LEADING_MINUS = re.compile(r"(?:^|\s)-[A-Za-z]")
"""A weight, not a word: `-drums` is how a negative prompt is smuggled into a
positive one."""

UN_PREFIX = re.compile(
    r"(?<![\w-])un(?:wanted|desired|necessary)(?![\w-])", re.IGNORECASE)
"""The three `un-` words that mean "leave it out".  Every other `un-` word in
a score -- unaccompanied, unbroken, unhurried, unison, unlettered -- is a
playing instruction and passes."""

ALLOWED = (
    # spelled like a negation, meaning something else
    "nocturne", "notation", "notch", "note", "notes", "noted", "knot",
    "Nottingham", "Notre-Dame", "Nome", "Nordic", "innocent", "nobleman",
    "noble", "nose", "noon", "north", "nook", "noise", "nomad", "nonet",
    "nonchalant", "denote", "canon", "piano", "snow",
    # hyphen compounds whose head is a negation
    "no-one", "non-diegetic",
    # musical terms carrying a negation morpheme
    "unaccompanied", "undamped", "unmuted", "unison", "untuned", "unbroken",
    "unhurried", "uninterrupted", "unlettered", "unoccupied", "unmarked",
    "shadowless", "windowless", "wordless", "textless",
)
"""Regression fixtures as much as exemptions.

Most of these already pass the look-arounds; listing them says WHY, and keeps
them passing if the pattern is ever tightened.  A caller may name more of its
own -- a closed answer vocabulary handed to a labeller is data, not a request.
"""


def _mask(text: str, allowed: tuple[str, ...]) -> str:
    """Blank out the exempt terms so the pattern cannot see inside them."""
    masked = text
    for term in allowed:
        pattern = re.compile(
            rf"(?<![\w-]){re.escape(term)}(?![\w-])",
            re.IGNORECASE)
        masked = pattern.sub(lambda m: "*" * len(m.group(0)), masked)
    return masked


def negations(text: str, allowed: tuple[str, ...] = ()) -> list[str]:
    """Every phrase in `text` that asks for an absence, in the order found."""
    masked = _mask(text, ALLOWED + tuple(allowed))
    return ([m.group(0) for m in NEGATION.finditer(masked)]
            + [m.group(0).strip() for m in LEADING_MINUS.finditer(masked)]
            + [m.group(0) for m in UN_PREFIX.finditer(masked)])


def is_affirmative(text: str, allowed: tuple[str, ...] = ()) -> bool:
    """True when every request in `text` names something present."""
    return negations(text, allowed) == []


def _strings(node: ast.AST) -> list[str]:
    """Every string literal inside one constant, tuple, list or dict node."""
    if isinstance(node, ast.Constant):
        return [node.value] if isinstance(node.value, str) else []
    if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
        return [s for item in node.elts for s in _strings(item)]
    if isinstance(node, ast.Dict):
        return [s for value in node.values for s in _strings(value)]
    return []


def literals(tree: ast.Module) -> dict[str, tuple[int, list[str]]]:
    """Module-level `NAME = <literal>` assignments, as (line, strings)."""
    found: dict[str, tuple[int, list[str]]] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name):
                found[target.id] = (node.value.lineno, _strings(node.value))
    return found


def declared(path: Path) -> list[tuple[int, str]]:
    """(line, text) for every string this module declares model-facing.

    A module says so by listing its constants in `MODEL_TEXT`; a module that
    says nothing is not scanned, because its strings are error messages.
    """
    with warnings.catch_warnings():
        # A lint is not a syntax checker: another module's `\m` in a docstring
        # is its own business, and a warning here would look like a finding.
        warnings.simplefilter("ignore")
        tree = ast.parse(path.read_text(encoding="utf-8"))
    known = literals(tree)
    if "MODEL_TEXT" not in known:
        return []
    node = next(n.value for n in tree.body if isinstance(n, ast.Assign)
                and getattr(n.targets[0], "id", "") == "MODEL_TEXT")
    return [row for element in getattr(node, "elts", [])
            for row in _rows_for(element, known)]


def _rows_for(element: ast.AST, known: dict[str, tuple[int, list[str]]]) -> list[tuple[int, str]]:
    """One MODEL_TEXT entry, resolved to (line, text) pairs."""
    if isinstance(element, ast.Name) and element.id in known:
        line, texts = known[element.id]
        return [(line, text) for text in texts]
    return [(element.lineno, text) for text in _strings(element)]


def json_strings(path: Path) -> list[tuple[int, str]]:
    """(line, text) for every string value in a JSON document."""
    lines = path.read_text(encoding="utf-8").splitlines()
    found: list[tuple[int, str]] = []
    for text in _walk_json(json.loads(path.read_text(encoding="utf-8"))):
        line = next((i + 1 for i, raw in enumerate(lines) if text[:60] in raw), 1)
        found.append((line, text))
    return found


def _walk_json(value: object) -> list[str]:
    """Every string anywhere in a decoded JSON document."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [s for item in value.values() for s in _walk_json(item)]
    if isinstance(value, list):
        return [s for item in value for s in _walk_json(item)]
    return []


def offences(path: Path) -> list[str]:
    """`file:line: phrase :: text` for one file, or nothing when it is clean."""
    rows = json_strings(path) if path.suffix == ".json" else declared(path)
    return [f"{path}:{line}: {found[0]} :: {text.strip()[:100]}"
            for line, text in rows for found in [negations(text)] if found]


def scan(paths: list[Path]) -> list[str]:
    """Every offence under these files and directories, in walk order."""
    found: list[str] = []
    for path in paths:
        targets = (sorted(p for p in path.rglob("*") if p.suffix in (".py", ".json"))
                   if path.is_dir() else [path])
        for target in targets:
            found += offences(target)
    return found


def main(argv: list[str] | None = None) -> int:
    """`python -m studio.affirm --scan <path> ...` -- silence means clean."""
    args = [a for a in (argv if argv is not None else sys.argv[1:]) if a != "--scan"]
    found = scan([Path(a) for a in args] or [Path("studio"), Path("scripts")])
    for line in found:
        print(line)
    return 1 if found else 0


if __name__ == "__main__":
    raise SystemExit(main())
