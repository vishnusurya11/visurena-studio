"""The screenplay contracts. Shared by three agents, the renderer, and every check.

The wire model is FLAT, not a discriminated union: studio/llm.py calls the provider's
strict structured outputs, and pydantic emits tagged unions as `oneOf` + `discriminator`.
We were burned once by an untested provider interaction (the 800-retry incident), so the
decision procedure is the free offline test `test_element_schema_is_provider_safe`.
Flip to a union, run it, keep it if it passes.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

Kind = Literal["action", "dialogue", "transition"]
Prov = Literal["verbatim", "adapted", "invented"]
IntExt = Literal["INT", "EXT", "INT/EXT", "UNKNOWN"]
TimeOfDay = Literal["DAY", "NIGHT", "DAWN", "DUSK", "CONTINUOUS", "LATER",
                    "MOMENTS LATER"]
Transfer = Literal["transfer", "adaptation_proper", "invented_connective"]


class SceneRef(BaseModel):
    chapter: int
    scene: int


class ScriptElement(BaseModel):
    kind: Kind
    text: str
    character: str | None = None       # dialogue only — canonical character id
    parenthetical: str | None = None
    provenance: Prov = "invented"
    source: SceneRef | None = None     # required when provenance == "verbatim"
    dual: bool = False


    @model_validator(mode="after")
    def _dialogue_needs_a_speaker(self):
        """A line with nobody attached renders a headless cue and reaches the page as
        garbage. Caught here rather than three steps downstream."""
        if self.kind == "dialogue" and not self.character:
            raise ValueError("a dialogue element must name its character")
        if self.kind != "dialogue" and self.parenthetical:
            raise ValueError("only dialogue may carry a parenthetical")
        if self.provenance == "verbatim" and self.source is None:
            raise ValueError("a verbatim claim must cite the scene it came from")
        return self


class SceneDraft(BaseModel):
    """What the screenwriter returns for ONE beat."""
    elements: list[ScriptElement]


class Beat(BaseModel):
    """One unit of the plan: a sequence, not a scene. ~4.5 slug lines each."""
    id: str
    intent: str                        # what it must accomplish, in one line
    unifying_aspect: str
    protagonist: str                   # canonical id — not always the lead
    objective: str                     # an infinitive: "to get her to admit it"
    boundary_event: str                # what ends it and pressures the next
    source: list[SceneRef]
    transfer: Transfer
    cold_open: bool = False
    difficulty: str = "easy"           # how much the audience must hold unexplained
    reversal: str | None = None        # required on the opening beat
    flashback: bool = False


class Omission(BaseModel):
    source: SceneRef
    reason: str


class ScreenplayPlan(BaseModel):
    """What the story editor returns for the WHOLE book. One call."""
    spine: str                         # one sentence; every beat hangs off it
    logline: str
    opening_beat_id: str
    final_beat_id: str
    bookend: str                       # how the two pair, stated
    must_keep: list[str] = Field(default_factory=list)
    beats: list[Beat]
    omitted: list[Omission] = Field(default_factory=list)


class Shot(BaseModel):
    """One camera setup over an element-index range in an already-frozen stream."""
    index: int
    covers_start: int
    covers_end: int                    # inclusive
    setup: str                         # spelled out — never "MCU"
    term: str | None = None            # null when no vocabulary term fits
    visual_consequence: str            # what the term alone cannot transmit
    axis_side: Literal["A", "B"] = "A"
    travel_direction: Literal["left", "right"] | None = None
    crosses_axis: bool = False
    licensed_by: int | None = None     # the neutral shot permitting a crossing


class ShotPlan(BaseModel):
    """What the shot designer returns for ONE beat."""
    shots: list[Shot]


class Issue(BaseModel):
    """One auditor finding. No quote, no issue — checked before it counts."""
    scene: int
    kind: Literal["place", "knowledge", "deduction", "state", "identity",
                  "verbatim", "period"]
    severity: Literal["blocking", "minor"]
    book_quote: str                    # verbatim; is_grounded() BEFORE it counts
    script_quote: str
    why: str


class AuditVerdict(BaseModel):
    ok: bool
    issues: list[Issue] = Field(default_factory=list)


class Slug(BaseModel):
    int_ext: IntExt
    location_id: str | None
    location_name: str
    time: TimeOfDay
    text: str                          # "INT. 221B BAKER STREET - NIGHT"


class Scene(BaseModel):
    number: int
    beat_id: str
    slug: Slug
    cast: list[str] = Field(default_factory=list)
    speaking: list[str] = Field(default_factory=list)
    elements: list[ScriptElement] = Field(default_factory=list)
    shots: list[Shot] = Field(default_factory=list)
    source: list[SceneRef] = Field(default_factory=list)
    transfer: Transfer = "adaptation_proper"
    page_eighths: int = 0              # measured by code, never asked of an agent
    duration_s: float = 0.0


class Totals(BaseModel):
    scenes: int
    pages: float
    runtime_s: float
    cast: int


class Screenplay(BaseModel):
    """THE artifact. Fountain and PDF are lossy projections of this."""
    title: str
    source_work: str
    target: str
    source_fingerprint: str
    spine: str = ""
    logline: str = ""
    scenes: list[Scene] = Field(default_factory=list)
    omitted: list[Omission] = Field(default_factory=list)
    totals: Totals
