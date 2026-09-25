"""An owner gate, raised: the step parks its unit and asks for one signature.

ESCALATE never blocks (docs/ARCHITECTURE.md): the runner records the event,
prints the call-sheet line, and moves on to other work.  The signature is a
file the next step refuses without; the next run resumes past the gate once
the file exists.
"""
from __future__ import annotations


class Escalation(Exception):
    def __init__(self, gate: str, verdict: str, ask: str):
        self.gate = gate          # LOOK | PLAN | EYE | MASTER | PUBLISH | MONEY
        self.verdict = verdict    # the file (relative to the unit) whose presence signs it
        self.ask = ask            # one line, what the owner is asked to look at
        super().__init__(f"{gate}: {ask} -> {verdict}")

    def line(self, unit_label: str) -> str:
        """The call-sheet line: who, what, where the signature goes."""
        return f"OWNER {self.gate} | {unit_label} | {self.ask} | sign: {self.verdict}"
