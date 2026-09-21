"""Tests der Regler-Spezifikation: Permalink-Auswertung (begrenzen, einrasten, Müll ignorieren), Presets innerhalb der Reglergrenzen, Konsistenz mit den Konstanten."""

import dsp_constants as C
import dsp_presets as P
import dsp_scenario as SC

S = P.SETTING_SPECS


def test_parse_clamps_to_range():
    spec = S["n_stacks_slider"]
    assert P.parse_setting(spec, "99") == C.N_STACKS_RANGE[1] and P.parse_setting(spec, "-5") == C.N_STACKS_RANGE[0] and P.parse_setting(spec, "12") == 12
    assert P.parse_setting(S["tiers_slider"], "1") == 2 and P.parse_setting(S["tiers_slider"], "11") == 10


def test_parse_snaps_to_step_from_lower_bound():
    unload, load = S["unload_slider"], S["load_slider"]
    assert P.parse_setting(unload, "23") == 20 and P.parse_setting(unload, "27") == 30 and P.parse_setting(unload, "10") == 10 and P.parse_setting(unload, "100") == 100
    assert P.parse_setting(load, "44") == 40 and P.parse_setting(load, "46") == 50 and P.parse_setting(load, "99") == 100 and P.parse_setting(load, "1") == 10


def test_ratio_is_stored_in_tenths_and_clamped():
    spec = S["ratio_slider"]
    assert P.parse_setting(spec, "14") == 1.4 and P.parse_setting(spec, "10") == 1.0 and P.parse_setting(spec, "19") == 1.9
    assert P.parse_setting(spec, "99") == 1.9 and P.parse_setting(spec, "3") == 1.0 and P.parse_setting(spec, "-5") == 1.0
    assert spec.encoder(1.4) == "14" and spec.encoder(1.0) == "10" and spec.encoder(1.9) == "19"
    for tenths in range(10, 20):
        assert P.parse_setting(spec, spec.encoder(tenths / 10)) == tenths / 10


def test_parse_ignores_garbage():
    for key in ("n_stacks_slider", "seed_input", "unload_slider", "ratio_slider"):
        assert P.parse_setting(S[key], "abc") is None and P.parse_setting(S[key], None) is None and P.parse_setting(S[key], "") is None
    assert P.parse_setting(S["ratio_slider"], "1.4") is None                       # nur ganze Zehntel
    assert P.parse_setting(S["view_radio"], "junk") is None
    assert P.parse_setting(S["view_radio"], "none") is None                        # die Referenz steht immer oben, ist keine Wahl rechts
    assert P.parse_setting(S["view_radio"], "johnson") == "johnson" and P.parse_setting(S["view_radio"], "short") == "short"


def test_step_grid_starts_at_the_lower_bound_not_at_zero():
    spec = P.SettingSpec("x", int, 1, 1, 21, 5)
    assert [P.parse_setting(spec, str(v)) for v in (1, 3, 4, 7, 9, 14, 19, 21)] == [1, 1, 6, 6, 11, 16, 21, 21]


def test_specs_match_constants_and_defaults_inside_bounds():
    assert S["n_stacks_slider"].default == C.N_STACKS_DEFAULT and S["seed_input"].default == C.SEED_DEFAULT == 657 and S["ratio_slider"].default == C.RATIO_DEFAULT == 1.4
    for key, spec in S.items():
        assert P.bounds(key) == (spec.lo, spec.hi)
        if spec.lo is not None:
            assert spec.lo <= spec.default <= spec.hi
            if spec.step and spec.step > 1:
                assert (spec.default - spec.lo) % spec.step == 0
    assert len({spec.url_param for spec in S.values()}) == len(S) and {spec.url_param for spec in S.values()} == {"ns", "tl", "un", "ld", "rt", "seed", "vw"}
    assert S["view_radio"].default in C.RIGHT_VIEW_KEYS and C.BASELINE not in C.RIGHT_VIEW_KEYS


def test_every_preset_is_inside_bounds_on_the_step():
    assert list(C.PRESETS) == ["Nur Löschen", "Ausgewogen", "Viel Laden", "Wenig Laden", "Große Bays"] and all(len(n) <= 16 for n in C.PRESETS)
    for name, p in C.PRESETS.items():
        assert set(p) == set(P.PRESET_STATE_KEYS)
        for field, state_key in P.PRESET_STATE_KEYS.items():
            spec = S[state_key]
            assert spec.lo <= p[field] <= spec.hi, (name, field)
            if spec.step and spec.step > 1:
                assert (p[field] - spec.lo) % spec.step == 0, (name, field)


def test_encoders_roundtrip_through_parse():
    for key, spec in S.items():
        assert P.parse_setting(spec, spec.encoder(spec.default)) == spec.default


def test_scenario_bay_matches_make_bay_and_casts():
    assert P.scenario_bay(10.0, 6.0, 50.0, 50.0, 657.0) == SC.make_bay(10, 6, 50, 50, 657)
    assert P.scenario_bay(10.0, 6.0, 20.0, 80.0, 5.0) == SC.make_bay(10, 6, 20, 80, 5) != SC.make_bay(10, 6, 80, 20, 5)      # Entladen und Beladen nicht vertauscht


def test_preset_state_keys_map_the_right_sliders():
    assert P.PRESET_STATE_KEYS == {"n_stacks": "n_stacks_slider", "tiers": "tiers_slider", "unload_pct": "unload_slider", "load_pct": "load_slider", "ratio": "ratio_slider", "seed": "seed_input"}
