"""A slow /prompt answer must never queue the same take twice."""
import pytest

from studio.comfy import already_queued


QUEUE = {"queue_running": [[1, "id-run", {"9": {"class_type": "SaveVideo",
                                                "inputs": {"filename_prefix": "ep_take_00"}}}]],
         "queue_pending": [[2, "id-11", {"9": {"class_type": "SaveVideo",
                                               "inputs": {"filename_prefix": "ep_take_11"}}}],
                           [3, "id-12", {"9": {"class_type": "SaveVideo",
                                               "inputs": {"filename_prefix": "ep_take_12"}}}]]}


def test_a_job_the_engine_already_took_is_found_by_its_prefix():
    assert already_queued(QUEUE, "ep_take_11") == "id-11"


def test_a_running_job_counts_as_queued():
    assert already_queued(QUEUE, "ep_take_00") == "id-run"


def test_a_job_that_never_landed_is_not_found():
    assert already_queued(QUEUE, "ep_take_23") is None


def test_a_graph_with_no_save_node_is_not_matched():
    queue = {"queue_running": [], "queue_pending": [[2, "x", {"1": {"class_type": "KSampler",
                                                                   "inputs": {}}}]]}
    assert already_queued(queue, "ep_take_01") is None
