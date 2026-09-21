"""Auswertung: ein Bay mit allen Verfahren, Stichprobe über viele Bays, Kurve über den Beladeanteil, gepaarte Differenz, Verteilung und Urteil.

Reine Rechnung ohne Streamlit. Kosten sind Kranspiele beziehungsweise Kranzeit (weniger ist besser); alle Vergleiche sind gepaart (dieselben Bays); Unterschied = Verfahren minus Referenz,
negativ = weniger Spiele."""

import math
import statistics
from dataclasses import dataclass

import dsp_constants as C
import dsp_rules as R
import dsp_scenario as SC

ORDERS = {C.STRAT_BAY: R.bay_order, C.STRAT_SHORT: R.short_first, C.STRAT_JOHNSON: R.johnson}


def ratio10(ratio):
    """Doppelspiel-Kosten als ganze Zehntel (1,4 -> 14)."""
    return int(round(ratio * 10))


def minutes(t10):
    """Kranzeit in Minuten aus Zehnteln eines Einzelspiels."""
    return t10 / 10 * C.SINGLE_CYCLE_MINUTES


# ---------------------------------------------------------------------------------------------------
# Ein Bay, alle Verfahren
# ---------------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class Outcome:
    key: str
    label: str
    order: tuple            # Reihenfolge der Stapel (bei "Ohne Doppelspiel" die Bay-Reihenfolge)
    seq: tuple              # Spielfolge
    singles_u: int
    singles_l: int
    duals: int
    time10: int
    violations: tuple

    @property
    def cycles(self):
        return len(self.seq)

    @property
    def valid(self):
        return not self.violations


def _outcome(bay, key, order, seq, r10):
    su, sl, d = R.counts(seq)
    return Outcome(key, C.STRATEGY_LABELS[key], order, seq, su, sl, d, R.time10(seq, r10), R.verify(bay, seq))


def run_methods(bay, r10):
    """Alle vier Verfahren auf demselben Bay."""
    out = [_outcome(bay, C.STRAT_NONE, R.bay_order(bay), R.play_none(bay), r10)]
    for key, rule in ORDERS.items():
        order = rule(bay)
        out.append(_outcome(bay, key, order, R.play(bay, order), r10))
    return tuple(out)


def outcome_of(outcomes, key):
    return next(o for o in outcomes if o.key == key)


def saving_pct(o, ref):
    """Ersparnis der Kranzeit in % der Referenz."""
    return 100.0 * (ref.time10 - o.time10) / ref.time10


@dataclass(frozen=True)
class Row:
    key: str
    label: str
    cycles: int
    singles: int
    duals: int
    minutes: float
    saving_pct: float
    gap_to_bound: int       # Spiele über der unteren Schranke
    delta_cycles: int       # Spiele minus Referenz (negativ = weniger)
    valid: bool
    violations: tuple


def comparison_rows(bay, outcomes, baseline=C.BASELINE):
    ref = outcome_of(outcomes, baseline)
    bound = R.lower_bound(bay)
    return tuple(Row(o.key, o.label, o.cycles, o.singles_u + o.singles_l, o.duals, minutes(o.time10), saving_pct(o, ref), o.cycles - bound, o.cycles - ref.cycles, o.valid, o.violations)
                 for o in outcomes)


def largest_first_row(bay, r10):
    """Vergleichszeile für "Größte Entladung zuerst": (Spiele, Doppelspiele, Minuten)."""
    seq = R.play(bay, R.largest_first(bay))
    return len(seq), R.counts(seq)[2], minutes(R.time10(seq, r10))


# ---------------------------------------------------------------------------------------------------
# Stichprobe: viele Bays
# ---------------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class ListResult:
    seed: int
    unloads: int
    loads: int
    cycles: dict            # Verfahren -> Spiele
    time10: dict            # Verfahren -> Kranzeit in Zehnteln
    bound: int              # untere Schranke der Spiele


def run_bay(n_stacks, tiers, unload_pct, load_pct, r10, seed):
    bay = SC.make_bay(n_stacks, tiers, unload_pct, load_pct, seed)
    none_seq = R.play_none(bay)
    cycles, times = {C.STRAT_NONE: len(none_seq)}, {C.STRAT_NONE: R.time10(none_seq, r10)}
    for key, rule in ORDERS.items():
        order = rule(bay)
        cycles[key] = R.cycles_of(bay, order)
        d = R.duals_of(bay, order)
        times[key] = 10 * (bay.containers - 2 * d) + r10 * d
    return ListResult(seed, bay.unloads, bay.loads, cycles, times, R.lower_bound(bay))


