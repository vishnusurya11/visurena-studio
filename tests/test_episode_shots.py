"""A take animates its own panel for its PLACED seconds; its run card is complete and lane-aware."""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("ep_shots", ROOT / "scripts" / "episode" / "shots.py")
shots = importlib.util.module_from_spec(spec)
sys.modules["ep_shots"] = shots
spec.loader.exec_module(shots)

from studio.episode_spec import Shot  # noqa: E402


def shot(index, take=0):
    return Shot(index=index, section="friction", setup="lab", size="wide", frame="f", motion="m",
                take=take)


def test_a_take_covers_the_placed_seconds_and_the_handle_on_the_grid():
    frames = shots.take_frames(4.0)
    assert frames % 17 == 5 and frames / 24 >= 4.0 + shots.HANDLE


def test_the_panel_is_the_shots_own_file(tmp_path):
    assert shots.panel_of(tmp_path, shot(7)).name == "S07.png"


def test_a_run_card_carries_the_prompt_the_lane_and_every_setting(monkeypatch):
    monkeypatch.setattr(shots.take_prompt, "build", lambda episode, shot: "the prompt")
    card = shots.run_card(shot(2), object(), Path("S02.png"), 7,
                          {"seconds": 4.0, "lane": "narration"})
    assert card["prompt"] == "the prompt" and card["start_image"] == "S02.png"
    assert card["seed"] == 7 and card["frames"] % 17 == 5 and card["lane"] == "narration"
    assert card["placed_seconds"] == 4.0 and card["audio"] is None


def test_a_dialogue_card_names_its_audio_and_the_dialogue_workflow(monkeypatch):
    monkeypatch.setattr(shots.take_prompt, "build", lambda episode, shot: "p")
    monkeypatch.setattr(shots, "DIALOGUE_WORKFLOW", "video_minimax_h3_lipsync")
    card = shots.run_card(shot(1), object(), Path("S01.png"), 5, {"seconds": 3.0, "lane": "dialogue"},
                          audio=Path("l01.wav"))
    assert card["workflow"] == "video_minimax_h3_lipsync" and card["audio"] == "l01.wav"
    monkeypatch.setattr(shots, "stage_image", lambda p: Path(p).name)
    values = shots.values_for(card, Path("S01.png"), Path("l01.wav"))
    assert values["audio"] == "l01.wav" and values["start_image"] == "S01.png"


def test_without_a_dialogue_workflow_a_dialogue_shot_falls_back_to_silent_i2v(monkeypatch):
    monkeypatch.setattr(shots.take_prompt, "build", lambda episode, shot: "p")
    monkeypatch.setattr(shots, "DIALOGUE_WORKFLOW", "")
    card = shots.run_card(shot(1), object(), Path("S01.png"), 5, {"seconds": 3.0, "lane": "dialogue"},
                          audio=Path("l01.wav"))
    assert card["workflow"] == shots.WORKFLOW


def test_a_retake_changes_the_seed(monkeypatch):
    monkeypatch.setattr(shots.take_prompt, "build", lambda episode, shot: "p")
    placed = {"seconds": 3.0, "lane": "narration"}
    seeds = [shots.run_card(s, object(), Path("S04.png"), 81000 + 4 + 7919 * s.take, placed)["seed"]
             for s in (shot(4), shot(4, take=1))]
    assert seeds[0] != seeds[1]
