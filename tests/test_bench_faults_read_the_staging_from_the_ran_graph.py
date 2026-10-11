"""Phase-0 bench faults (2026-10-10): the people a take planned, the sheets it staged and the
voice that drove it are read from the graph that ran, never typed per shot."""
from scripts.bench import faults


def graph() -> dict:
    return {
        "18": {"class_type": "LoadImage", "inputs": {"image": "sheet_front_28241af7.png"}},
        "19": {"class_type": "LoadImage", "inputs": {"image": "sheet_4d5059f4.png"}},
        "20": {"class_type": "LoadImage", "inputs": {"image": "shot_12_1885304d.png"}},
        "21": {"class_type": "LoadAudio", "inputs": {"audio": "voice_12_a54cc980.wav"}},
    }


def test_the_staged_sheets_are_the_planned_people():
    assert faults.sheets_of(graph()) == ["sheet_front_28241af7.png", "sheet_4d5059f4.png"]


def test_a_voiced_take_names_its_voice_and_a_silent_one_none():
    assert faults.voice_of(graph()) == "voice_12_a54cc980.wav"
    g = graph()
    g["21"]["inputs"]["audio"] = "silence_05_9edf7e50.wav"
    assert faults.voice_of(g) is None


def test_big_faces_past_the_planned_count_are_clones():
    assert faults.clone_frames([[0.3, 0.25], [0.3], [0.3, 0.05]], planned=1) == 1
