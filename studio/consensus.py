"""Agreement between independent judges. Zero LLM — this is the arithmetic only.

The point of asking several judges the same question is that their agreement means
something. It only means something if they answered INDEPENDENTLY, which is the agent's
job, and if the two questions their answers support are kept apart, which is this
module's:

  * do the judges agree with EACH OTHER?  -> is this scene knowable from the text at all
  * do they agree with the PIPELINE?      -> is the pipeline right

Conflating those wastes the exercise. A scene where judges split is not a pipeline bug -
it is a scene the book declines to place. The only combination that is definitely a bug
is unanimous judges disagreeing with the pipeline.
"""

from __future__ import annotations

from collections import Counter

# Answers that are ABOUT the question rather than answers to it.
ABSTAIN = "ambiguous"
UNLISTED = "unlisted"


def agreement(answers: list[str]) -> dict:
    """How much the judges agree, and on what.

    A strict majority is required — two against two is not agreement, however tempting
    the arithmetic.
    """
    if not answers:
        return {"level": "none", "answer": None, "counts": {}, "judges": 0}
    counts = Counter(answers)
    top, top_n = counts.most_common(1)[0]
    if top_n == len(answers):
        level = "unanimous"
    elif top_n * 2 > len(answers):
        level = "majority"
    else:
        level = "split"
    return {"level": level,
            "answer": top if level != "split" else None,
            "counts": dict(counts),
            "judges": len(answers)}


def verdict(answers: list[str], pipeline_location: str | None) -> dict:
    """What the judges say about the pipeline's choice for one scene."""
    found = agreement(answers)
    result = {**found, "pipeline": pipeline_location, "should_be": None}

    if found["level"] == "none":
        return {**result, "verdict": "no_judges"}
    if found["answer"] == ABSTAIN:
        # The text does not place this scene. That is a fact about the BOOK.
        return {**result, "verdict": "unknowable"}
    if found["answer"] == UNLISTED:
        # A real place the registry lacks. A finding about the registry, not the scene.
        return {**result, "verdict": "registry_gap"}
    if found["level"] == "split":
        return {**result, "verdict": "unknowable"}
    if found["answer"] == pipeline_location:
        return {**result, "verdict": "confirmed"}
    return {**result,
            "verdict": "wrong" if found["level"] == "unanimous" else "disputed",
            "should_be": found["answer"]}


# Scenes the book does not place cannot count for or against the pipeline.
DECIDABLE = ("confirmed", "wrong", "disputed")


def summarise(rows: list[dict]) -> dict:
    """Counts per verdict, plus a confirmation rate over DECIDABLE scenes only."""
    counts = Counter(row["verdict"] for row in rows)
    decidable = sum(counts[k] for k in DECIDABLE)
    return {**{k: counts.get(k, 0) for k in
               ("confirmed", "wrong", "disputed", "unknowable",
                "registry_gap", "no_judges")},
            "scenes": len(rows),
            "decidable": decidable,
            "confirmed_rate": (counts.get("confirmed", 0) / decidable
                               if decidable else 0.0)}
