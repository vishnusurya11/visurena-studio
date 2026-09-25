"""The judges: every taste gate of the refs and episode lines, automated.

`registry` names each judge and wraps the shipped verdict functions so the
bench (`studio.judge_bench`) can run them over casebook rows from the stored
json alone.  Judge modules (`panel_eye`, `take_eye`, `look`, `plan`,
`master_eye`) and the shared contract (`verdict`) land beside it; this
package imports none of them at import time, so a judge is loaded by name
when it is asked for.
"""
