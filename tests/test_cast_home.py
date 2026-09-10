"""A character is one thing and belongs in one place."""
import json

from studio import cast_home


def book_with(tmp_path, who="sherlock_holmes", card=True, image=True):
    """A book laid out the OLD way, scattered across three folders."""
    if card:
        (tmp_path / "analysis/characters").mkdir(parents=True, exist_ok=True)
        (tmp_path / f"analysis/characters/{who}.json").write_text(
            json.dumps({"id": who}), encoding="utf-8")
    if image:
        (tmp_path / "refs/characters").mkdir(parents=True, exist_ok=True)
        (tmp_path / f"refs/characters/char-{who}.png").write_bytes(b"png")
    return tmp_path


class TestEverythingHangsOffOnePlace:
    def test_every_path_is_under_the_character_folder(self, tmp_path):
        home = cast_home.home(tmp_path, "sherlock_holmes")
        for path in (cast_home.card(tmp_path, "sherlock_holmes"),
                     cast_home.portrait(tmp_path, "sherlock_holmes"),
                     cast_home.clip(tmp_path, "sherlock_holmes"),
                     cast_home.sheet_path(tmp_path, "sherlock_holmes"),
                     cast_home.qc_path(tmp_path, "sherlock_holmes")):
            assert home in path.parents

    def test_the_home_sits_at_book_level_not_under_a_production(self, tmp_path):
        """A voice cast for the trailer must be reusable by the audiobook."""
        home = cast_home.home(tmp_path, "sherlock_holmes")
        assert home.parent.parent == tmp_path
        assert "trailer" not in str(home)

    def test_a_feeling_is_a_take_of_the_same_voice(self, tmp_path):
        angry = cast_home.clip(tmp_path, "sherlock_holmes", "angry")
        design = cast_home.clip(tmp_path, "sherlock_holmes")
        assert angry.parent == design.parent
        assert angry.name == "angry.wav"


class TestGatheringWhatIsScattered:
    def test_it_brings_the_card_and_the_portrait_home(self, tmp_path):
        book = book_with(tmp_path)
        got = cast_home.gather(book)
        assert got == {"sherlock_holmes": ["character.json", "portrait.png"]}
        assert cast_home.card(book, "sherlock_holmes").exists()
        assert cast_home.portrait(book, "sherlock_holmes").exists()

    def test_it_copies_so_the_old_readers_keep_working(self, tmp_path):
        book = book_with(tmp_path)
        cast_home.gather(book)
        assert (book / "analysis/characters/sherlock_holmes.json").exists()

    def test_it_never_overwrites_a_home_that_already_has_one(self, tmp_path):
        book = book_with(tmp_path)
        cast_home.card(book, "sherlock_holmes").parent.mkdir(parents=True)
        cast_home.card(book, "sherlock_holmes").write_text("mine", encoding="utf-8")
        cast_home.gather(book)
        assert cast_home.card(book, "sherlock_holmes").read_text(encoding="utf-8") == "mine"

    def test_a_character_with_no_portrait_still_comes_home(self, tmp_path):
        book = book_with(tmp_path, image=False)
        assert cast_home.gather(book) == {"sherlock_holmes": ["character.json"]}


class TestIsThisCharacterReady:
    def test_a_bare_book_has_nobody(self, tmp_path):
        assert cast_home.cast_of(tmp_path) == []

    def test_it_names_exactly_what_is_missing(self, tmp_path):
        book = book_with(tmp_path)
        cast_home.gather(book)
        assert cast_home.missing(book) == {"sherlock_holmes": ["voice", "checked"]}

    def test_a_finished_character_is_missing_nothing(self, tmp_path):
        book = book_with(tmp_path)
        cast_home.gather(book)
        cast_home.voice_dir(book, "sherlock_holmes").mkdir(parents=True)
        cast_home.clip(book, "sherlock_holmes").write_bytes(b"wav")
        cast_home.qc_path(book, "sherlock_holmes").write_text("[]", encoding="utf-8")
        assert cast_home.missing(book) == {}
        assert all(cast_home.ready(book, "sherlock_holmes").values())
