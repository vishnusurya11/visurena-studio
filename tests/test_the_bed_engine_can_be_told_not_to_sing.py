"""The default bed engine is the one that HAS an instrumental control.

MEASURED by reading the node source, 2026-09-14, after YuE2 sang on three
separate beds (episode 3's shipped master, and both of episode 4's):

  * YuE2's token vocabulary has no vocal/instrumental token at all
    (`_vendor/yue2/tokenization_yue2.py:16-18`), and `encode_ordinary` means an
    `[inst]`-style string is encoded as literal TEXT, never as a control.
  * `SongRequest.text()` (`_vendor/yue2/protocol.py:108`) interpolates lyrics
    unconditionally, so an empty field yields a `[Lyrics]` header with a blank
    line under it -- an UNFILLED SLOT, not an instruction.
  * With `cot='full'` the plan stage writes a chord-annotated ABC score whose
    melody line IS the vocal line, and the semantic stage then improvises
    syllables over it.  That is why the two refused beds were phoneme scat --
    one pseudo-English, one pseudo-Japanese -- rather than actual verse.
  * `guidance` returns exactly 1.0 for `cot='full'` (`protocol.py:106`), so the
    negative branch is never built and CFG has been OFF on every bed ever
    generated.
  * The word "instrumental" occurs once in the entire node pack: a tooltip
    string on the lyrics input.  `assemble.py` chose the olmpack pipeline
    BECAUSE of that tooltip.  A tooltip is not a mechanism.

ACE-Step has both halves: `[inst]` is a trained control string in its lyric
encoder, its tags field says instrumental too, and it runs real CFG at 2.0
against a zeroed negative.  So `[inst]` is a lever and `""` is the absence of
one.  Episodes 1, 2 and 4 shipped silent beds on ACE-Step.

The owner's preference for YuE2 was about STYLE CONTROL and it is correct --
YuE2 does have better style control.  It simply cannot be told not to sing.
`--bed=yue2` stays reachable.
"""
import inspect

from scripts.episode import assemble


def test_the_default_engine_is_the_one_with_a_control():
    assert assemble.BED_ENGINE_DEFAULT == "acestep"


def test_yue2_is_still_reachable():
    assert "yue2" in assemble.BED_INSTRUMENTAL


def test_the_reason_is_recorded_as_a_mechanism_not_an_outcome():
    said = inspect.getsource(assemble)
    assert "tokenization_yue2" in said and "no vocal" in said.lower()


def test_a_yue2_bed_asks_for_the_length_it_needs():
    """`bed_request` takes `seconds` and the yue2 branch DISCARDED it.
    `semantic_max_tokens` is the duration control at 25 tokens a second, it is
    injectable, and nobody was setting it -- so the bed's length had no relation
    to the runtime asked for."""
    _, values = assemble.bed_request("yue2", 150.0, 90105)
    assert values["semantic_max_tokens"] >= 150 * assemble.YUE2_TOKENS_PER_S


def test_a_longer_episode_asks_for_more_tokens():
    _, short = assemble.bed_request("yue2", 100.0, 1)
    _, long = assemble.bed_request("yue2", 300.0, 1)
    assert long["semantic_max_tokens"] > short["semantic_max_tokens"]


def test_the_token_ask_is_capped_at_what_the_model_can_do():
    """9000 tokens / 25 fps = 360 s is the model's own ceiling."""
    _, values = assemble.bed_request("yue2", 10_000.0, 1)
    assert values["semantic_max_tokens"] <= 9000


def test_acestep_still_gets_its_seconds():
    _, values = assemble.bed_request("acestep", 150.0, 1)
    assert values["seconds"] == 150.0 and values["lyrics"] == "[inst]"
