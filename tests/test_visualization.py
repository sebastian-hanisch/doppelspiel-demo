import pytest

import dsp_constants as C
import dsp_evaluation as E
import dsp_rules as R
import dsp_scenario as SC
import dsp_visualization as V
from dsp_evaluation import ListResult

N_, B_, S_, J_ = C.STRAT_NONE, C.STRAT_BAY, C.STRAT_SHORT, C.STRAT_JOHNSON
BAY = SC.make_bay(10, 6, 50, 50, 657)
OUTS = E.run_methods(BAY, 14)
JOH = OUTS[3]


def rects(fig):
    return [s for s in fig.layout.shapes if s.type == "rect"]


def trace(fig, name):
    return next(t for t in fig.data if t.name == name)


def lr(seed, **kw):
    v = dict(none=60, bay=40, short=38, johnson=36)
    v.update(kw)
    n = v["none"]
    cycles = {N_: n, B_: v["bay"], S_: v["short"], J_: v["johnson"]}
    return ListResult(seed, 30, 30, cycles, {k: 10 * (n - 2 * (n - c)) + 14 * (n - c) for k, c in cycles.items()}, 33)


# ---------------------------------------------------------------------------------------------------
# Spielfolge
# ---------------------------------------------------------------------------------------------------
def test_cycle_widths_and_texts():
    seq = (("U", 0), ("D", 1, 0), ("L", 2))
    assert V.cycle_widths(seq, 14) == [1.0, 1.4, 1.0]
    assert V.cycle_text(seq[0]) == "Einzelspiel: aus Stapel 1 löschen" and V.cycle_text(seq[2]) == "Einzelspiel: in Stapel 3 laden"
    assert V.cycle_text(seq[1]) == "Doppelspiel: aus Stapel 2 löschen und in Stapel 1 laden"


def test_sequence_figure_draws_one_cycle_rect_per_cycle_with_the_right_color_and_width():
    fig = V.sequence_figure(BAY, JOH.seq, 14)
    cycle_rects = [s for s in rects(fig) if s.y0 == 0 and s.y1 == 1]
    assert len(cycle_rects) == len(JOH.seq)
    assert [s.fillcolor for s in cycle_rects] == [C.CYCLE_COLORS[c[0]] for c in JOH.seq]
    widths = [round(s.x1 - s.x0 + V.GAP, 6) for s in cycle_rects]
    assert widths == [1.4 if c[0] == "D" else 1.0 for c in JOH.seq]
    assert cycle_rects[0].x0 == pytest.approx(V.GAP / 2) and all(b.x0 > a.x0 for a, b in zip(cycle_rects, cycle_rects[1:]))


def test_sequence_figure_total_width_is_the_crane_time():
    fig = V.sequence_figure(BAY, JOH.seq, 14)
    last = [s for s in rects(fig) if s.y0 == 0 and s.y1 == 1][-1]
    assert last.x1 + V.GAP / 2 == pytest.approx(JOH.time10 / 10)
    assert fig.layout.xaxis.range[1] == pytest.approx(JOH.time10 / 10 + 0.2)


def test_stack_rows_show_source_below_and_target_above_and_merge_consecutive_cycles():
    seq = (("U", 0), ("U", 0), ("D", 1, 0), ("L", 0))
    fig = V.sequence_figure(SC.Bay((2, 1), (2, 0)), seq, 14)
    below = [s for s in rects(fig) if s.y0 == -0.55]
    above = [s for s in rects(fig) if s.y0 == 1.1]
    assert [s.fillcolor for s in below] == [V.stack_color(0), V.stack_color(1)]               # Stapel 0 zwei Spiele zusammengefasst, dann Stapel 1
    assert [s.fillcolor for s in above] == [V.stack_color(0)] and round(above[0].x1 - above[0].x0 + V.GAP, 6) == 2.4          # Doppelspiel und Einzelspiel laden beide in Stapel 0
    assert round(below[0].x1 - below[0].x0 + V.GAP, 6) == 2.0


def test_hover_covers_each_cycle_and_names_it():
    fig = V.sequence_figure(BAY, JOH.seq, 14)
    hover = trace(fig, "Spiele")
    assert len(hover.x) == 3 * len(JOH.seq) and hover.marker.opacity == 0
    assert hover.text[0].startswith("<b>Spiel 1</b>") and V.cycle_text(JOH.seq[0]) in hover.text[0]
    assert all(V.cycle_text(c) in hover.text[3 * i] for i, c in enumerate(JOH.seq))


def test_legend_has_the_three_cycle_types_and_axes_are_fixed():
    fig = V.sequence_figure(BAY, JOH.seq, 14)
    assert [t.name for t in fig.data if t.name in C.CYCLE_NAMES.values()] == [C.CYCLE_NAMES[k] for k in ("U", "L", "D")]
    assert fig.layout.xaxis.fixedrange and fig.layout.yaxis.fixedrange


