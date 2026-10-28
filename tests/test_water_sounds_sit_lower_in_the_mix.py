"""Owner 2026-10-28 on Jekyll ep04: "Slightly cool down on the sound effects .. they are little loud
especially water draining".  Every cue sits 3 dB lower (CUE_TRIM_DB 3 -> 6) and a cue whose own words
name water (the sidecar's prompt: "river water lapping", "fog drip", "a dripping tap") a further
WATER_TRIM_DB.  Measured on ep04 against its lines (-20 LUFS): effects -22 to -24 LUFS with peaks at
-3.5 dBFS, ambience loops -34 LUFS running under whole scenes."""
import json
from pathlib import Path

from studio import episode_sound as es


def sidecar(folder: Path, name: str, words: str) -> None:
    (folder / name).write_text(json.dumps({"prompt": f"TrackType: SFX, {words}, London, October"}), encoding="utf-8")


def test_every_cue_is_three_db_lower_than_before():
    assert es.CUE_TRIM_DB == 6.0


def test_a_water_ambience_is_trimmed_further_through_its_loop(tmp_path):
    sidecar(tmp_path, "amb_356ebf8b.loop.json", "river water lapping at a wall, a dog barking far off")
    assert es.trim_for(tmp_path / "amb_356ebf8b_0015.83.wav") == es.CUE_TRIM_DB + es.WATER_TRIM_DB


def test_a_water_effect_is_trimmed_further_and_a_dry_one_is_not(tmp_path):
    sidecar(tmp_path, "shot09_aa.json", "a dripping tap in a stone cell")
    sidecar(tmp_path, "shot03_bb.json", "a boot stamping hard on cobbles")
    assert es.trim_for(tmp_path / "shot09_aa.wav") == es.CUE_TRIM_DB + es.WATER_TRIM_DB
    assert es.trim_for(tmp_path / "shot03_bb.wav") == es.CUE_TRIM_DB


def test_a_cue_with_no_sidecar_takes_the_plain_trim(tmp_path):
    assert es.trim_for(tmp_path / "shot01_cc.wav") == es.CUE_TRIM_DB


def test_the_mix_applies_the_cue_s_own_trim(tmp_path):
    sidecar(tmp_path, "shot09_aa.json", "water draining into a gutter")
    ran = []
    es.ducked([(1.0, tmp_path / "shot09_aa.wav")], [], tmp_path, run=ran.append)
    assert f"{es.db_gain(-(es.CUE_TRIM_DB + es.WATER_TRIM_DB)):.6f}" in " ".join(ran[0])
