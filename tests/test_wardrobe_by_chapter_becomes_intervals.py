"""WotW's dossiers already carry a costume plot (`profile.wardrobe` +
`wardrobe_by_chapter`).  `looks_from_dossier` reads it as the look table:
one look per wardrobe key, a span where the chapter's look changes, a look
that returns gets a second span, a chapter with no entry keeps the last look."""
from __future__ import annotations

from studio import look_timeline as lt

CARD = {"id": "narrator", "profile": {
    "physical": "Man of 34, grey eyes. Dark brown hair cut short. Neat dark brown moustache; shaven chin.",
    "wardrobe": {"day_suit": "Mid-grey tweed lounge suit. Straw boater with a black band.",
                 "flight_hatless": "Mid-grey tweed suit, torn. Bareheaded, dark hair tousled.",
                 "ragged_greyed": "Torn flannel shirt, battered brown felt hat. Hair turned ash-grey; "
                                  "sixteen days of grey-brown beard."},
    "wardrobe_by_chapter": {"1": "day_suit", "2": "day_suit", "7": "flight_hatless", "8": "day_suit",
                            "22": "ragged_greyed", "23": "ragged_greyed"}}}


def test_every_chapter_resolves_as_wardrobe_state_did():
    looks = lt.looks_from_dossier(CARD)
    assert [looks.look_id_at(n) for n in (1, 6, 7, 8, 16, 22, 27)] == \
        ["day_suit", "day_suit", "flight_hatless", "day_suit", "day_suit", "ragged_greyed", "ragged_greyed"]


def test_the_base_is_the_first_chapters_look_and_the_body_has_no_head():
    looks = lt.looks_from_dossier(CARD)
    assert looks.base == "day_suit" and looks.looks["day_suit"].made_by == "base"
    assert "hair" not in looks.body and "moustache" not in looks.body


def test_a_face_changing_look_is_marked_so():
    looks = lt.looks_from_dossier(CARD)
    assert looks.looks["ragged_greyed"].face_change and not looks.looks["flight_hatless"].face_change
    assert looks.looks["ragged_greyed"].markers.facial_hair == "beard"


def test_a_dossier_without_a_costume_plot_gives_none():
    assert lt.looks_from_dossier({"profile": {"physical": "A man."}}) is None


def test_every_look_carries_a_whole_head_and_its_words_lead_with_it():
    looks = lt.looks_from_dossier(CARD)
    assert "Dark brown hair" in looks.looks["day_suit"].layers.hair
    words = lt.look_words(looks, "ragged_greyed")
    assert words.startswith("Hair turned ash-grey") and "Dark brown" not in words
    assert words.index("Man of 34") < words.index("Wearing:")
    assert "moustache" in lt.look_words(looks, "day_suit")
