"""R7: Jekyll ep01 l11 'Gold, and a cheque.' -- whisper heard 'check' x8 (WER 0.25), a ruler fault."""
from pathlib import Path

import pytest

from studio import voice_qc

WAV = Path(__file__).parent / "fixtures" / "ep01_replay" / "P11" / "l11.wav"
LINE = "Gold, and a cheque."
PARK = "Gold and a check."          # the transcript of the eight parked tries


def test_the_parked_pair_is_phoneme_equal_and_filed(tmp_path):
    assert voice_qc.differing_pair(PARK, LINE) == ("check", "cheque")
    assert voice_qc.file_homophone(tmp_path, PARK, LINE)
    heard = voice_qc.with_lexicon(lambda clip: PARK, voice_qc.ear_lexicon(tmp_path))(WAV)
    assert voice_qc.error_rate(heard, LINE) == 0.0


@pytest.mark.local
def test_the_stored_l11_wav_relistens_at_wer_0_under_the_lexicon(tmp_path):
    voice_qc.file_homophone(tmp_path, PARK, LINE)
    ear = voice_qc.with_lexicon(voice_qc.cpu_transcriber(), voice_qc.ear_lexicon(tmp_path))
    assert voice_qc.check(WAV, LINE, transcribe=ear).error_rate == 0.0
