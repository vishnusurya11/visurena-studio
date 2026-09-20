"""A workflow's node ids are not all numbers.

The Singularity take workflow names its second stacked turbo LoRA `lora_second`.
`h3_anchors._next_id` ran `int(k)` over every key and raised on the first take
of WotW ep04 -- after the whole 24-take run had been queued.
"""
from studio.h3_anchors import next_id


def test_a_named_node_is_skipped():
    assert next_id({"1": {}, "7": {}, "lora_second": {}}) == "8"


def test_a_part_numeric_key_is_skipped_too():
    assert next_id({"3": {}, "12a": {}}) == "4"


def test_an_all_named_graph_starts_at_one():
    assert next_id({"lora_second": {}}) == "1"
