"""Jedes Preset erzählt eine Geschichte (Abnahmekriterien in dsp_stories.py). Hier wird geprüft, dass sie trägt:

1. an dem EINEN Bay, den das Preset zeigt (sonst zeigt das Preset das Gegenteil seines Hilfetexts),
2. im MITTEL über 200 andere Bays (sonst ist das Preset ein Einzelfall, ausgesucht nach dem schönsten Seed),
3. dass der gewählte Bay typisch ist: bei jeder Kennzahl zwischen dem 10. und 90. Perzentil der Bays.

(Die Schwellen selbst prüft test_stories.py mit künstlichen Werten.) Alles ist ganzzahlig und deterministisch, kein Löser und keine Zeitgrenze: die Tests hängen nicht vom Rechner ab."""

import pytest

import dsp_constants as C
import dsp_evaluation as E
import dsp_stories as ST

NAMES = list(C.PRESETS)
_cache = {}


def _run(name, seed):
    p = C.PRESETS[name]
    return E.run_bay(p["n_stacks"], p["tiers"], p["unload_pct"], p["load_pct"], E.ratio10(p["ratio"]), seed)


def _population(name):
    if name not in _cache:
        p = C.PRESETS[name]
        _cache[name] = E.sample(p["n_stacks"], p["tiers"], p["unload_pct"], p["load_pct"], E.ratio10(p["ratio"]))
    return _cache[name]


# ---------------- 1. am gezeigten Bay ----------------
@pytest.mark.parametrize("name", NAMES)
def test_the_story_holds_on_the_bay_the_preset_shows(name):
    r = _run(name, C.PRESETS[name]["seed"])
    assert ST.holds(name, r), (name, r)


def test_presets_share_one_bay_number_and_only_change_what_the_story_needs():
    assert len({p["seed"] for p in C.PRESETS.values()}) == 1 and len({p["ratio"] for p in C.PRESETS.values()}) == 1 and len({p["unload_pct"] for p in C.PRESETS.values()}) == 1
    assert [C.PRESETS[n]["load_pct"] for n in NAMES] == [10, 50, 80, 20, 50]
    assert [(C.PRESETS[n]["n_stacks"], C.PRESETS[n]["tiers"]) for n in NAMES] == [(10, 6), (10, 6), (10, 6), (10, 6), (20, 8)]


# ---------------- 2. im Mittel der Grundgesamtheit ----------------
@pytest.mark.parametrize("name", NAMES)
def test_the_story_holds_on_average_over_many_bays(name):
    failed = [text for ok, text in ST.criteria(name, _population(name)) if not ok]
    assert not failed, failed


def test_the_population_does_not_contain_the_preset_seed():
    assert C.PRESETS["Ausgewogen"]["seed"] >= C.SAMPLE_BAYS                       # sonst wäre die Grundgesamtheit nicht unabhängig vom gezeigten Fall


# ---------------- 3. der gezeigte Bay ist typisch ----------------
def _pct(values, q):
    v = sorted(values)
    return v[int(q * (len(v) - 1))]


@pytest.mark.parametrize("name,key", ST.TYPICAL)
def test_the_shown_bay_is_typical(name, key):
    pop = [r.cycles[key] for r in _population(name)]
    shown = _run(name, C.PRESETS[name]["seed"]).cycles[key]
    assert _pct(pop, 0.1) <= shown <= _pct(pop, 0.9), (name, key, shown, sorted(pop))
