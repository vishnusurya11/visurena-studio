"""C3_verdict #9: the hair colour is the colour next to "hair".

The look table took the FIRST colour word anywhere in the hair layer, in table
order (grey, white, bald, red ...): WotW's Gregg ("Sandy-ginger hair cut short
around a bald crown") read bald, Mary Lennox ("thicker-looking hair, and red
in her cheeks") read red, and "grey eyes under sandy hair" read grey.  Now the
adjective next to hair/haired decides; a grey modifier in the hair clause
("greying", "threaded with grey") keeps grey; sandy is fair; every colour word
has its word boundary ("towards" is not tow, "affair" is not fair)."""
from __future__ import annotations

import pytest

from studio import look_table as lt


@pytest.mark.parametrize("text, colour", [
    ("Sandy-ginger hair cut short around a bald crown.", "red"),                        # Gregg
    ("with hair lying flat against her head. thicker-looking hair, and red in her cheeks", ""),  # Lennox
    ("Grey eyes under sandy hair.", "fair"),
    ("Light brown hair threaded with grey, worn in a smooth bun at the crown.", "grey"),  # Mrs Elphinstone
    ("Thick auburn hair greying at the temples, brushed straight back.", "grey"),        # Ogilvy
    ("Brown hair flecked with grey, thinning on the crown and brushed flat.", "grey"),   # the landlord
    ("Thick near-black hair worn in a low coiled chignon at the nape.", "dark"),         # Miss Elphinstone
    ("A red-haired boy.", "red"),
    ("Bald.", "bald"),
    ("Long flaxen ringlets.", "fair"),
    ("Hair turned ash-grey throughout and grown shaggy over the ears.", "grey"),          # WotW narrator, late
    ("Black hair hanging over the eyes, red cut across the chin and jaw.", "dark"),      # a cut is not hair                                       # no hair noun: first-of
])
def test_the_colour_next_to_hair_decides(text, colour):
    assert lt.hair_colour(text) == colour


def test_colour_words_have_their_boundaries():
    assert lt.first_of(lt.HAIR, "he walked towards the door") == ""
    assert lt.first_of(lt.HAIR, "a sorry affair") == ""
    assert lt.first_of(lt.HAIR, "a darkened room") == ""


def test_the_markers_read_the_adjacent_colour():
    assert lt.markers_of("Sandy-ginger hair cut short around a bald crown.", "")["hair_colour"] == "red"
