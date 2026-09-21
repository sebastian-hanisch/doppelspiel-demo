import pytest

import dsp_constants as C
import dsp_evaluation as E
import dsp_rules as R
import dsp_scenario as SC
from dsp_evaluation import ListResult
from helpers import random_bay

N_, B_, S_, J_ = C.STRAT_NONE, C.STRAT_BAY, C.STRAT_SHORT, C.STRAT_JOHNSON
BAY = SC.make_bay(10, 6, 50, 50, 657)


def lr(seed, none=60, bay=40, short=38, johnson=36, bound=33, r10=14, containers=None):
    """Künstliches Ergebnis: Spiele gegeben, Doppelspiele = Container - Spiele; Kranzeit daraus."""
    n = none if containers is None else containers
    cycles = {N_: none, B_: bay, S_: short, J_: johnson}
    times = {k: 10 * (n - 2 * (n - c)) + r10 * (n - c) for k, c in cycles.items()}
    return ListResult(seed, n // 2, n - n // 2, cycles, times, bound)


def test_ratio10_and_minutes():
    assert E.ratio10(1.4) == 14 and E.ratio10(1.0) == 10 and E.ratio10(1.9) == 19 and E.ratio10(1.1) == 11
    assert E.minutes(10) == C.SINGLE_CYCLE_MINUTES and E.minutes(14) == 2.8 and E.minutes(0) == 0


def test_run_methods_returns_four_valid_outcomes_in_order():
    outs = E.run_methods(BAY, 14)
    assert [o.key for o in outs] == list(C.STRATEGY_KEYS) and [o.label for o in outs] == [C.STRATEGY_LABELS[k] for k in C.STRATEGY_KEYS]
    assert all(o.valid and o.violations == () for o in outs)
    assert [o.cycles for o in outs] == [len(R.play_none(BAY)), R.cycles_of(BAY, R.bay_order(BAY)), R.cycles_of(BAY, R.short_first(BAY)), R.cycles_of(BAY, R.johnson(BAY))]
    assert outs[0].duals == 0 and outs[0].singles_u == BAY.unloads and outs[0].singles_l == BAY.loads
    for o in outs:
        assert o.singles_u + o.singles_l + o.duals == o.cycles and o.time10 == R.time10(o.seq, 14)


def test_outcome_orders_and_the_reference_uses_the_bay_order():
    outs = E.run_methods(BAY, 14)
    assert outs[0].order == R.bay_order(BAY) and outs[1].order == R.bay_order(BAY) and outs[2].order == R.short_first(BAY) and outs[3].order == R.johnson(BAY)
    assert E.outcome_of(outs, J_) is outs[3]


def test_a_violating_sequence_is_reported_through_the_outcome():
    bad = E._outcome(BAY, N_, R.bay_order(BAY), (("U", 0),), 14)
    assert not bad.valid and "Entladen" in bad.violations


def test_saving_pct_and_comparison_rows():
    outs = E.run_methods(BAY, 14)
    ref, best = outs[0], outs[3]
    assert E.saving_pct(ref, ref) == 0.0
    assert E.saving_pct(best, ref) == pytest.approx(100 * (ref.time10 - best.time10) / ref.time10)
    rows = E.comparison_rows(BAY, outs)
    assert [r.delta_cycles for r in rows] == [o.cycles - ref.cycles for o in outs] and [r.gap_to_bound for r in rows] == [o.cycles - R.lower_bound(BAY) for o in outs]
    assert rows[3].singles == best.singles_u + best.singles_l and rows[3].duals == best.duals and rows[3].minutes == E.minutes(best.time10) and rows[0].saving_pct == 0.0


def test_largest_first_row_matches_a_direct_play():
    cycles, duals, minutes = E.largest_first_row(BAY, 14)
    seq = R.play(BAY, R.largest_first(BAY))
    assert cycles == len(seq) and duals == R.counts(seq)[2] and minutes == E.minutes(R.time10(seq, 14))


# ---------------------------------------------------------------------------------------------------
# Stichprobe
# ---------------------------------------------------------------------------------------------------
def test_run_bay_is_consistent_with_a_direct_run():
    r = E.run_bay(10, 6, 50, 50, 14, 657)
    outs = E.run_methods(SC.make_bay(10, 6, 50, 50, 657), 14)
    assert r.seed == 657 and r.cycles == {o.key: o.cycles for o in outs} and r.time10 == {o.key: o.time10 for o in outs}
    assert r.unloads == BAY.unloads and r.loads == BAY.loads and r.bound == R.lower_bound(BAY)


def test_sample_uses_seeds_from_zero_and_defaults_to_200():
    res = E.sample(8, 4, 50, 50, 14, n_bays=5)
    assert [r.seed for r in res] == [0, 1, 2, 3, 4] and res[2] == E.run_bay(8, 4, 50, 50, 14, 2)
    assert len(E.sample(4, 2, 10, 10, 14)) == C.SAMPLE_BAYS == 200


def test_curve_over_load_uses_the_same_seeds_at_every_point_and_the_given_points():
    cv = E.curve_over_load(8, 4, 50, 14, points=(20, 60), n_bays=3)
    assert cv.points == (20, 60) and cv.n_bays == 3
    for p in (20, 60):
        assert [r.seed for r in cv.lists[p]] == [0, 1, 2] and cv.lists[p] == E.sample(8, 4, 50, p, 14, 3)
    default = E.curve_over_load(4, 2, 50, 14, n_bays=2)
    assert default.points == C.CURVE_POINTS == tuple(range(10, 101, 10))


# ---------------------------------------------------------------------------------------------------
# Statistik (künstliche Ergebnisse)
# ---------------------------------------------------------------------------------------------------
def test_mean_cycles_and_savings():
    rs = [lr(0, none=60, bay=40), lr(1, none=60, bay=30)]
    assert E.mean_cycles(rs, B_) == 35
    assert E.mean_cycle_saving_pct(rs, B_) == pytest.approx((100 * 20 / 60 + 100 * 30 / 60) / 2)
    r = rs[0]
    assert E.mean_saving_pct([r], B_) == pytest.approx(100 * (r.time10[N_] - r.time10[B_]) / r.time10[N_])
    assert E.mean_saving_pct([r], N_) == 0.0


def test_paired_and_at_bound_share():
    rs = [lr(0, johnson=33, bound=33), lr(1, johnson=34, bound=33), lr(2, johnson=33, bound=33), lr(3, johnson=35, bound=33)]
    assert E.paired(rs, J_, B_) == [-7, -6, -7, -5] and E.at_bound_share(rs, J_) == 0.5


def test_distribution_counts_better_equal_worse_and_positive_gain_is_fewer_cycles():
    rs = [lr(0, bay=40, johnson=36), lr(1, bay=40, johnson=40), lr(2, bay=40, johnson=42), lr(3, bay=40, johnson=36)]         # -4, 0, +2, -4
    d = E.distribution(rs, J_, B_)
    assert (d.n, d.better, d.equal, d.worse) == (4, 0.5, 0.25, 0.25) and d.mean_gain == pytest.approx(1.5) and d.median_gain == 2.0


def test_verdict_three_states():
    better = [lr(i, bay=40, johnson=36 + i % 2) for i in range(10)]
    v = E.verdict(better, J_, B_)
    assert v.kind == "better" and v.diff < 0 and v.pct < 0 and v.worse_share == 0 and v.n == 10
    worse = [lr(i, bay=40, johnson=44 + i % 2) for i in range(10)]
    w = E.verdict(worse, J_, B_)
    assert w.kind == "worse" and w.diff > 0 and w.pct > 0 and w.worse_share == 1.0
    unclear = [lr(i, bay=40, johnson=40 + (i % 2) * 2 - 1) for i in range(10)]
    assert E.verdict(unclear, J_, B_).kind == "unclear"


def test_verdict_threshold_is_two_standard_errors_inclusive_and_equal_lists_are_unclear():
    same = [lr(i, bay=40, johnson=40) for i in range(6)]
    v = E.verdict(same, J_, B_)
    assert v.kind == "unclear" and v.diff == 0 and v.se == 0
    constant = [lr(i, bay=40, johnson=39) for i in range(6)]                                    # gleiche Differenz überall: se = 0, klar
    assert E.verdict(constant, J_, B_).kind == "better" and E.verdict([lr(i, bay=39, johnson=40) for i in range(6)], J_, B_).kind == "worse"
    edge = [lr(0, bay=40, johnson=39), lr(1, bay=40, johnson=37)]                               # Differenzen -1 und -3: Mittel -2, Standardfehler 1: genau 2 Standardfehler
    ve = E.verdict(edge, J_, B_)
    assert ve.diff == -2.0 and ve.se == pytest.approx(1.0) and ve.kind == "unclear"
    few = [lr(i, bay=40, johnson=40 - (i % 2) * 2) for i in range(4)]
    many = [lr(i, bay=40, johnson=40 - (i % 2) * 2) for i in range(16)]
    assert E.verdict(few, J_, B_).kind == "unclear" and E.verdict(many, J_, B_).kind == "better"


def test_verdict_pct_is_none_when_the_reference_needs_no_cycles():
    rs = [lr(i, none=0, bay=0, short=0, johnson=1, containers=0) for i in range(6)]
    v = E.verdict(rs, J_, B_)
    assert v.pct is None and v.kind == "worse"


def test_curve_saving_per_point():
    cv = E.Curve((10, 50), {10: (lr(0, none=60, bay=50),), 50: (lr(0, none=60, bay=30),)}, 1)
    assert E.curve_saving(cv, B_) == pytest.approx((E.mean_saving_pct(cv.lists[10], B_), E.mean_saving_pct(cv.lists[50], B_)))
    assert E.curve_saving(cv, B_)[1] > E.curve_saving(cv, B_)[0]


def test_real_sample_is_ordered_johnson_best_and_never_worse_than_no_dual_cycling():
    rs = E.sample(10, 6, 50, 50, 14)
    assert all(r.cycles[J_] <= r.cycles[S_] and r.cycles[J_] <= r.cycles[B_] <= r.cycles[N_] for r in rs)
    assert E.mean_cycles(rs, J_) < E.mean_cycles(rs, S_) < E.mean_cycles(rs, B_) < E.mean_cycles(rs, N_)
    assert 25 < E.mean_saving_pct(rs, J_) < 28 and E.verdict(rs, J_, B_).kind == "better"
