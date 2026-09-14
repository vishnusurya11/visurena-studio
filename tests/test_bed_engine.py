"""The episode's music bed, and which model makes it.

The bed is NOT new -- every episode has had one since ep01 (`audio/bed.wav`,
ACE-Step 1.5, 11 dB under the voice, ducked, room tone beneath). It was
invisible because the skill documented it in half a line inside a sentence
about `assemble.py`, so this names it as its own stage.

YuE2 is installed beside it (`yue2_3b_bf16.safetensors`, `audio_yue2_song`),
and the one thing it offers that ACE-Step does not is an ABC score: the plan
can be generated, EDITED and then synthesised, which is how fourteen episodes
could share a motif instead of fourteen unrelated drones. Whether it sounds
better is an A/B nobody has run, so ACE-Step stays the default.

THE INSTRUMENTAL MARKER IS NOT THE SAME WORD. ACE-Step takes `[inst]`; YuE2
takes `(instrumental)` -- measured on the trailer (`music_tone`), where a
parenthetical is otherwise read as a SUNG backing line and three delivered
cues came back singing their own stage directions.
"""
import importlib.util
import sys

import pytest

spec = importlib.util.spec_from_file_location("ep_assemble", "scripts/episode/assemble.py")
asm = importlib.util.module_from_spec(spec)
sys.modules["ep_assemble"] = asm
spec.loader.exec_module(asm)


def test_the_default_engine_is_the_one_that_can_be_told_not_to_sing():
    """The owner asked for YuE2 and he is right about its style control.  It has
    no instrumental control of any kind, and that is a mechanism, not a bad run:
    no vocal token exists in its vocabulary, `encode_ordinary` makes any
    `[inst]`-style string literal text, an empty `lyrics` yields an UNFILLED SLOT
    rather than an instruction, and `guidance` returns exactly 1.0 for
    `cot="full"` so CFG has been off on every bed ever generated.  Three YuE2
    beds have sung.  ACE-Step has a trained control string AND real CFG against a
    zeroed negative; episodes 1, 2 and 4 shipped silent on it.  `--bed=yue2`
    stays reachable."""
    assert asm.BED_ENGINE_DEFAULT == "acestep"
    assert "yue2" in asm.BED_INSTRUMENTAL


def test_acestep_asks_with_its_own_instrumental_marker():
    name, values = asm.bed_request("acestep", 171.0, 90003)
    assert name == "audio_acestep15_music"
    assert values["lyrics"] == "[inst]"
    assert values["seconds"] == 171.0 and values["duration"] == 171.0
    assert values["bpm"] == 60 and values["keyscale"] == "D minor"
    assert values["seed"] == values["lm_seed"] == 90003


def test_yue2_uses_the_workflow_THAT_DOCUMENTS_AN_INSTRUMENTAL():
    """Third answer, and this one is the node's own.

    `audio_yue2_song` drives `YuE2GenerateMusic`, whose lyrics field promises
    nothing: given `(instrumental)` it sang invented verse (64 % of ep03's bed),
    and given "" it sang again -- "winter silence i am hating ... ah ah ah".
    Both were caught, the second by the gate.

    `OlmYuE2Request.lyrics` carries a TOOLTIP reading "Leave empty for
    instrumental music", and this module chose the `audio_yue2_song_olmpack`
    pipeline because of it.  A tooltip is not a mechanism: the word
    "instrumental" appears exactly once in the whole node pack, in that string,
    and is implemented nowhere.

    THE JUSTIFICATION THIS DOCSTRING USED TO GIVE FOR `cot="full"` -- "the vendor
    guidance says to leave it at full so the model has an arrangement to build
    without words to sing" -- CITES A SOURCE THAT DOES NOT EXIST.  Nothing in the
    pack, its README, its four example workflows or the vendored upstream
    recommends a `cot` setting for an instrumental.  And the reasoning is
    inverted: `cot="full"` is what makes the plan stage write a chord-annotated
    TRANSCRIPTION whose melody line is baked into the semantic prefix, so the
    semantic stage improvises syllables over a prescribed lead.  "An arrangement
    to build without words to sing" is a precise description of how you get scat
    singing, which is what both refused beds were.

    This is the same fault `BED_INSTRUMENTAL` warns about one layer up -- a
    plausible sentence credited to a source never consulted -- repeated in the
    test that was supposed to catch it.  The value is left at `full` because
    changing it is a twenty-minute GPU experiment nobody has run, not because
    anyone recommends it."""
    name, values = asm.bed_request("yue2", 171.0, 90003)
    assert name == "audio_yue2_song_olmpack"
    assert values["lyrics"] == ""
    assert values["cot"] == "full"
    assert values["seed"] == 90003


def test_yue2_gets_style_PROSE_not_acesteps_tag_list():
    _n, values = asm.bed_request("yue2", 100.0, 1)
    assert values["style"] == asm.BED_STYLE


def test_the_olmpack_request_carries_one_seed():
    """The olmpack graph plans, samples and synthesises from one request, so
    there is a single seed rather than three to keep in step."""
    _n, values = asm.bed_request("yue2", 100.0, 4242)
    assert values["seed"] == 4242


def test_an_unknown_engine_is_refused_by_name():
    with pytest.raises(ValueError, match="bed engine"):
        asm.bed_request("suno", 100.0, 1)


def test_both_engines_name_the_same_output_prefix():
    """`bed()` copies the first output; the prefix is what finds it."""
    for engine in ("acestep", "yue2"):
        assert asm.bed_request(engine, 100.0, 1)[1]["filename_prefix"] == "ep_bed"


