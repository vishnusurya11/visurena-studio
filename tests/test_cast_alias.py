"""cast_alias: a plan's epithet ("the lawyer") binds to the staged person it tags.

Jekyll ep01 iter4 (audit 2026-10-15, 02_prompts.md T4/G4): 18 takes never cited a
staged <Subject k>; "the lawyer (long, gaunt ...)" rode beside "<Subject 1> is Mr.
Utterson", one person told to the model twice (the ep16 duplicate class)."""
from studio import cast_alias as ca

ROWS = {
    "gabriel_john_utterson": "lank grey hair long gaunt rugged unsmiling face black bowler hat long black overcoat",
    "edward_hyde": "soft black felt wideawake hat small slight narrow-shouldered frame clean-shaven pale smooth cheeks",
    "child_of_hyde_incident": "fair hair in two plaits small soft grey woollen bonnet plain grey pinafore dress and black boots",
    "richard_enfield": "receding brown hair light-brown top hat mid-grey long coat",
}


def test_tags_in_reads_said_and_fragments():
    text = "a wide of the lawyer (long, gaunt, rugged, unsmiling face, black bowler hat) and Mr. Enfield (light-brown top hat)"
    got = ca.tags_in(text)
    assert got[0] == ("the lawyer", ["long", "gaunt", "rugged", "unsmiling face", "black bowler hat"])
    assert got[1][0] == "Mr. Enfield"


def test_owner_of_picks_the_row_saying_most_fragments():
    assert ca.owner_of(["black bowler hat", "long"], ROWS) == "gabriel_john_utterson"
    assert ca.owner_of(["fair hair in two plaits", "small knitted woollen bonnet"], ROWS) == "child_of_hyde_incident"


def test_owner_of_none_when_no_fragment_matches_or_tie():
    assert ca.owner_of(["a red parasol"], ROWS) is None
    assert ca.owner_of(["hat"], {"a": "hat", "b": "hat"}) is None


def test_aliases_collects_epithets_per_person():
    texts = ["the lawyer (black bowler hat) turns", "the little man (soft black felt wideawake hat) walks",
             "the girl (fair hair in two plaits) runs", "the lawyer (long, gaunt) nods"]
    got = ca.aliases(texts, ROWS)
    assert got == {"gabriel_john_utterson": ["the lawyer"], "edward_hyde": ["the little man"],
                   "child_of_hyde_incident": ["the girl"]}


def test_aliases_drop_a_phrase_two_people_share():
    texts = ["the man (black bowler hat)", "the man (soft black felt wideawake hat)"]
    assert ca.aliases(texts, ROWS) == {}


def test_bind_replaces_epithet_and_drops_its_parenthetical():
    text = "the little man (clean-shaven, pale smooth cheeks) lifts his chin; the little man's pale face"
    got = ca.bind(text, {"edward_hyde": "<Subject 1>"}, {"edward_hyde": ["the little man"]})
    assert got == "<Subject 1> lifts his chin; <Subject 1>'s pale face"


def test_bind_is_case_blind_at_a_sentence_start():
    got = ca.bind("The lawyer nods.", {"u": "<Subject 2>"}, {"u": ["the lawyer"]})
    assert got == "<Subject 2> nods."


def test_bind_leaves_an_unstaged_person_alone():
    text = "the girl (fair hair in two plaits) runs"
    assert ca.bind(text, {"edward_hyde": "<Subject 1>"}, {"child_of_hyde_incident": ["the girl"]}) == text


def test_strip_labelled_drops_a_parenthetical_after_any_label():
    text = "<Subject 2> (light-brown top hat, fashionable dark frock coat) and <Subject 1> walk"
    assert ca.strip_labelled(text) == "<Subject 2> and <Subject 1> walk"


def test_strip_labelled_keeps_a_parenthetical_that_is_not_after_a_label():
    assert ca.strip_labelled("a cheque (folded) and <Subject 1>") == "a cheque (folded) and <Subject 1>"


def test_strip_labelled_keeps_the_grammars_own_parentheticals():
    text = "<Subject 1> (S1), on screen, says: and <Subject 2> (the man in [Shot 1]): kept"
    assert ca.strip_labelled(text) == text
