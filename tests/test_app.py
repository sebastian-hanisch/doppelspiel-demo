"""AppTest: Skelett und Footer, jedes Preset, Permalink, alle Regler an Min und Max, Kennzahlen im 2 x 2-Raster, Stichprobe, Kurve und Urteil, Johnson-Tab mit Gegenprobe, eigener Bay,
Vergleichstabelle, PDF, Texte."""

import pathlib

import pytest
from streamlit.proto.Metric_pb2 import Metric as MetricProto
from streamlit.testing.v1 import AppTest

import dsp_constants as C
import dsp_evaluation as E
from dsp_presets import SETTING_SPECS

APP = str(pathlib.Path(__file__).resolve().parent.parent / "app.py")
FOOTER = ("Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
          "Operations Research und Machine Learning. Interesse an einer maßgeschneiderten Lösung für "
          "Ihr Unternehmen? [Kontakt aufnehmen](https://sebastianhanisch.net/kontakt.html)")
N_, B_, S_, J_ = C.STRAT_NONE, C.STRAT_BAY, C.STRAT_SHORT, C.STRAT_JOHNSON

# Spiele je Verfahren an Seed 657 (Preset-Bay), r = 1,4
EXPECTED = {"Nur Löschen": [34, 31, 30, 30], "Ausgewogen": [60, 36, 33, 31], "Viel Laden": [78, 52, 49, 49], "Wenig Laden": [42, 32, 31, 30], "Große Bays": [160, 93, 85, 85]}


def fresh(**query):
    at = AppTest.from_file(APP, default_timeout=120)
    for k, v in query.items():
        at.query_params[k] = v
    at.run()
    assert not at.exception, at.exception
    return at


def set_and_run(at, **values):
    for key, value in values.items():
        (at.number_input if key.endswith("_input") else at.slider)(key=key).set_value(value)
    at.run()
    assert not at.exception, at.exception
    return at


def main_metrics(at):
    return [(m.label, m.value, m.delta) for m in at.metric[:4]]


def click(at, label):
    next(b for b in at.button if b.label == label).click().run()
    assert not at.exception, at.exception
    return at


# ---------------------------------------------------------------------------------------------------
# Skelett
# ---------------------------------------------------------------------------------------------------
def test_skeleton_and_footer():
    at = fresh()
    assert [h.value for h in at.sidebar.header] == ["⚙️ Einstellungen"]                # genau EIN Header
    assert len(at.title) == 1 and "Doppelspiel" in at.title[0].value
    assert any(v.value.startswith("## 🎯") for v in at.markdown)
    assert [s.value for s in at.subheader] == ["📐 Was ist die Reihenfolge wert?"]
    assert [e.label for e in at.expander] == ["🔧 Wie wir das erreichen – vollständiger Methodenvergleich", "Wie funktioniert diese Demo?", "📐 Mathematische Formulierung"]
    assert any(c.value == FOOTER for c in at.caption)
    presets = [b.label for b in at.button if b.label in C.PRESETS]
    assert presets == list(C.PRESETS) and len(presets) == 5 and all(len(n) <= 16 for n in presets)


def test_main_metrics_are_2x2_with_the_four_strategies_and_signed_deltas():
    at = fresh()
    assert [m[0] for m in main_metrics(at)] == [C.STRATEGY_LABELS[k] for k in C.STRATEGY_KEYS]
    assert [m[1] for m in main_metrics(at)] == ["60", "36", "33", "31"]
    assert [m[2] for m in main_metrics(at)] == ["", "-24", "-27", "-29"]
    colors = [m.proto.color for m in at.metric[:4]]
    assert colors[1:] == [MetricProto.GREEN] * 3                                          # weniger Spiele = besser = grün ("inverse")
    assert all(len(m[0]) <= 24 for m in main_metrics(at))


def test_main_message_states_cycles_minutes_saving_and_the_gap_to_the_bound():
    at = fresh()
    msg = [i.value for i in at.info if "Ohne Doppelspiel braucht" in i.value][0]
    assert "**60 Spiele** (120 min)" in msg and "In Bay-Reihenfolge sind es 36" in msg and "**31** (85 min)" in msg and "**29 Spiele weniger, 29 % Kranzeit gespart**" in msg
    assert "Die untere Schranke liegt bei 30; Johnson liegt 1 darüber: bewiesen das Beste" in msg
    assert len(at.get("plotly_chart")) >= 9                                             # 2 Spielfolgen + Reihenfolge + Verteilung + Gewinn + Kurve + 4 Tabs (je 2) ...
    assert any("blau = Einzelspiel Entladen" in c.value for c in at.caption)


