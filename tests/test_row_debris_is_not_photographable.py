"""Row debris never reaches a Subject definition (Jekyll ep01 iter4 audit T10)."""
from studio.trailer_refs import is_photographable


def test_a_biography_sentence_with_an_appearance_word_is_refused():
    assert not is_photographable("A small or little man, repeatedly described as shorter and lighter than Henry Jekyll.")
    assert not is_photographable("He is associated with respectable clothing and access to Jekyll's house, a furnished Soho residence.")
    assert not is_photographable("He is presented as a gentleman who walks regularly with Utterson.")


def test_a_cut_sentence_is_refused():
    assert not is_photographable("A lean, long, bony, dry man of about forty, younger than Jekyll, narrow-chested, with a long.")


def test_a_plain_appearance_sentence_still_passes():
    assert is_photographable("A lean, long, bony, dry man of about forty, narrow-chested.")