# ---- the level must be MEASURED, not inherited from another model -----------

def test_the_bed_target_sits_well_under_the_lines():
    """Lines are laid at -16 LUFS. ACE-Step's raw bed measured -14.6 LUFS --
    LOUDER than the voice -- and -11 dB put it at -25.6. That -25.6 is the
    number that two shipped episodes were judged at, so it is the target, and
    the GAIN to reach it is whatever this model happens to need."""
    assert asm.BED_TARGET_LUFS == -25.6


def test_the_gain_is_derived_from_the_bed_that_was_actually_made():
    """A fixed -11 dB is only right for a bed that arrives at -14.6."""
    assert asm.bed_gain_db(-14.6) == pytest.approx(-11.0, abs=0.05)
    assert asm.bed_gain_db(-20.0) == pytest.approx(-5.6, abs=0.05)
    assert asm.bed_gain_db(-30.0) == pytest.approx(4.4, abs=0.05)


def test_a_silent_or_unmeasurable_bed_falls_back_rather_than_exploding():
    """-inf LUFS on a dead file would ask for infinite gain."""
    assert asm.bed_gain_db(float("-inf")) == asm.BED_TRIM_DB
    assert asm.bed_gain_db(None) == asm.BED_TRIM_DB


def test_the_lift_is_capped_so_a_quiet_bed_cannot_be_amplified_into_noise():
    """A bed 30 LU down is a failed generation, not something to crank."""
    assert asm.bed_gain_db(-60.0) == asm.BED_MAX_LIFT_DB


# ---- the bed must COVER the cut, whatever length the model felt like --------

def test_max_duration_is_a_cap_so_a_short_bed_is_expected():
    """MEASURED 2026-09-13: asked YuE2 for 172 s, got 157.8 s for a 162 s cut --
    4.2 s of the episode with no bed under it. The node's own tooltip says
    "generation can stop earlier", and `trailer_music` learned the same thing on
    seven cues that ended by themselves at 101.9-146.8 s under a 150 s cap. A
    bed is covered by LOOPING it, never by asking again and hoping."""
    assert asm.loops_for(157.8, 162.0) == 2
    assert asm.loops_for(157.8, 300.0) == 2      # 2 passes cover 315.6 s
    assert asm.loops_for(172.0, 162.0) == 1      # already long enough
    assert asm.loops_for(50.0, 162.0) == 4


def test_a_bed_exactly_long_enough_is_not_looped():
    assert asm.loops_for(162.0, 162.0) == 1


def test_a_bed_of_no_length_does_not_divide_by_zero():
    assert asm.loops_for(0.0, 162.0) == 1
    assert asm.loops_for(None, 162.0) == 1


def test_a_short_bed_is_kept_rather_than_thrown_away(tmp_path):
    """Deleting it bought a four-minute regeneration that can come back short
    again. The file is the expensive part; covering the cut is free."""
    assert asm.bed_is_usable(157.8, 162.0)
    assert asm.bed_is_usable(200.0, 162.0)
    assert not asm.bed_is_usable(0.0, 162.0)
    assert not asm.bed_is_usable(None, 162.0)


# ---- YuE2 has NO instrumental token: the lyrics field must be EMPTY ---------

def test_yue2_gets_EMPTY_lyrics_not_a_marker():
    """MEASURED 2026-09-13: ep03's bed sang invented English verse for 101 of its
    157.8 s -- 64% -- confirmed by two Whisper models agreeing word-for-word and
    by 5-27x the consonant energy in exactly those windows at equal loudness.

    The cause was mine. `(instrumental)` was measured on MiniMax Music 3 (the
    TRAILER's engine, `music_tone`), and I wrote into this module's docstring
    that it had been measured on YuE2. It had not. YuE2 has no instrumental
    token: its documentation says the lyrics field must be EMPTY -- not
    `[Instrumental]`, not a section tag without words. Given any lyric-shaped
    string it writes a song to fit."""
    _name, values = asm.bed_request("yue2", 171.0, 1)
    assert values["lyrics"] == ""


def test_acestep_keeps_its_own_token_which_is_verified():
    """`[inst]` is ACE-Step's own, and two shipped episodes came back silent."""
    assert asm.bed_request("acestep", 171.0, 1)[1]["lyrics"] == "[inst]"


def test_the_style_never_names_a_voice_even_to_forbid_one():
    """"without vocal descriptors, otherwise the model still adds a voice."
    A negation is not a fence -- MiniMax cannot read one at all, and YuE2 reads
    `no choir` as a choir. The style now describes only what should be heard."""
    import re
    # WORD boundaries: "single piano notes" contains "sing", and that is the
    # style doing its job, not naming a voice.
    for word in ("vocal", "vocals", "voice", "choir", "sings", "singer", "singing", "lyric"):
        assert not re.search(rf"{word}", asm.BED_STYLE, re.I), word


def test_the_style_still_says_what_the_bed_IS():
    for word in ("cello", "minor", "60 BPM"):
        assert word in asm.BED_STYLE, word


# ---- the violin: Holmes's own instrument (owner 2026-09-13) ----------------

def test_the_bed_is_a_violin_because_holmes_plays_one():
    assert "violin" in asm.BED_STYLE.lower()


def test_the_violin_style_still_names_no_voice():
    import re
    for word in ("vocal", "vocals", "voice", "choir", "sings", "singer", "singing", "lyric"):
        assert not re.search(rf"{word}", asm.BED_STYLE, re.I), word