def test_message_says_the_bound_is_reached_when_it_is():
    at = click(fresh(), "Nur Löschen")
    msg = [i.value for i in at.info if "Ohne Doppelspiel braucht" in i.value][0]
    assert "Die untere Schranke (30) ist erreicht: mehr geht nicht." in msg


def test_core_section_metrics_show_unloads_loads_and_the_bound():
    at = fresh()
    assert [(m.label, m.value) for m in at.metric[4:7]] == [("Zu löschen", "30"), ("Zu laden", "30"), ("Untere Schranke", "30 Spiele")]


# ---------------------------------------------------------------------------------------------------
# Presets, Permalink
# ---------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("name", list(C.PRESETS))
def test_every_preset_loads_within_widget_bounds_and_shows_its_story(name):
    at = fresh()
    click(at, name)
    p = C.PRESETS[name]
    assert at.slider(key="load_slider").value == p["load_pct"] and at.slider(key="n_stacks_slider").value == p["n_stacks"] and at.number_input(key="seed_input").value == p["seed"]
    for state_key, spec in SETTING_SPECS.items():
        if spec.lo is not None:
            value = at.session_state[state_key]
            assert spec.lo <= value <= spec.hi and (spec.step in (None, 1) or (value - spec.lo) % spec.step == 0)
    assert [int(m[1]) for m in main_metrics(at)] == EXPECTED[name]


def test_permalink_is_clamped_snapped_and_ignores_garbage():
    at = fresh(ld="47", un="23", vw="junk", ns="abc", rt="99", tl="1")
    assert at.slider(key="load_slider").value == 50 and at.slider(key="unload_slider").value == 20
    assert at.radio(key="view_radio").value == C.VIEW_DEFAULT and at.slider(key="n_stacks_slider").value == C.N_STACKS_DEFAULT
    assert at.slider(key="ratio_slider").value == 1.9 and at.slider(key="tiers_slider").value == 2


def test_permalink_roundtrip_reflects_settings():
    at = fresh(ns="6", tl="4", un="30", ld="70", rt="12", seed="11", vw="short")
    assert at.slider(key="n_stacks_slider").value == 6 and at.slider(key="tiers_slider").value == 4 and at.slider(key="unload_slider").value == 30
    assert at.slider(key="load_slider").value == 70 and at.slider(key="ratio_slider").value == 1.2 and at.number_input(key="seed_input").value == 11
    assert at.radio(key="view_radio").value == "short"
    assert at.query_params["rt"] in ("12", ["12"]) and at.query_params["ld"] in ("70", ["70"])


def test_seed_button_uses_the_random_draw_unchanged(monkeypatch):
    import random
    monkeypatch.setattr(random, "randint", lambda lo, hi: hi)
    at = click(fresh(), "🎲 Neuer Bay")
    assert at.number_input(key="seed_input").value == C.SEED_RANGE[1]


def test_seed_button_changes_only_the_seed():
    at = fresh()
    before = {k: at.session_state[k] for k in SETTING_SPECS if k != "seed_input"}
    click(at, "🎲 Neuer Bay")
    assert {k: at.session_state[k] for k in SETTING_SPECS if k != "seed_input"} == before
    assert C.SEED_RANGE[0] <= at.number_input(key="seed_input").value <= C.SEED_RANGE[1]


# ---------------------------------------------------------------------------------------------------
# Regler an den Grenzen
# ---------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("key,value", [
    ("n_stacks_slider", 4), ("n_stacks_slider", 20), ("tiers_slider", 2), ("tiers_slider", 10), ("unload_slider", 10), ("unload_slider", 100), ("load_slider", 10), ("load_slider", 100),
    ("ratio_slider", 1.0), ("ratio_slider", 1.9), ("seed_input", 0), ("seed_input", 9999),
])
def test_every_slider_at_min_and_max(key, value):
    at = set_and_run(fresh(), **{key: value})
    assert len(at.get("plotly_chart")) >= 6 and [m[0] for m in main_metrics(at)] == [C.STRATEGY_LABELS[k] for k in C.STRATEGY_KEYS]


