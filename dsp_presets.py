"""Regler-Spezifikation, Permalink, Presets und Seed-Knopf (Standardmuster aus dem OR-Demo-Portfolio, siehe bahn_presets.py)."""

import math
import random
from dataclasses import dataclass
from typing import Callable, Optional

import streamlit as st

import dsp_constants as C
from dsp_scenario import make_bay


def _view(raw):
    if raw not in C.RIGHT_VIEW_KEYS:
        raise ValueError(raw)
    return raw


def _int_text(value):
    return str(int(value))


@dataclass(frozen=True)
class SettingSpec:
    url_param: str
    caster: Callable
    default: object
    lo: Optional[float] = None
    hi: Optional[float] = None
    step: Optional[int] = None
    encoder: Callable = _int_text


def _tenths(raw):
    """Doppelspiel-Kosten stehen in der Adresszeile als ganze Zehntel (14 = 1,4) und werden auf den Reglerbereich begrenzt."""
    return int(raw) / 10


def _tenths_text(value):
    return str(int(round(value * 10)))


SETTING_SPECS = {
    "n_stacks_slider": SettingSpec("ns", int, C.N_STACKS_DEFAULT, *C.N_STACKS_RANGE, 1),
    "tiers_slider": SettingSpec("tl", int, C.TIERS_DEFAULT, *C.TIERS_RANGE, 1),
    "unload_slider": SettingSpec("un", int, C.UNLOAD_PCT_DEFAULT, *C.UNLOAD_PCT_RANGE, C.PCT_STEP),
    "load_slider": SettingSpec("ld", int, C.LOAD_PCT_DEFAULT, *C.LOAD_PCT_RANGE, C.PCT_STEP),
    "ratio_slider": SettingSpec("rt", _tenths, C.RATIO_DEFAULT, *C.RATIO_RANGE, None, _tenths_text),
    "seed_input": SettingSpec("seed", int, C.SEED_DEFAULT, *C.SEED_RANGE, 1),
    "view_radio": SettingSpec("vw", _view, C.VIEW_DEFAULT, encoder=str),
}

PRESET_STATE_KEYS = {
    "n_stacks": "n_stacks_slider", "tiers": "tiers_slider", "unload_pct": "unload_slider", "load_pct": "load_slider", "ratio": "ratio_slider", "seed": "seed_input",
}


def bounds(state_key):
    spec = SETTING_SPECS[state_key]
    return spec.lo, spec.hi


def parse_setting(spec, raw):
    """Wert aus der Adresszeile: umwandeln, auf den Bereich begrenzen, auf die Schrittweite runden. None, wenn er sich nicht auswerten lässt."""
    try:
        value = spec.caster(raw)
    except (ValueError, TypeError):
        return None
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if spec.lo is not None:
        value = max(spec.lo, value)
    if spec.hi is not None:
        value = min(spec.hi, value)
    if spec.step and spec.step > 1 and spec.lo is not None:
        value = spec.lo + round((value - spec.lo) / spec.step) * spec.step
        value = min(spec.hi, value)
    return value


def init_session_state_defaults():
    for state_key, spec in SETTING_SPECS.items():
        if state_key not in st.session_state:
            st.session_state[state_key] = spec.default


def load_permalink_settings():
    if "permalink_loaded" in st.session_state:
        return
    qp = st.query_params
    for state_key, spec in SETTING_SPECS.items():
        if spec.url_param in qp:
            value = parse_setting(spec, qp[spec.url_param])
            if value is not None:
                st.session_state[state_key] = value
    st.session_state["permalink_loaded"] = True


def sync_query_params(values):
    """values: dict state_key -> aktueller Wert (aus den Widgets, damit dieselbe Änderung, die gerade gerendert wurde, sofort in der Adresszeile landet)."""
    try:
        for state_key, value in values.items():
            st.query_params[SETTING_SPECS[state_key].url_param] = SETTING_SPECS[state_key].encoder(value)
    except Exception:
        pass


def apply_preset(name):
    for field, state_key in PRESET_STATE_KEYS.items():
        st.session_state[state_key] = C.PRESETS[name][field]


def scenario_bay(n_stacks, tiers, unload_pct, load_pct, seed):
    return make_bay(int(n_stacks), int(tiers), int(unload_pct), int(load_pct), int(seed))


def randomize_seed():
    """Würfelt einen neuen Seed für den Bay (jeder Bay ist spielbar)."""
    st.session_state["seed_input"] = random.randint(*C.SEED_RANGE)