def test_sequence_figure_handles_an_empty_and_a_single_cycle_sequence():
    assert V.sequence_figure(SC.Bay((0,), (1,)), (("L", 0),), 14).layout.xaxis.range[1] == pytest.approx(1.2)
    empty = V.sequence_figure(SC.Bay((0,), (0,)), (), 14)
    assert len(rects(empty)) == 0 and empty.layout.xaxis.range[1] == pytest.approx(1.2)


def test_stack_color_wraps():
    assert V.stack_color(0) == C.STACK_COLORS[0] and V.stack_color(len(C.STACK_COLORS)) == C.STACK_COLORS[0]
    assert len(C.STACK_COLORS) >= 10 and len(set(C.STACK_COLORS)) == len(C.STACK_COLORS)


# ---------------------------------------------------------------------------------------------------
# Reihenfolge
# ---------------------------------------------------------------------------------------------------
def test_order_figure_shows_the_stacks_in_the_given_order():
    fig = V.order_figure(BAY, JOH.order)
    assert list(fig.data[0].x) == [str(k + 1) for k in JOH.order] and list(fig.data[0].y) == [BAY.u[k] for k in JOH.order] and list(fig.data[1].y) == [BAY.l[k] for k in JOH.order]
    assert [t.name for t in fig.data] == ["zu löschen", "zu laden"] and fig.layout.xaxis.type == "category" and fig.layout.xaxis.fixedrange


# ---------------------------------------------------------------------------------------------------
# Kurve
# ---------------------------------------------------------------------------------------------------
def make_curve():
    return E.Curve((10, 50, 100), {p: tuple(lr(i, bay=50 - p // 5) for i in range(2)) for p in (10, 50, 100)}, 2)


def test_curve_figure_has_a_line_per_method_with_the_saving_values():
    cv = make_curve()
    fig = V.curve_figure(cv, 50)
    assert [t.name for t in fig.data] == [C.STRATEGY_LABELS[k] for k in (B_, S_, J_)]
    assert list(fig.data[0].x) == [10, 50, 100] and list(fig.data[0].y) == pytest.approx(list(E.curve_saving(cv, B_)))
    assert fig.layout.xaxis.fixedrange and fig.layout.yaxis.fixedrange
    assert len(fig.layout.shapes) == 1 and len(V.curve_figure(cv, None).layout.shapes) == 0


# ---------------------------------------------------------------------------------------------------
# Verteilung, Gewinn, Vergleich
# ---------------------------------------------------------------------------------------------------
def test_distribution_figure_stacks_three_shares_per_method_and_names_the_reference():
    rs = [lr(0), lr(1, johnson=40), lr(2, johnson=42), lr(3)]
    dists = [E.distribution(rs, k, B_) for k in (S_, J_)]
    fig = V.distribution_figure(dists, "Bay-Reihenfolge")
    assert [t.name for t in fig.data] == ["weniger Spiele als Bay-Reihenfolge", "gleich viele", "mehr Spiele als Bay-Reihenfolge"]
    assert list(fig.data[0].y) == ["Kurze Entladung zuerst", "Johnson"]
    for i in range(2):
        assert abs(sum(t.x[i] for t in fig.data) - 100) < 1e-9
    assert fig.layout.barmode == "stack" and fig.layout.xaxis.fixedrange


def test_gain_figure_shows_median_and_mean():
    rs = [lr(0, johnson=36), lr(1, johnson=40), lr(2, johnson=30)]
    fig = V.gain_figure([E.distribution(rs, J_, B_)], "Bay-Reihenfolge")
    assert [t.name for t in fig.data] == ["Median (typischer Bay)", "Mittelwert"] and fig.data[0].y[0] == 4.0 and fig.data[1].y[0] == pytest.approx((4 + 0 + 10) / 3)
    assert fig.layout.yaxis.title.text == "eingesparte Spiele gegen Bay-Reihenfolge"


def test_comparison_figure_has_a_bar_per_method_and_the_bound_line():
    bound = R.lower_bound(BAY)
    fig = V.comparison_figure(OUTS, bound)
    assert [t.y[0] for t in fig.data] == [o.cycles for o in OUTS]
    lines = [s for s in fig.layout.shapes if s.type == "line"]
    assert len(lines) == 1 and lines[0].y0 == bound and fig.layout.annotations[0].text == f"untere Schranke {bound}"
    assert tuple(fig.layout.yaxis.range) == (0, max(o.cycles for o in OUTS) * 1.15)
    assert fig.layout.xaxis.fixedrange and fig.layout.yaxis.fixedrange


def test_stack_labels_appear_only_on_spans_at_least_one_and_a_half_cycles_wide():
    seq = (("U", 0), ("U", 0), ("D", 1, 0), ("L", 0))                   # Löschquelle: Stapel 0 über 2 Spiele (Breite 2), Stapel 1 über ein Doppelspiel (Breite 1,4); Ladeziel: Stapel 0 über 2,4
    fig = V.sequence_figure(SC.Bay((2, 1), (2, 0)), seq, 14)
    labels = [a.text for a in fig.layout.annotations if a.text in ("1", "2")]
    assert labels == ["1", "1"]                                          # Stapel 0 unten (2,0) und oben (2,4); Stapel 1 (1,4) bleibt unbeschriftet