def test_smallest_and_largest_bays_and_extreme_ratios():
    small = set_and_run(fresh(), n_stacks_slider=4, tiers_slider=2, unload_slider=10, load_slider=10)
    assert all(int(m[1]) >= 1 for m in main_metrics(small))
    big = set_and_run(fresh(), n_stacks_slider=20, tiers_slider=10, unload_slider=100, load_slider=100)
    assert [int(m[1]) for m in main_metrics(big)][0] == 400 and int(main_metrics(big)[3][1]) < 400
    no_gain = set_and_run(fresh(), ratio_slider=1.9)
    assert [int(m[1]) for m in main_metrics(no_gain)] == EXPECTED["Ausgewogen"]         # die Spielzahl hängt nicht vom Verhältnis ab, nur die Minuten
    assert any("Doppelspiel dauert" in c.value or "1.9" in c.value for c in no_gain.caption)


def test_the_ratio_changes_minutes_but_never_the_order_or_the_cycles():
    a, b = fresh(), set_and_run(fresh(), ratio_slider=1.0)
    assert [m[1] for m in main_metrics(a)] == [m[1] for m in main_metrics(b)]
    ma = [i.value for i in a.info if "Ohne Doppelspiel braucht" in i.value][0]
    mb = [i.value for i in b.info if "Ohne Doppelspiel braucht" in i.value][0]
    assert "(85 min)" in ma and "(62 min)" in mb                                        # bei Verhältnis 1,0 kostet ein Doppelspiel wie ein Einzelspiel: 31 Spiele = 62 min


# ---------------------------------------------------------------------------------------------------
# Stichprobe, Kurve, Urteil (immer da, ohne Knopf)
# ---------------------------------------------------------------------------------------------------
def test_sample_verdicts_distribution_and_curve_are_shown_without_a_button():
    at = fresh()
    texts = [x.value for x in list(at.success) + list(at.warning) + list(at.info)]
    assert any("Johnson gegen Bay-Reihenfolge" in t for t in texts) and any("Johnson gegen Kurze Entladung zuerst" in t for t in texts) and any("Kurze Entladung zuerst gegen Bay-Reihenfolge" in t for t in texts)
    caps = " ".join(c.value for c in at.caption)
    assert "Basis: 200 Bays (Seeds 0-199, nicht Ihr Seed)" in caps and "Basis: 10 Beladeanteile × 100 Bays (Seeds 0-99)" in caps
    assert not [b for b in at.button if "berechnen" in b.label]


def test_real_verdicts_johnson_beats_the_bay_order_and_short_first_is_unclear_or_better_against_johnson_only_when_true():
    at = fresh()
    assert [s for s in at.success if "Johnson gegen Bay-Reihenfolge" in s.value and "weniger" in s.value]
    sample = E.sample(10, 6, 50, 50, 14)
    v = E.verdict(sample, J_, S_)
    matching = [x for x in list(at.success) + list(at.warning) + list(at.info) if "Johnson gegen Kurze Entladung zuerst" in x.value]
    assert len(matching) == 1 and ({"better": "weniger", "worse": "mehr", "unclear": "Kein klarer"}[v.kind] in matching[0].value)


def test_stale_state_cannot_happen_the_sample_follows_every_setting():
    at = fresh()
    before = " ".join(c.value for c in at.caption if "Im Mittel" in c.value)
    set_and_run(at, load_slider=20)
    after = " ".join(c.value for c in at.caption if "Im Mittel" in c.value)
    assert before != after
    set_and_run(at, seed_input=5)                                                        # der Seed ändert die Stichprobe nicht
    assert " ".join(c.value for c in at.caption if "Im Mittel" in c.value) == after


def _fake_verdict(monkeypatch, kind, pct):
    monkeypatch.setattr(E, "verdict", lambda res, key, ref: E.Verdict(kind, -2.0 if kind == "better" else 2.0, 0.5, pct, 20, 0.25))


@pytest.mark.parametrize("kind,pct,expected", [
    ("better", -40.0, "im Mittel **40.0 % weniger** Spiele (-2.00 je Bay, Standardfehler 0.50)."),
    ("better", None, "im Mittel **2.0 weniger** Spiele (-2.00 je Bay, Standardfehler 0.50)."),
    ("worse", 25.0, "im Mittel **25.0 % mehr** Spiele (+2.00 je Bay, Standardfehler 0.50)."),
    ("worse", None, "im Mittel **2.0 mehr** Spiele (+2.00 je Bay, Standardfehler 0.50)."),
])
def test_verdict_sentences_in_the_four_variants(monkeypatch, kind, pct, expected):
    import streamlit as st
    st.cache_data.clear()
    _fake_verdict(monkeypatch, kind, pct)
    at = fresh()
    texts = [x.value for x in (at.success if kind == "better" else at.warning) if "im Mittel" in x.value and "Spiele" in x.value]
    assert len(texts) == 3 and all(expected in t for t in texts)
    assert all(t.count("(") == t.count(")") for t in texts)


