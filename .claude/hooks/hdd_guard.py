"""PreToolUse guard for Bash: refuse a recursive scan that climbs above the repo
or sweeps library/ or a drive root. D: is a spinning disk; on 2026-10-11 an
orphaned `grep -rn ... . ..` held it at 700-1000% disk time."""
import json
import re
import shlex
import sys

SCANNERS = {"grep", "egrep", "fgrep", "rg", "find", "du", "ls"}
RECURSIVE = re.compile(r"^-[a-zA-Z]*[rR]")
WIDE = re.compile(r"^(\.\.(/.*)?|(\./)?library(/[^/]+(/episodes)?)?|/[a-z]/?|[A-Za-z]:[\\/]?|/)$")
WHY = ("hdd_guard: recursive scans over '..', library/ or a drive root thrash the D: hard disk. "
       "Use the Grep tool scoped to code (studio/ scripts/ tests/ docs/), or name the one "
       "episode folder you need.")


def is_scan(words: list[str]) -> bool:
    """A scanner that walks a tree: find/rg always, grep/ls/du only when recursive."""
    if not words or words[0].rsplit("/", 1)[-1] not in SCANNERS:
        return False
    name = words[0].rsplit("/", 1)[-1]
    return name in ("find", "rg", "du") or any(RECURSIVE.match(w) for w in words[1:])


def refusal(command: str) -> str | None:
    """The refusal text when any piped/chained part scans a wide root, else None."""
    for part in re.split(r"&&|\|\||[|;]", command):
        try:
            words = shlex.split(part)
        except ValueError:
            words = part.split()
        if is_scan(words) and any(WIDE.match(w.rstrip("/") or "/") for w in words[1:]):
            return WHY
    return None


def main() -> None:
    command = (json.load(sys.stdin).get("tool_input") or {}).get("command") or ""
    why = refusal(command)
    if why:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                                 "permissionDecision": "deny",
                                                 "permissionDecisionReason": why}}))


if __name__ == "__main__":
    main()
