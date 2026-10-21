"""The brain's scripted stream for a rehearsal (2026-10-21_ep02_proof DESIGN 3: `brain` is the real
brain code over ReplayTransport with a scripted stream per scenario: relaunch, redo:<step>, park).

The manifest's `brain_stream` is a list of words, one per brain session.  `install` wraps P4's SDK
source (fake_sdk's Library) so that the REAL brain.turn, asking for studio.brain:Verdict, gets the
next word as a Verdict result and parses, clamps and acts on it with its own code.  The wrap keeps
the Library's ask count, so a planted `sdk_faults` row still fires on its k-th ask and wins over
the script.  Every scripted answer is an sdk_log.jsonl row labelled `scripted`; past the end of the
stream, or for any other schema, the Library answers (recorded, substituted, then canned)."""
from __future__ import annotations

from pathlib import Path
from typing import Callable, Mapping

from studio.rehearsal import fakes

SCRIPTED = "scripted"
WORDS = ("relaunch", "redo:<step>", "park")


def verdict_of(word: str) -> dict:
    """A brain_stream word as the Verdict instance the brain would have answered."""
    kind, _, step = str(word).partition(":")
    if kind not in ("relaunch", "redo", "park") or (kind == "redo") != bool(step):
        raise ValueError(f"a brain_stream word is one of {', '.join(WORDS)}, not {word!r}")
    said = {"reason": f"scripted rehearsal verdict: {word}", "finding_row": f"| F? | rehearsal | 0 | scripted {word} | open |"}
    if kind == "redo":
        return {**said, "response": "cure", "order": {"kind": "redo", "step_id": step}}
    return {**said, "response": kind}


def is_brain(ask: Mapping) -> bool:
    """The brain's own verdict ask: the Verdict title AND its exact schema (other agents share the title)."""
    from studio import brain
    return ask.get("title") == "Verdict" and ask.get("schema") == brain.Verdict.model_json_schema()


class Scripted:
    """P4's Library with the brain's sessions answered from the stream first."""

    def __init__(self, library, stream: list[str], box: Path):
        for word in stream:
            verdict_of(word)                                 # a bad word refuses at install, not mid-run
        self.library, self.left, self.box = library, list(stream), Path(box)

    def __call__(self, ask: Mapping) -> list[dict]:
        lib = self.library
        if not self.left or not is_brain(ask) or lib.faults.get(lib.asked + 1) is not None:
            return lib(ask)
        lib.asked += 1
        word = self.left.pop(0)
        fakes.log(self.box, "sdk_log", {"n": lib.asked, "label": SCRIPTED, "title": ask.get("title"), "row": word})
        from studio.rehearsal import fake_sdk
        return [fake_sdk.result_row(verdict_of(word))]


def wrap(stream: list[str], box: Path) -> Callable[[], None]:
    """Put the script in front of the installed Library; the undo puts the Library back."""
    from studio.rehearsal import fake_sdk
    library = fake_sdk._SOURCE[0]
    fake_sdk._SOURCE[0] = Scripted(library, stream, box)
    return lambda: fake_sdk._SOURCE.__setitem__(0, library)


def install(manifest: Mapping, box: Path) -> bool:
    """Arm the script for this process when the manifest has one (after fakes.install); armed or not."""
    stream = list(manifest.get("brain_stream") or ())
    if not stream:
        return False
    fakes.on_import("studio.brain", lambda _brain: wrap(stream, box))
    return True
