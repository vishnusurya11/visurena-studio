r"""The card framing gate was calibrated on six men in trousers.

`hands_clear` asks whether the bottom OUTER THIRDS of a wardrobe card are
backdrop, because "hands hang OUTBOARD and legs run CENTRAL". Its own
calibration table is six cards, and every one of them is a man in a jacket and
trousers:

    g_lestrade 0.320 · john_rance 0.155 · john_watson 0.112
    sherlock_holmes 0.151 · tobias_gregson 0.140 · marine_sergeant 0.640

A floor-length Victorian dress is WIDE AT THE HEM. It fills the outer thirds of
the bottom edge because that is what the garment does, with both hands plainly
inside the frame and nothing cut off at all. Measured on the two such cards on
disk:

    madame_sawyer_indoor    0.843      madame_charpentier_indoor  0.736
    madame_sawyer_outdoor   0.812

Every woman in period dress this production will ever draw fails a gate whose
question -- "is a hand running off the frame?" -- is answered NO in all three
pictures. That is the shape of a gate that gets commented out: it is not wrong
about its threshold, it is being asked of a picture it cannot read.

So the instrument declares where it does not apply. A row whose own `garments`
contract says the dress reaches the floor is not measured by the outer thirds,
and the report says which rule stood down rather than silently passing -- an
unmeasured check that reads as a pass is the fault class this repo has found
thirteen times.

THE GATE IS NOT WEAKENED FOR MEN. The six-card calibration stands exactly as it
was, and a man whose hand runs off the frame still fails.
"""
import pytest

from studio.cast_agree import FLOOR_LENGTH, floor_length


def test_a_full_length_dress_is_recognised():
    said = ("She wears a high-necked black bombazine dress buttoned to the throat; the key "
            "light falls a stop brighter on the bodice than on the backdrop.")
    assert floor_length({"sheet": {"garments": said}}) is True


def test_a_long_dark_skirt_to_the_boot_is_recognised():
    """Mrs Sawyer's own wardrobe line."""
    row = {"wardrobe": {"indoor": "is in a black straw bonnet tied under the chin, a brown "
                                  "shawl crossed over her chest, and a long dark skirt to "
                                  "the boot, with both hands bare"}}
    assert floor_length(row) is True


def test_a_man_in_trousers_is_not():
    said = ("He wears a dark green hunting jacket over a black silk scarf; the key light "
            "falls a stop brighter on the jacket than on the backdrop.")
    assert floor_length({"sheet": {"garments": said}}) is False


def test_watsons_overcoat_is_not_a_skirt():
    """A long coat is still worn over trousers and still leaves the corners."""
    row = {"wardrobe": {"outdoor": "wears a brown tweed overcoat open over the waistcoat and "
                                   "its watch chain, and a black bowler set square"}}
    assert floor_length(row) is False


def test_an_empty_row_is_not():
    assert floor_length({}) is False
    assert floor_length({"sheet": {}, "wardrobe": {}}) is False


def test_the_vocabulary_is_about_length_not_about_women():
    """A cassock, a greatcoat to the ankle and a nightgown reach the floor too;
    the rule is the garment's hem, never who wears it."""
    for said in ("a black cassock to the floor", "a grey greatcoat to the ankle",
                 "a white nightgown to the instep", "a long skirt to the boot"):
        assert floor_length({"sheet": {"garments": said}}) is True, said


def test_the_pattern_is_anchored_to_a_hem_word():
    """`to the floor` inside "the light falls to the floor" is lighting, not a
    hem, so the garment word has to be there too."""
    assert floor_length({"sheet": {"garments": "the key light spills to the floor"}}) is False


# ---- and the report says it stood down -------------------------------------

def test_the_complaint_is_not_raised_for_a_floor_length_row(tmp_path, monkeypatch):
    from studio import cast_agree

    monkeypatch.setattr(cast_agree, "hands_clear", lambda *a, **k: False)
    monkeypatch.setattr(cast_agree, "plain_backdrop", lambda *a, **k: True)
    monkeypatch.setattr(cast_agree, "bottom_share", lambda *a, **k: 0.736)
    monkeypatch.setattr(cast_agree, "detector", lambda: None)
    card = tmp_path / "char-x_indoor.png"
    card.write_bytes(b"x")
    row = {"sheet": {"garments": "a long dark skirt to the boot"}}
    got = cast_agree.picture_complaints(card, "card", row=row)
    assert not any("runs off the frame" in c for c in got)


def test_a_man_still_fails_it(tmp_path, monkeypatch):
    from studio import cast_agree

    monkeypatch.setattr(cast_agree, "hands_clear", lambda *a, **k: False)
    monkeypatch.setattr(cast_agree, "plain_backdrop", lambda *a, **k: True)
    monkeypatch.setattr(cast_agree, "bottom_share", lambda *a, **k: 0.64)
    monkeypatch.setattr(cast_agree, "detector", lambda: None)
    card = tmp_path / "char-y_indoor.png"
    card.write_bytes(b"y")
    row = {"sheet": {"garments": "a dark green hunting jacket over a black silk scarf"}}
    got = cast_agree.picture_complaints(card, "card", row=row)
    assert any("runs off the frame" in c for c in got)


def test_no_row_at_all_still_measures():
    """The default must be to ASK, never to stand down."""
    assert FLOOR_LENGTH.search("a long dark skirt to the boot")
    assert not floor_length(None)
