"""Kriterien der Preset-Geschichten (dsp_stories.py) mit KÜNSTLICHEN Werten: jedes Kriterium kippt einzeln an seiner Schwelle. (Abnahmen über echte Daten prüfen Schwellen nicht;
die stehen in test_preset_stories.py.)"""

import pytest

import dsp_constants as C
import dsp_stories as ST
from dsp_evaluation import ListResult

N_, B_, S_, J_ = C.STRAT_NONE, C.STRAT_BAY, C.STRAT_SHORT, C.STRAT_JOHNSON
NAMES = list(C.PRESETS)


def fake(none=60, bay=40, short=38, johnson=36, bound=33, containers=60, n=100):
    """n gleiche Bays; die Kranzeit folgt aus den Spielen (Doppelspiele = Container - Spiele, Doppelspiel kostet 1,4)."""
    cycles = {N_: none, B_: bay, S_: short, J_: johnson}
    times = {k: 10 * (containers - 2 * (containers - c)) + 14 * (containers - c) for k, c in cycles.items()}
    return tuple(ListResult(i, containers // 2, containers - containers // 2, cycles, times, bound) for i in range(n))


def failing(name, results):
    return [i for i, (ok, _) in enumerate(ST.criteria(name, results)) if not ok]


def mixed(k, a, b, n=100, **kw):
    """n Bays; die ersten k mit den Werten a (dict), die übrigen mit b (dict)."""
    rows = []
    for i in range(n):
        v = dict(kw, **(a if i < k else b))
        rows.append(fake(n=1, **v)[0])
    return tuple(ListResult(i, r.unloads, r.loads, r.cycles, r.time10, r.bound) for i, r in enumerate(rows))


BASE = {
    "Nur Löschen": dict(none=36, bay=31, short=31, johnson=30, bound=30, containers=36),          # Johnson spart 16,7 %, liegt auf der Schranke
    "Ausgewogen": dict(none=60, bay=36, short=34, johnson=33, bound=30, containers=60),           # spart 45 % der Spiele, Johnson < Bay
    "Viel Laden": dict(none=78, bay=52, short=49, johnson=49, bound=48, containers=78),           # Johnson = kurze Entladung
    "Wenig Laden": dict(none=42, bay=32, short=31, johnson=30, bound=30, containers=42),
    "Große Bays": dict(none=160, bay=93, short=87, johnson=85, bound=80, containers=160),
}


def base(name, **override):
    return fake(**dict(BASE[name], **override))


@pytest.mark.parametrize("name", NAMES)
def test_the_artificial_base_case_satisfies_every_criterion_and_the_single_bay_story(name):
    assert failing(name, base(name)) == []
    assert ST.holds(name, base(name)[0])


@pytest.mark.parametrize("name,override,expected", [
    # Nur Löschen: [Spiele gespart <= 20 %, auf der Schranke >= 95 %]
    ("Nur Löschen", dict(bound=29), [1]), ("Nur Löschen", dict(johnson=28, bound=28), [0]), ("Nur Löschen", dict(johnson=25, bound=25), [0]),
    # Ausgewogen: [Spiele gespart >= 40 %, Kranzeit >= 20 %, Johnson < Bay in >= 75 %]
    ("Ausgewogen", dict(johnson=37, bay=37), [0, 2]), ("Ausgewogen", dict(johnson=36, bay=37), []), ("Ausgewogen", dict(johnson=37, bay=38), [0]),
    # Viel Laden: [Johnson = kurze Entladung >= 90 %, Kranzeit >= 20 %]
    ("Viel Laden", dict(johnson=48), [0]), ("Viel Laden", dict(johnson=50, short=48), [0]), ("Viel Laden", dict(johnson=55, short=55), [1]),
    # Wenig Laden: [Johnson < Bay >= 60 %, Vorsprung >= 1,5 Punkte, Schranke >= 85 %]
    ("Wenig Laden", dict(bay=30), [0, 1]), ("Wenig Laden", dict(johnson=31), [1, 2]),
    # Große Bays: [Spiele gespart >= 44 %, Schranke <= 20 %]
    ("Große Bays", dict(johnson=95), [0]), ("Große Bays", dict(johnson=80, bound=80), [1]),
])
def test_each_criterion_flips_at_its_threshold(name, override, expected):
    assert failing(name, base(name, **override)) == expected, (name, override)


def test_nur_loeschen_savings_boundary_is_inclusive_at_20_percent():
    assert failing("Nur Löschen", fake(none=50, bay=41, short=41, johnson=40, bound=40, containers=50)) == []                    # genau 20 %
    assert failing("Nur Löschen", fake(none=50, bay=40, short=40, johnson=39, bound=39, containers=50)) == [0]                   # 22 %


def test_ausgewogen_cycle_saving_boundary_is_inclusive_at_40_percent():
    assert failing("Ausgewogen", fake(none=50, bay=32, short=31, johnson=30, bound=25, containers=50)) == []                     # genau 40 %
    assert failing("Ausgewogen", fake(none=50, bay=32, short=31, johnson=31, bound=25, containers=50)) == [0]                    # 38 %


def test_ausgewogen_share_of_bays_where_johnson_beats_bay_flips_at_75_percent():
    a, b = dict(bay=36, johnson=33), dict(bay=33, johnson=33)
    assert failing("Ausgewogen", mixed(75, a, b, none=60, short=34, bound=30, containers=60)) == []
    assert failing("Ausgewogen", mixed(74, a, b, none=60, short=34, bound=30, containers=60)) == [2]


def test_viel_laden_equality_share_flips_at_90_percent():
    a, b = dict(johnson=49, short=49), dict(johnson=49, short=50)
    assert failing("Viel Laden", mixed(90, a, b, none=78, bay=52, bound=48, containers=78)) == []
    assert failing("Viel Laden", mixed(89, a, b, none=78, bay=52, bound=48, containers=78)) == [0]


def test_wenig_laden_share_and_lead_and_bound_boundaries():
    a, b = dict(johnson=30, bay=32), dict(johnson=30, bay=30)
    assert failing("Wenig Laden", mixed(60, a, b, none=42, short=31, bound=30, containers=42)) == []                            # genau 60 %
    assert failing("Wenig Laden", mixed(59, a, b, none=42, short=31, bound=30, containers=42)) == [0]
    c, d = dict(johnson=30), dict(johnson=31)
    assert failing("Wenig Laden", mixed(85, c, d, none=42, bay=33, short=31, bound=30, containers=42)) == []                     # Schranke an genau 85 %
    assert failing("Wenig Laden", mixed(84, c, d, none=42, bay=33, short=31, bound=30, containers=42)) == [2]


def test_grosse_bays_bound_share_flips_at_20_percent():
    a, b = dict(johnson=85, bound=85), dict(johnson=85, bound=80)
    assert failing("Große Bays", mixed(20, a, b, none=160, bay=93, short=87, containers=160)) == []
    assert failing("Große Bays", mixed(21, a, b, none=160, bay=93, short=87, containers=160)) == [1]


@pytest.mark.parametrize("name,override,expected", [
    ("Nur Löschen", {}, True), ("Nur Löschen", dict(bound=29), False), ("Nur Löschen", dict(johnson=27, bound=27, none=36), True), ("Nur Löschen", dict(johnson=26, bound=26), False),
    ("Ausgewogen", {}, True), ("Ausgewogen", dict(bay=33), False), ("Ausgewogen", dict(johnson=37, bay=37), False), ("Ausgewogen", dict(johnson=37, bay=38), False), ("Ausgewogen", dict(none=54, bay=36, short=34, johnson=32, bound=27, containers=54), True),
    ("Viel Laden", {}, True), ("Viel Laden", dict(short=50), False), ("Viel Laden", dict(none=70, bay=50, short=45, johnson=45, bound=40, containers=70), True),
    ("Viel Laden", dict(none=62, bay=40, short=50, johnson=50, bound=40, containers=62), False),
    ("Wenig Laden", {}, True), ("Wenig Laden", dict(bay=30), False), ("Wenig Laden", dict(johnson=31), False),
    ("Große Bays", {}, True), ("Große Bays", dict(bound=85), False), ("Große Bays", dict(johnson=95), False),
])
def test_single_bay_story_flips_at_its_threshold(name, override, expected):
    assert ST.holds(name, base(name, **override)[0]) is expected, (name, override)


def test_cycle_and_time_saving_helpers():
    r = fake(none=50, bay=40, short=38, johnson=30, bound=25, containers=50)[0]
    assert ST.cycle_saving(r) == 40.0 and ST.cycle_saving(r, B_) == 20.0 and ST.cycle_saving(r, N_) == 0.0
    assert ST.time_saving(r) == pytest.approx(100 * (500 - (10 * (50 - 40) + 14 * 20)) / 500) and ST.time_saving(r, N_) == 0.0


def test_unknown_preset_name_raises():
    with pytest.raises(KeyError):
        ST.criteria("Unbekannt", base("Ausgewogen"))
    with pytest.raises(KeyError):
        ST.holds("Unbekannt", base("Ausgewogen")[0])


def test_key_values_lists_the_typical_indicators_of_the_preset():
    assert ST.key_values("Ausgewogen", base("Ausgewogen")) == {B_: 36.0, J_: 33.0} and ST.key_values("Nur Löschen", base("Nur Löschen")) == {J_: 30.0}
    assert {n for n, _ in ST.TYPICAL} == set(NAMES)


def test_inclusive_boundaries_of_the_remaining_thresholds():
    # Nur Löschen: Schranke an genau 95 % der Bays
    a, b = dict(johnson=30, bound=30), dict(johnson=30, bound=29)
    assert failing("Nur Löschen", mixed(95, a, b, none=36, bay=31, short=31, containers=36)) == [] and failing("Nur Löschen", mixed(94, a, b, none=36, bay=31, short=31, containers=36)) == [1]
    # Ausgewogen: Kranzeit genau 20 % (Container 60, 20 Doppelspiele): Kriterium 1 erfüllt, bei 19 Doppelspielen nicht
    assert 1 not in failing("Ausgewogen", fake(none=60, bay=41, short=41, johnson=40, bound=30, containers=60))
    assert 1 in failing("Ausgewogen", fake(none=60, bay=42, short=42, johnson=41, bound=30, containers=60))
    # Wenig Laden: Vorsprung genau 1,5 Punkte (Container 200: jedes Doppelspiel spart 0,3 Punkte)
    assert 1 not in failing("Wenig Laden", fake(none=200, bay=180, short=176, johnson=175, bound=100, containers=200))
    assert 1 in failing("Wenig Laden", fake(none=200, bay=180, short=176, johnson=176, bound=100, containers=200))
    # Große Bays: genau 44 % der Spiele
    assert 0 not in failing("Große Bays", fake(none=50, bay=40, short=38, johnson=28, bound=20, containers=50))
    assert 0 in failing("Große Bays", fake(none=50, bay=40, short=38, johnson=29, bound=20, containers=50))
    # Viel Laden (ein Bay): Kranzeit genau 18 % (Container 100, 30 Doppelspiele)
    assert ST.holds("Viel Laden", fake(none=100, bay=80, short=70, johnson=70, bound=50, containers=100)[0])
    assert not ST.holds("Viel Laden", fake(none=100, bay=80, short=71, johnson=71, bound=50, containers=100)[0])
