"""Phase-0 bench timing (2026-10-10): a render's sampler seconds come from the progress bar
ComfyUI logged inside that prompt's window, so load time never counts against an arm."""
from datetime import datetime

from scripts.bench import timing

LOG = ("[2026-10-10 20:22:05.203] 100%|####| 8/8 [01:54<00:00, 14.93s/it]100%|####| 8/8 [01:54<00:00, 14.30s/it]\n"
       "[2026-10-10 20:24:04.216] 100%|####| 4/4 [00:41<00:00,  10.2s/it]\r[2026-10-10 20:24:04.300] other\n")


def at(s: str) -> float:
    return datetime.strptime(s, "%Y-%m-%d %H:%M:%S").timestamp()


def test_the_bar_inside_the_window_is_read():
    ev = timing.log_events(LOG)
    s = timing.sampler_in(ev, at("2026-10-10 20:23:00"), at("2026-10-10 20:25:00"))
    assert s["steps"] == 4 and s["sample_s"] == 41 and s["s_per_it"] == 10.2


def test_an_unstamped_bar_fragment_after_a_carriage_return_is_read():
    ev = timing.log_events("[2026-10-10 20:30:00.000]   0%| 0/4 [00:00<?, ?s/it]\r100%|##| 4/4 [00:40<00:00, 10.0s/it]\n")
    s = timing.sampler_in(ev, at("2026-10-10 20:29:00"), at("2026-10-10 20:31:00"))
    assert s["sample_s"] == 40 and s["at"] == at("2026-10-10 20:30:00")


def test_the_last_bar_of_a_line_wins_and_a_window_without_one_is_none():
    ev = timing.log_events(LOG)
    assert timing.sampler_in(ev, at("2026-10-10 20:22:00"), at("2026-10-10 20:22:30"))["s_per_it"] == 14.30
    assert timing.sampler_in(ev, at("2026-10-10 21:00:00"), at("2026-10-10 21:01:00")) is None
