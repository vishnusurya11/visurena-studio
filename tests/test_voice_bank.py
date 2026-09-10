"""A voice bank per character: one timbre, several emotions, from the book."""
from __future__ import annotations

from studio import voice_bank

HOLMES = {"id": "sherlock_holmes", "name": "Sherlock Holmes", "profile": {
    "voice": "His speech is direct, confident, formal, and concise. He states "
             "conclusions bluntly and uses dry humour."},
    "quotes": [{"quote": "“You have been in Afghanistan, I perceive.”"},
               {"quote": "“The question now is about hæmoglobin.”"},
               {"quote": "“I have my eye on a suite in Baker Street.”"},
               {"quote": "“There is nothing like first hand evidence.”"}]}
HOPE = {"id": "jefferson_hope", "name": "Jefferson Hope", "profile": {
    "voice": "Direct, emotionally open, comparatively plain, with frontier "
             "references. Under pressure he is concise and commanding."},
    "quotes": [{"quote": "I will come and claim you then, my darling."},
               {"quote": "A couple of months at the outside."},
               {"quote": "There is death in one and life in the other."},
               {"quote": "Choose and eat."}]}


def a_render(made: list):
    def render(text, instruct, out):
        made.append((out.name, text, instruct))
        out.write_bytes(b"wav")
    return render


class TestTheBank:
    def test_a_clip_is_made_for_every_emotion_once(self, tmp_path):
        made = []
        bank = voice_bank.build(HOLMES, tmp_path, a_render(made))
        assert set(bank) == set(voice_bank.EMOTIONS)
        assert len(made) == len(voice_bank.EMOTIONS)
        voice_bank.build(HOLMES, tmp_path, a_render(made))       # again
        assert len(made) == len(voice_bank.EMOTIONS)             # nothing re-rendered

    def test_every_character_reads_the_SAME_words(self):
        """The baseline.  When the content differs, a comparison between two
        voices measures the content -- so the words are held fixed and the
        voice becomes the only variable."""
        for emotion in voice_bank.EMOTIONS:
            assert voice_bank.bank_text(HOLMES, emotion) == voice_bank.bank_text(HOPE, emotion)

    def test_every_emotion_opens_on_the_same_sentence_and_then_turns(self):
        """Held fixed in the other direction too: one character's calm and
        angry clips differ only in feeling.  The turn is what an emotion
        reference carries and what a one-shot engine replicates."""
        opening = "I have looked at this a long while, and I know now what it is."
        texts = [voice_bank.bank_text(HOLMES, e) for e in voice_bank.EMOTIONS]
        assert all(t.startswith(opening) for t in texts)
        assert len({t[len(opening):] for t in texts}) == len(voice_bank.EMOTIONS)

    def test_the_passage_gives_the_engine_somewhere_to_MOVE(self):
        """A reference clip needs sentences that start and stop, a phrase that
        lands harder than the one before, a place to breathe.  Forty words of
        even prose gives the engine one colour to copy."""
        for emotion in voice_bank.EMOTIONS:
            text = voice_bank.bank_text(HOLMES, emotion)
            assert len(text.split()) >= 65
            assert text.count(".") >= 4           # room to breathe, not one long line

    def test_the_delivery_note_is_direction_rather_than_a_label(self):
        """"hard and clipped" is a LABEL, and a label gives the engine nothing
        to act on.  Direction says what the mouth and the breath do: pace,
        pitch, breath, attack, where a word lands."""
        for emotion in voice_bank.EMOTIONS:
            note = voice_bank.DELIVERY[emotion]
            assert len(note.split()) >= 30
            assert any(w in note for w in ("pitch", "breath", "pace", "volume"))

    def test_the_passage_belongs_to_no_book(self):
        """A baseline that mentions a hansom cannot be reused for the next
        book.  No name, no period, no plot."""
        joined = " ".join(voice_bank.BASELINE.values()).lower()
        for word in ("holmes", "watson", "london", "hansom", "gaslight", "scarlet"):
            assert word not in joined

    def test_the_text_never_says_the_emotion_out_loud(self):
        """"how I sound when I am threatening" is the actor reading the stage
        direction.  The feeling belongs in the INSTRUCT."""
        for emotion in voice_bank.EMOTIONS:
            assert emotion not in voice_bank.bank_text(HOLMES, emotion).lower()

    def test_the_instruct_never_asks_for_two_deliveries_at_once(self):
        """The bug this file already fixed in the image prompt, made again
        here: `voice.voice_instruct` ends on "an even unhurried pace, a calm
        neutral read", and appending "hard and clipped" left the model holding
        two contradictory directions.  The neutral tail comes off first."""
        note = voice_bank.instruct(HOLMES, "threatening")
        assert "calm neutral read" not in note
        assert "even unhurried pace" not in note
        assert voice_bank.DELIVERY["threatening"] in note

    def test_the_calm_read_keeps_its_own_delivery(self):
        note = voice_bank.instruct(HOLMES, "calm")
        assert voice_bank.DELIVERY["calm"] in note
        assert note.count("Speak this") == 1

    def test_the_instruct_carries_who_is_speaking_and_how(self):
        """`voice.voice_instruct` already builds the who -- sex, age, role and
        the book's own line on how they speak -- and never names an accent."""
        note = voice_bank.instruct(HOLMES, "threatening")
        assert voice_bank.DELIVERY["threatening"] in note
        assert len(note.split()) < 90
        assert voice_bank.instruct(HOLMES, "threatening") != voice_bank.instruct(HOPE, "threatening")

    def test_the_emotions_are_chosen_for_the_JOB_not_the_engine(self):
        """An earlier draft used IndexTTS2's slider names -- Happy, Angry,
        Sad, Afraid -- which is choosing by the tool.  `happy` is nearly
        useless in a detective mystery, and `curious` is the register the
        book gives Holmes ("amused self-assurance").  Neither engine
        constrains us: Qwen takes free text, IndexTTS2 takes any clip."""
        assert "curious" in voice_bank.EMOTIONS
        assert "cold" in voice_bank.EMOTIONS
        assert "happy" not in voice_bank.EMOTIONS


class TestWhichEmotionALineWants:
    def test_the_timbre_comes_from_the_unpushed_read(self, tmp_path):
        bank = voice_bank.build(HOLMES, tmp_path, a_render([]))
        assert voice_bank.timbre_of(bank).name.endswith("-calm.wav")

    def test_a_threat_is_read_as_a_threat(self):
        assert voice_bank.emotion_for("escalation", "the figure names his revenge") \
            == "threatening"

    def test_a_deduction_is_read_cold(self):
        assert voice_bank.emotion_for("promise", "the method: first hand evidence") == "cold"

    def test_the_chase_is_read_urgent(self):
        assert voice_bank.emotion_for("turn", "the pursuit closes") == "urgent"

    def test_a_beat_that_says_nothing_particular_is_read_plain(self):
        assert voice_bank.emotion_for("button", "one last image") == voice_bank.TIMBRE
