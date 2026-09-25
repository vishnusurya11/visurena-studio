"""A judge's terminal that sets a unit aside: the step says so, the runner stops
the unit and records `deferred`, and the next pass authors again.

Not an owner gate (studio/escalate.py): nobody is asked to sign; the draft went
to a `.deferred.json` beside where the artefact would have been.
"""
from __future__ import annotations


class Deferred(Exception):
    def __init__(self, gate: str, aside: str, note: str):
        self.gate = gate          # PLAN
        self.aside = aside        # the .deferred.json, relative to the book
        self.note = note          # the terminal verdict's summary
        super().__init__(f"{gate}: {note} -> {aside}")

    def line(self, unit_label: str) -> str:
        """The run's line: what was deferred, where, and where the draft went."""
        return f"DEFERRED {self.gate} | {unit_label} | {self.note} | aside: {self.aside}"
