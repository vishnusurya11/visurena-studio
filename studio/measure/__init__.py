"""Measures: a number or a list from a picture, never a verdict.

Detectors count and place (DWPose keypoints, GroundingDINO boxes, YuNet faces),
embeddings say who (facenet), hashes say whether a picture is a staged input
handed back, OCR says what the letters spell.  Each module takes its model or
its ComfyUI call as an injectable (`run=`, `reader=`, `embed=`, `detect=`), so a
test reads a recorded fixture and never loads a model.  The judges under
`studio/judges/` turn these numbers into faults; nothing here signs.
"""
