"""Takes of one episode are not independent: the bench says so (fleet H ruling A4).

A wall that refuses every take of six episodes and none of six others has a
row-wise share of one half on 120 rows, and a Wilson interval that pretends
120 coin flips.  The episode-cluster bootstrap resamples whole episodes, so
its interval is wider, and its effective n is nearer the 12 episodes than the
120 rows.  Under the convention's 10 episodes a percentile bootstrap
under-covers, so the bench prints "too few clusters" instead of a number.
"""
from studio import judge_bench as jb
from studio.casebook import Row


def rows(units: int, per_unit: int = 10) -> list[Row]:
    return [Row(codex="c", unit=f"ep{u:02d}", kind="take", path=f"episodes/ep{u:02d}/T{t:02d}.mp4",
                verdict="pass", verdict_by="owner") for u in range(units) for t in range(per_unit)]


def refuse_even_units(row):
    return {"refused": int(row.unit[2:]) % 2 == 0, "classes": [], "values": {}}


def test_a_clustered_refusal_pattern_widens_the_interval():
    outcomes = jb.run(rows(12), refuse_even_units)
    flat = jb.false_refusals(outcomes, "owner")
    boot = jb.clustered([o for o in outcomes if o.row.verdict == "pass"])
    assert flat.point == 0.5 and boot["clusters"] == 12
    assert boot["high"] - boot["low"] > 1.5 * (flat.high - flat.low)
    assert boot["n_eff"] < 30


def test_the_same_rows_give_the_same_bootstrap():
    outcomes = [o for o in jb.run(rows(12), refuse_even_units)]
    assert jb.clustered(outcomes) == jb.clustered(outcomes)


def test_too_few_episodes_print_too_few_clusters():
    outcomes = jb.run(rows(4), refuse_even_units)
    boot = jb.clustered(outcomes)
    assert boot["note"] == "too few clusters (4 episodes, under 10)" and boot["low"] is None
    assert "too few clusters" in jb.report(outcomes, "fixture", "abcdef01")


def test_nothing_counted_is_no_bootstrap():
    assert jb.clustered([])["note"] == "too few clusters (0 episodes, under 10)"