def test_verdict_unclear(monkeypatch):
    _fake_verdict(monkeypatch, "unclear", 1.0)
    at = fresh()
    us = [i.value for i in at.info if "Kein klarer Unterschied" in i.value]
    assert len(us) == 3 and all("Rauschens" in u for u in us)


# ---------------------------------------------------------------------------------------------------
# Methodenvergleich
# ---------------------------------------------------------------------------------------------------
def test_comparison_table_lists_all_strategies_and_the_largest_first_row():
    at = fresh()
    df = next(d.value for d in at.dataframe if "Verfahren" in d.value.columns)
    assert list(df["Verfahren"]) == [C.STRATEGY_LABELS[k] for k in C.STRATEGY_KEYS] + [C.UDESC_LABEL]
    assert list(df["Spiele"])[:4] == [60, 36, 33, 31] and list(df["Differenz zu Ohne Doppelspiel"])[:4] == [0, -24, -27, -29] and list(df["über der Schranke"])[:4] == [30, 6, 3, 1]
    assert list(df["Doppelspiele"])[:4] == [0, 24, 27, 29] and list(df["Minuten"])[:4] == [120, 91, 88, 85]
    assert df.loc[4, "Spiele"] > df.loc[1, "Spiele"]                                    # größte Entladung zuerst ist schlechter als die Bay-Reihenfolge


def test_johnson_tab_shows_the_order_table_and_the_brute_force_check_only_for_small_bays():
    at = fresh()
    assert any("Die Gegenprobe (alle Reihenfolgen durchprobieren) gibt es bis 7 Stapel; hier sind es 10." in c.value for c in at.caption)
    small = set_and_run(fresh(), n_stacks_slider=6)
    assert any("Gegenprobe: alle 720 Reihenfolgen durchprobiert, keine braucht weniger als" in s.value for s in small.success)
    seven = set_and_run(fresh(), n_stacks_slider=7)
    assert any("alle 5040 Reihenfolgen" in s.value for s in seven.success)
    assert not small.error


def test_custom_bay_tab_computes_and_rejects_bad_input():
    at = fresh()
    assert any("Johnson-Reihenfolge:" in c.value for c in at.caption)
    at.text_input(key="custom_u").set_value("3, 0, 5").run()
    assert any("gleich viele Stapel" in w.value for w in at.warning)
    at.text_input(key="custom_l").set_value("2, 4, 1").run()
    assert not at.exception and any("Johnson-Reihenfolge: " in c.value and "untere Schranke 8 Spiele" in c.value for c in at.caption)
    at.text_input(key="custom_u").set_value("3, x, 5").run()
    assert any("keine ganze Zahl" in w.value for w in at.warning)
    at.text_input(key="custom_u").set_value("0, 0, 0").run()
    at.text_input(key="custom_l").set_value("0, 0, 0").run()
    assert any("mindestens ein Container" in w.value for w in at.warning)


# ---------------------------------------------------------------------------------------------------
# PDF
# ---------------------------------------------------------------------------------------------------
def test_pdf_download_button_is_in_the_main_view_and_survives_edge_scenarios():
    at = fresh()
    buttons = at.get("download_button")
    assert len(buttons) == 1 and "PDF" in buttons[0].proto.label and buttons[0].proto.url.endswith(".pdf")
    assert not at.sidebar.get("download_button")
    for values in (dict(load_slider=10), dict(load_slider=100), dict(n_stacks_slider=4, tiers_slider=2), dict(n_stacks_slider=20, tiers_slider=10)):
        assert len(set_and_run(at, **values).get("download_button")) == 1


# ---------------------------------------------------------------------------------------------------
# Texte
# ---------------------------------------------------------------------------------------------------
def test_texts_mention_limits_and_no_dead_file_links():
    at = fresh()
    md = "\n".join(m.value for m in at.markdown)
    assert "Grenzen dieses Modells" in md and "Größenordnungen aus einer Simulation" in md and "Keine Fahrzeiten" in md
    assert "Literaturmodell" in md and "Goodchild und Daganzo 2006" in md and "Johnson" in md
    assert "](" not in md.replace("https://sebastianhanisch.net", "")
    for word in ("Doppelspiel", "Einzelspiel", "Reihenfolge", "Mathematische Formulierung", "Flow-Shop"):
        assert word in md
    for ascii_form in ("Loeschen", "Doppelspiele fahren", "Groesse", "Reihenfolge der Staple"):
        assert ascii_form not in md
