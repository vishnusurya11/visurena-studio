"""The PUP runner (run by ComfyUI's python, which has CUDA torch + transformers) asks exactly as
BFL's model card documents: the t2i system prompt, the request as the user turn, greedy decoding."""
from __future__ import annotations

from prism.scripts.pup_captions import GENERATE, messages, pending_rows


def test_the_t2i_system_prompt_and_the_request_are_the_two_turns():
    said = messages({"t2i": "Be the upsampler."}, "Dracula, cel anime.")
    assert said == [{"role": "system", "content": "Be the upsampler."},
                    {"role": "user", "content": "Dracula, cel anime."}]


def test_decoding_is_greedy_with_the_cards_token_budget():
    assert GENERATE == {"max_new_tokens": 3584, "do_sample": False}


def test_a_rerun_writes_only_the_rows_not_yet_captioned():
    rows = [{"style": "a", "subject": "count"}, {"style": "a", "subject": "chase"}]
    done = [{"style": "a", "subject": "count", "caption": "x"}]
    assert pending_rows(rows, done) == [{"style": "a", "subject": "chase"}]
