r"""A character's name may carry an epithet, and the epithet is not an alias.

MEASURED, episode 8. The bible row for Lucy at five was named

    "Lucy Ferrier, aged five"

and `name_map` takes `name.split()[-1]` as an alias, so the token **"five"**
became a name that identifies her. Shot 21's staging reads

    "A gaunt bearded man in a dark velveteen tunic stands ... , a girl of FIVE
     in a pink frock stands at his hip ..."

so `named_in` found exactly one character in it -- her -- and `crossed_mark`,
which answers only when the prose names exactly one man, reported that Lucy was
wearing John Ferrier's velveteen tunic. The mark gate refused a correct plan,
and the reason was a word that means a number.

Ferrier is not named in that sentence at all: he is "a gaunt bearded man". So
the one token the matcher did find decided the whole verdict.

A COMMA IN A CHARACTER'S NAME SEPARATES THE NAME FROM A DESCRIPTION. "Lucy
Ferrier, aged five" is a person and an epithet, and the last word of the epithet
is not what anybody calls her. That is the rule, and it is not a stoplist: a
stoplist would need to know that "five" is a number and "Wiggins" is not.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from studio import episode_spec as es


def row(entity, name, **extra):
    return dict(kind="character", entity_id=entity, name=name, **extra)


def test_the_epithet_supplies_no_alias():
    names = es.name_map([row("lucy_child", "Lucy Ferrier, aged five")])
    assert "five" not in names
    assert "aged five" not in names


def test_the_real_name_still_does():
    names = es.name_map([row("lucy_child", "Lucy Ferrier, aged five")])
    assert names.get("ferrier") == "lucy_child"
    assert names.get("lucy ferrier, aged five") == "lucy_child"


def test_a_plain_name_keeps_its_surname_alias():
    names = es.name_map([row("wiggins", "Wiggins")])
    assert names.get("wiggins") == "wiggins"


def test_a_plain_two_word_name_is_unchanged():
    names = es.name_map([row("g_lestrade", "Inspector Lestrade")])
    assert names.get("lestrade") == "g_lestrade"


def test_the_shot_that_was_refused_now_names_both_men():
    """The real staging, verbatim from episode 8 shot 21."""
    refs = [row("john_ferrier", "John Ferrier", marks=["velveteen tunic"]),
            row("lucy_ferrier_child", "Lucy Ferrier, aged five", marks=["pink frock"])]
    names = es.name_map(refs)
    said = ("A gaunt bearded man in a dark velveteen tunic stands at the CENTRE of frame "
            "facing the camera, a girl of five in a pink frock stands at his hip")
    assert es.named_in(said, names) == [], (
        "neither man is NAMED in this sentence -- they are described, so the mark "
        "gate must not measure it at all")


def test_a_number_word_cannot_become_a_character():
    for said in ("Lucy Ferrier, aged five", "John Ferrier, about sixty",
                 "A boy, about thirteen"):
        names = es.name_map([row("who", said)])
        tail = said.split()[-1].lower()
        assert tail not in names, f"{tail!r} became a name from {said!r}"