def sample(n_stacks, tiers, unload_pct, load_pct, r10, n_bays=C.SAMPLE_BAYS):
    """Bays mit den Seeds 0..n_bays-1 (unabhängig vom eingestellten Seed) mit den eingestellten Werten."""
    return tuple(run_bay(n_stacks, tiers, unload_pct, load_pct, r10, s) for s in range(n_bays))


@dataclass(frozen=True)
class Curve:
    points: tuple           # Beladeanteil in %
    lists: dict             # Punkt -> Tupel von ListResult (gleiche Seeds an jedem Punkt)
    n_bays: int


def curve_over_load(n_stacks, tiers, unload_pct, r10, points=C.CURVE_POINTS, n_bays=C.CURVE_BAYS):
    """Kranzeit-Ersparnis über dem Beladeanteil: dieselben Seeds an jedem Punkt."""
    return Curve(tuple(points), {p: sample(n_stacks, tiers, unload_pct, p, r10, n_bays) for p in points}, n_bays)


# ---------------------------------------------------------------------------------------------------
# Statistik über Bays (gepaart)
# ---------------------------------------------------------------------------------------------------
def _se(xs):
    return statistics.stdev(xs) / math.sqrt(len(xs)) if len(xs) > 1 else 0.0


def mean_cycles(results, key):
    return statistics.fmean(r.cycles[key] for r in results)


def mean_saving_pct(results, key, reference=C.BASELINE):
    """Mittlere Kranzeit-Ersparnis in % je Bay gegen die Referenz."""
    return statistics.fmean(100.0 * (r.time10[reference] - r.time10[key]) / r.time10[reference] for r in results)


def mean_cycle_saving_pct(results, key, reference=C.BASELINE):
    return statistics.fmean(100.0 * (r.cycles[reference] - r.cycles[key]) / r.cycles[reference] for r in results)


def paired(results, key, reference):
    """Gepaarte Differenz der Spiele key - reference (negativ = weniger Spiele)."""
    return [r.cycles[key] - r.cycles[reference] for r in results]


def at_bound_share(results, key):
    """Anteil der Bays, in denen das Verfahren die untere Schranke erreicht."""
    return sum(1 for r in results if r.cycles[key] == r.bound) / len(results)


@dataclass(frozen=True)
class Distribution:
    key: str
    n: int
    better: float           # Anteile (0..1) gegen die Referenz
    equal: float
    worse: float
    mean_gain: float        # eingesparte Spiele je Bay (positiv = weniger Spiele als die Referenz)
    median_gain: float


def distribution(results, key, reference):
    d = paired(results, key, reference)
    n = len(d)
    better, worse = sum(1 for x in d if x < 0), sum(1 for x in d if x > 0)
    return Distribution(key, n, better / n, (n - better - worse) / n, worse / n, -statistics.fmean(d), -statistics.median(d))


@dataclass(frozen=True)
class Verdict:
    kind: str               # "better" (weniger Spiele) | "worse" | "unclear"
    diff: float             # Verfahren minus Referenz, Spiele je Bay (negativ = weniger)
    se: float
    pct: object             # Unterschied in % der Referenz; None, wenn die Referenz im Mittel 0 Spiele braucht
    n: int
    worse_share: float      # Anteil der Bays mit mehr Spielen als die Referenz


def verdict(results, key, reference):
    """Bewertung gegen die Referenz. 'Klar' heißt: Unterschied > VERDICT_Z Standardfehler der gepaarten Differenz; sonst 'unclear'."""
    d = paired(results, key, reference)
    diff, se = statistics.fmean(d), _se(d)
    ref_mean = mean_cycles(results, reference)
    if se == 0:
        kind = "unclear" if diff == 0 else ("better" if diff < 0 else "worse")
    else:
        kind = "unclear" if abs(diff) <= C.VERDICT_Z * se else ("better" if diff < 0 else "worse")
    return Verdict(kind, diff, se, 100.0 * diff / ref_mean if ref_mean else None, len(d), sum(1 for x in d if x > 0) / len(d))


def curve_saving(cv, key):
    """Mittlere Kranzeit-Ersparnis in % je Punkt der Kurve."""
    return tuple(mean_saving_pct(cv.lists[p], key) for p in cv.points)
