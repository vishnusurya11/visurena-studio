"""No music bed ships without something having LISTENED to it.

Episode 3 shipped with its bed singing invented English verse under the
narration for 101 of 157.8 seconds. Nothing caught it because nothing between
`bed()` and the mix ever transcribed the file.

THE FIRST VERSION OF THIS GATE WAS ALSO A NO-OP, and for an instructive reason:
it expected whisper SEGMENTS (`no_speech_prob`, `compression_ratio`), while both
of the studio's transcribers -- `voice_qc.transcriber` and `comfy_transcriber`
-- return a PLAIN STRING. `isinstance(heard, list)` was therefore always False,
`listen` always returned [], and `sings([])` is False. A gate that cannot
measure must never be indistinguishable from a gate that measured and approved.

So the judgement works on the text itself, and "could not listen" is its own
answer. Whisper on an instrumental returns a tiny stock vocabulary -- "Thank
you.", "You", "Mm-hmm." -- or one phrase looped. Sung verse returns many
DISTINCT words. That is the separator, and it needs no per-segment metadata.
"""
import pytest

from studio.bed_gate import UNVERIFIED, distinct_words, refuse_text, sings_text

# verbatim, the three beds the music audit transcribed
EP03_SUNG = ("When the rains are sunned and down Where the flames our sea dissolve "
             "In the hums and silent hold Locked between the stars and soul "
             "We move like hearts divine In the dust we hate divine "
             "Wraps of whispers soft and roar")
EP01_CLEAN = "Thank you. Thank you. Thank you. You Mm-hmm."
EP02_LOOP = "I'm sorry, but " * 12


def test_the_episode_3_bed_is_caught():
    """The one that shipped."""
    assert sings_text(EP03_SUNG)


def test_an_instrumental_bed_passes():
    assert not sings_text(EP01_CLEAN)


def test_a_repetition_loop_is_a_hallucination_not_a_song():
    assert not sings_text(EP02_LOOP)


def test_silence_passes():
    assert not sings_text("") and not sings_text("   ")


def test_distinct_words_is_what_separates_them():
    """The artefacts have a tiny vocabulary however long they run."""
    assert distinct_words(EP01_CLEAN) <= 5
    assert distinct_words(EP02_LOOP) <= 5
    assert distinct_words(EP03_SUNG) >= 25


def test_could_not_listen_is_NOT_the_same_as_clean():
    """The flaw that made the first version useless."""
    assert refuse_text(None) == UNVERIFIED
    assert refuse_text(EP03_SUNG).startswith("the bed sings")
    assert refuse_text(EP01_CLEAN) == ""


def test_the_refusal_quotes_what_it_heard():
    said = refuse_text(EP03_SUNG)
    assert "rains are sunned" in said


# ---- refusing twice must not crash ------------------------------------------

def test_the_refused_name_is_free_on_disk(tmp_path):
    """MEASURED 2026-09-13: YuE2 sang, the bed was refused and kept as
    `bed.sings.wav`; YuE2 sang AGAIN on the next attempt and the rename raised
    FileExistsError, killing the assemble after four minutes of GPU. `take_dq`
    solved this shape long ago and wrote down why: DISK KNOWS. The name comes
    off what is already there, never off a counter."""
    from studio.bed_gate import refused_name

    bed = tmp_path / "bed.wav"
    assert refused_name(bed).name == "bed.sings.wav"
    (tmp_path / "bed.sings.wav").write_bytes(b"")
    assert refused_name(bed).name == "bed.sings2.wav"
    (tmp_path / "bed.sings2.wav").write_bytes(b"")
    assert refused_name(bed).name == "bed.sings3.wav"
