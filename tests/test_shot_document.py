"""The lean Ref2V document: the SUBJECT dominates, not the boilerplate.

MEASURED on the first script-driven render, and the reason its pictures were
wrong.  B08's prompt ran 1009 words and said "pills" twice.  303 of those
words were byte-identical across all eighteen prompts -- generic light,
parallax, materials, performance and continuity -- and ~150 more re-described
Holmes' face in prose while the reference IMAGE was already carrying it.  B05
went further and contradicted itself: "the shot holds an EMPTY 3 Lauriston
Gardens" followed by "a gloved hand lifting a pill", plus "the shadowed side
of the FACE keeps visible detail" in a shot with no face.  Handed that, the
model rendered the boilerplate and invented plausible table objects: candles.
"""
from __future__ import annotations

from studio import shot_document as doc

HOLMES = ("A lean man in his late twenties, over six feet, pale, hawk-nosed, "
          "dark hair swept back, a tweed deerstalker and a checked muffler")
ROOM = "A cluttered first-floor sitting room, bow window, gaslight"
LOOK = "Muted soot-black and gaslight amber, 1881 London, fog and deep shadow"


def a_doc(**kw) -> str:
    fields = {"style": LOOK, "character": HOLMES, "place": ROOM,
              "subject": "two identical pills on a table",
              "action": "Holmes sets two identical pills on the table and lifts a scalpel.",
              "open_framing": "A medium-wide of the table, lamp behind.",
              "close_framing": "An extreme close-up of the two pills.",
              "camera": "A slow push from the table's edge onto the pills.",
              "seconds": 3.0}
    fields.update(kw)
    return doc.build(**fields)


class TestTheSubjectWins:
    def test_the_subject_is_named_first_and_named_again_at_the_close(self):
        """"pills" appeared twice in 1009 words.  The thing the shot is OF has
        to open the description and end it."""
        body = a_doc().split("detailed_description:")[1]
        first = body.strip().lower()
        assert first.startswith("two identical pills on a table")
        assert "two identical pills" in first[-400:]

    def test_the_subject_outweighs_what_every_shot_shares(self):
        """Two documents for different subjects must differ more than they
        agree.  At 303 shared words out of 1009 the model was reading the
        boilerplate."""
        pills = a_doc()
        street = a_doc(character="", subject="a hansom cab in fog",
                       action="A hansom cuts through the fog toward the kerb.",
                       open_framing="A low wide from the kerb, lamps beyond.",
                       close_framing="A tight pass of the wheel through water.",
                       camera="A locked-off hold as the cab crosses frame.",
                       place="a fogged street")
        shared = set(pills.split(". ")) & set(street.split(". "))
        assert sum(len(s.split()) for s in shared) < 60

    def test_the_template_costs_little_of_the_document(self):
        """The number to hold down is the TEMPLATE's own share, because that is
        what every shot pays whatever it is of.  The old builder spent 303
        identical words in every prompt; anything the shot list writes then had
        to outweigh that.  Width should come from richer action and framing,
        never from padding the template."""
        bare = doc.build(style="S", character="C", place="P", subject="x", action="y.",
                         open_framing="a", close_framing="b", camera="c", seconds=3.0)
        overhead = bare.split("detailed_description:")[1].split("overall_soundscape:")[0]
        assert len(overhead.split()) <= 130            # was 303
        assert len(a_doc().split()) <= 500             # whole document; B08 was 1009


class TestNoContradictions:
    def test_a_shot_with_a_hand_in_it_is_never_called_empty(self):
        """B05: "the shot holds an EMPTY room" and "a gloved hand lifting a
        pill", in the same paragraph."""
        body = a_doc(character="", subject="a gloved hand lifting a pill",
                     action="A gloved hand reaches into frame and lifts a pill.")
        assert "empty" not in body.lower()

    def test_a_shot_with_nobody_in_it_may_still_say_the_room_is_empty(self):
        body = a_doc(character="", subject="the empty hallway",
                     action="Fog moves through the hallway; nothing else stirs.")
        assert "only occupants" in body.lower() or "empty" in body.lower()

    def test_a_faceless_shot_does_not_light_a_face(self):
        """"the shadowed side of the face keeps visible detail" was in every
        prompt, including the ones with no face."""
        body = a_doc(character="", subject="two identical pills on a table",
                     action="A hand sets two pills down on the table.")
        assert "shadowed side of the face" not in body.lower()
        assert "raking across the hands" in body.lower()

    def test_a_shot_with_a_bound_face_still_lights_the_face(self):
        assert "face" in a_doc().lower()


class TestItIsStillTheSpec:
    def test_every_named_section_is_present_and_in_order(self):
        text = a_doc()
        found = [s for s in doc.SECTIONS if f"{s}:" in text]
        assert found == list(doc.SECTIONS)
        assert text.index("summary:") < text.index("detailed_description:")

    def test_the_identity_is_bound_by_label_not_retold_in_prose(self):
        """The reference IMAGE carries the face; 150 words re-describing it
        only competed with the action for the model's attention."""
        text = a_doc()
        assert "<Subject 1>" in text and "fully_preserved" in text
        assert text.count("hawk-nosed") == 1
