"""A slow /prompt answer must never queue the same take twice, nor adopt another job.

The job is found by the client prompt id `submit` posted (fleet E A4, 2026-10-22); a job
writing the same `filename_prefix` under another id is someone else's."""
from studio.comfy import already_queued


SAVE = {"9": {"class_type": "SaveVideo", "inputs": {"filename_prefix": "ep_take_11"}}}
QUEUE = {"queue_running": [[1, "id-run", SAVE]],
         "queue_pending": [[2, "id-11", SAVE], [3, "id-12", SAVE]]}


def test_a_job_the_engine_already_took_is_found_by_its_id():
    assert already_queued(QUEUE, "id-11") == "id-11"


def test_a_running_job_counts_as_queued():
    assert already_queued(QUEUE, "id-run") == "id-run"


def test_a_job_that_never_landed_is_not_found():
    assert already_queued(QUEUE, "id-23") is None


def test_a_job_writing_the_same_prefix_under_another_id_is_not_matched():
    assert already_queued({"queue_running": [], "queue_pending": [[2, "x", SAVE]]}, "id-11") is None
