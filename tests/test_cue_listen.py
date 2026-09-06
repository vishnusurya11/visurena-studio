"""A cue's SOUND, judged by a model that hears: the caption is a promise and
the listen gate asks whether the audio kept it, by ranking the brief against
the sounds a cue has come back as before (a parlour piece, a song, a drone).
Nothing in runs 9-12 listened; sixteen cues were graded on form and grid and
every one was the wrong kind of music."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from studio import cue_listen
from studio.cue_listen import PROBES, Verdict, brief_for, listen
from studio.music_tone import TRAILER_GENRE, load_tone

SCARLET = Path("library/20260822113400_a-study-in-scarlet")


def unit(*xs: float) -> np.ndarray:
    v = np.asarray(xs, dtype=np.float32)
    return v / np.linalg.norm(v)


class FakeEmbedder:
    """Text and audio in one tiny space: axis 0 is 'trailer', 1 'parlour',
    2 'song', 3 'drone'.  The audio vector says what the cue sounds like."""

    def __init__(self, sounds_like: np.ndarray):
        self.sounds_like = sounds_like
        self.asked: list[str] = []

    def text(self, sentences: list[str]) -> np.ndarray:
        self.asked += sentences
        axes = {"trailer": 0, "parlour": 1, "song": 2, "drone": 3}
        rows = []
        for s in sentences:
            key = next((k for k in axes if k in s.lower()), "trailer")
            rows.append(unit(*[1.0 if i == axes[key] else 0.1 for i in range(4)]))
        return np.stack(rows)

    def audio(self, path: Path) -> np.ndarray:
        return self.sounds_like


@pytest.fixture
def tone():
    return load_tone(SCARLET)


class TestBrief:
    def test_the_brief_opens_on_the_trailers_genre_and_carries_the_books_colour(self, tone):
        text = brief_for(tone)
        assert text.startswith(TRAILER_GENRE)
        assert tone.genre in text and tone.mood[0] in text

    def test_the_brief_is_one_short_sentence(self, tone):
        """CLAP's text tower was trained on captions of a few words; a 600-word
        caption is truncated at 77 tokens and the truncation decides the score."""
        assert len(brief_for(tone).split()) <= 40

    def test_every_probe_names_a_sound_a_cue_has_come_back_as(self):
        assert set(PROBES) >= {"parlour", "song", "drone"}
        for name, sentence in PROBES.items():
            assert name in sentence.lower(), (name, sentence)


class TestListen:
    def test_a_cue_that_sounds_like_the_brief_passes(self, tone):
        verdict = listen(Path("cue.flac"), tone, FakeEmbedder(unit(1.0, 0.2, 0.1, 0.1)))
        assert verdict.heard == "brief" and verdict.passes

    def test_a_parlour_piece_is_heard_as_one_and_fails(self, tone):
        verdict = listen(Path("cue.flac"), tone, FakeEmbedder(unit(0.2, 1.0, 0.1, 0.1)))
        assert verdict.heard == "parlour" and not verdict.passes

    def test_the_verdict_records_every_score_so_a_learning_can_quote_it(self, tone):
        verdict = listen(Path("cue.flac"), tone, FakeEmbedder(unit(0.2, 1.0, 0.1, 0.1)))
        assert set(verdict.scores) == {"brief", *PROBES}
        assert verdict.scores["parlour"] > verdict.scores["brief"]
        assert "parlour" in verdict.why and "brief" in verdict.why

    def test_the_brief_and_the_probes_are_embedded_in_one_call(self, tone):
        embedder = FakeEmbedder(unit(1.0, 0.2, 0.1, 0.1))
        listen(Path("cue.flac"), tone, embedder)
        assert embedder.asked[0] == brief_for(tone) and len(embedder.asked) == 1 + len(PROBES)

    def test_a_verdict_serialises_beside_the_cue(self, tone, tmp_path):
        verdict = listen(Path("cue.flac"), tone, FakeEmbedder(unit(1.0, 0.2, 0.1, 0.1)))
        path = cue_listen.write_verdict(tmp_path / "cue-1.flac", verdict)
        assert path.name == "cue-1.listen.json"
        assert Verdict.model_validate_json(path.read_text(encoding="utf-8")) == verdict


class FakeTensor:
    def __init__(self, rows): self.rows = rows
    def detach(self): return self
    def float(self): return self
    def cpu(self): return self
    def numpy(self): return np.asarray(self.rows, dtype=np.float32)


class TestFeatures:
    def test_a_bare_tensor_is_read_as_is(self):
        """transformers < 5 returns the projected embedding itself."""
        assert cue_listen.features_of(FakeTensor([[1.0, 2.0]])).tolist() == [[1.0, 2.0]]

    def test_an_output_object_yields_its_pooler_output(self):
        """transformers 5.16.1 returns BaseModelOutputWithPooling with the
        projected, normalised embedding in `pooler_output`; the probe of
        2026-09-06 died on `.float()` of that object."""
        class Out:
            pooler_output = FakeTensor([[3.0, 4.0]])
        assert cue_listen.features_of(Out()).tolist() == [[3.0, 4.0]]


class TestWindows:
    def test_a_long_cue_is_cut_into_full_windows(self):
        """One call on a long cue scores a random ten seconds; every window
        is embedded and averaged instead."""
        cut = cue_listen.windows(np.zeros(48_000 * 25), rate=48_000, seconds=10)
        assert [len(w) for w in cut] == [480_000, 480_000]

    def test_a_short_cue_is_one_window(self):
        assert len(cue_listen.windows(np.zeros(48_000 * 4))) == 1


class TestRealEmbedder:
    def test_the_real_embedder_is_imported_lazily(self):
        """The gate must be testable without the 600 MB checkpoint; the
        transformers import happens inside the constructor, never at module
        load, so step 03 imports cleanly on a box without it."""
        import sys
        assert "transformers" not in sys.modules
        assert callable(cue_listen.ClapEmbedder)
