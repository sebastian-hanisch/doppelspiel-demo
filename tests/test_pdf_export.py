import re

import pytest

import dsp_constants as C
import dsp_evaluation as E
import dsp_rules as R
import dsp_scenario as SC
from dsp_evaluation import ListResult
from dsp_pdf_export import generate_dsp_pdf, pdf_text, short_name, verdict_text

N_, B_, S_, J_ = C.STRAT_NONE, C.STRAT_BAY, C.STRAT_SHORT, C.STRAT_JOHNSON


def _settings(name="Ausgewogen", **override):
    p = dict(C.PRESETS[name])
    p.update(override)
    p["ratio10"] = E.ratio10(p.pop("ratio"))
    return p


def _pdf(name="Ausgewogen", compress=False, sample=None, curve=None, bay=None, **override):
    s = _settings(name, **override)
    bay = bay or SC.make_bay(s["n_stacks"], s["tiers"], s["unload_pct"], s["load_pct"], s["seed"])
    outs = E.run_methods(bay, s["ratio10"])
    return generate_dsp_pdf(bay, outs, s, sample=sample, curve=curve, compress=compress), bay, outs, s


def _texts(data):
    """Alle Textstücke des (unkomprimierten) PDFs als Liste, Latin-1 gelesen, PDF-Escapes aufgelöst."""
    raw = re.findall(rb"\((.*?)\)\s*Tj", data)
    return [t.decode("latin-1").replace(r"\(", "(").replace(r"\)", ")").replace(r"\\", "\\") for t in raw]


def _after(text, label):
    return text[text.index(label) + 1]


def lr(seed, **kw):
    v = dict(none=60, bay=40, short=38, johnson=36)
    v.update(kw)
    n = v["none"]
    cycles = {N_: n, B_: v["bay"], S_: v["short"], J_: v["johnson"]}
    return ListResult(seed, 30, 30, cycles, {k: 10 * (n - 2 * (n - c)) + 14 * (n - c) for k, c in cycles.items()}, 33)


# ---------- Sonderzeichen: mit den GENAUEN Zeichen testen (fpdf2 stürzt bei "–" und "€" ab) ----------
EXPECTED = {"–": "-", "—": "-", "−": "-", "€": "EUR", "Σ": "Summe", "δ": "Delta", "≥": ">=", "≤": "<=", "→": "->", "≈": "ca.", "„": '"', "“": '"', "’": "'", "·": "-", "±": "+-",
            "⚠️": "(!)", "⚠": "(!)"}


@pytest.mark.parametrize("char,replacement", list(EXPECTED.items()))
def test_pdf_text_replaces_every_known_troublemaker_with_a_readable_equivalent(char, replacement):
    out = pdf_text(f"a{char}b")
    out.encode("latin-1")
    assert out == f"a{replacement}b"


def test_pdf_text_keeps_umlauts_and_times_sign_and_replaces_unknown():
    assert pdf_text("Füllgrad äöüß ÄÖÜ × 3") == "Füllgrad äöüß ÄÖÜ × 3"
    assert pdf_text("日本語").encode("latin-1") == b"???"
    assert "?" in pdf_text("🧮 Johnson")


def test_short_names_have_no_emoji_and_survive_latin_1():
    for key in C.STRATEGY_KEYS:
        assert pdf_text(short_name(key)) == short_name(key) and "<br>" not in short_name(key)
    assert short_name(J_) == "Johnson" and short_name(S_) == "Kurze Entladung zuerst"


# ---------- Inhalt ----------
def test_pdf_is_a_valid_document_with_all_sections_without_sample():
    data, *_ = _pdf()
    assert data.startswith(b"%PDF") and data.endswith(b"%%EOF\n") and len(data) > 2000
    text = _texts(data)
    for needle in ["Doppelspiel: Was bringt es, beim Löschen gleich zu laden?", "Szenario", "Zusammenfassung", "Verfahrensvergleich", "Hinweise zum Modell"]:
        assert needle in text, needle
    assert "Stichprobe und Urteil" not in text and "Kranzeit gespart über dem Beladeanteil" not in text


def test_pdf_scenario_block_pairs_every_label_with_its_own_value():
    data, bay, outs, s = _pdf()
    text = _texts(data)
    assert _after(text, "Bay") == "10 Stapel" and _after(text, "Lagen") == "6" and _after(text, "Entladeanteil") == "50 %" and _after(text, "Beladeanteil") == "50 %"
    assert _after(text, "Seed des Bays") == "657" and _after(text, "Zu löschen / zu laden") == f"{bay.unloads} / {bay.loads} Container"
    assert _after(text, "Doppelspiel kostet") == "1.4 Einzelspiele (Annahme)"


def test_pdf_scenario_follows_the_settings_and_a_custom_bay_has_no_slider_values():
    data, bay, outs, s = _pdf("Große Bays", ratio=1.9)
    text = _texts(data)
    assert _after(text, "Bay") == "20 Stapel" and _after(text, "Lagen") == "8" and _after(text, "Doppelspiel kostet") == "1.9 Einzelspiele (Annahme)"
    custom = SC.custom_bay([3, 0, 5], [2, 4, 1])
    outs = E.run_methods(custom, 14)
    text2 = _texts(generate_dsp_pdf(custom, outs, dict(ratio10=14), compress=False))
    assert _after(text2, "Bay") == "3 Stapel" and _after(text2, "Herkunft") == "eigener Bay (Eingabe)" and "Lagen" not in text2 and "Seed des Bays" not in text2


def test_pdf_summary_quotes_each_method_with_its_signed_difference_and_saving():
    data, bay, outs, s = _pdf()
    text = _texts(data)
    ref = outs[0]
    assert _after(text, "Ohne Doppelspiel") == f"{ref.cycles} Spiele"
    for o in outs[1:]:
        assert _after(text, short_name(o.key)) == f"{o.cycles} Spiele ({o.cycles - ref.cycles:+d}), {E.saving_pct(o, ref):.0f} % Kranzeit gespart"
    joined = " ".join(text)
    assert f"mit der besten Reihenfolge {outs[3].cycles}" in joined and f"Untere Schranke der Spiele: {R.lower_bound(bay)}" in joined
    assert f"min): {E.minutes(ref.time10 - outs[3].time10):.0f} min weniger Kranzeit" in joined


def test_pdf_comparison_table_rows_are_complete_and_in_column_order():
    data, bay, outs, s = _pdf()
    text = _texts(data)
    start = text.index("über Schranke") + 1
    for i, r in enumerate(E.comparison_rows(bay, outs)):
        row = text[start + 7 * i: start + 7 * i + 7]
        assert row == [short_name(r.key), str(r.cycles), str(r.singles), str(r.duals), f"{r.minutes:.0f}", f"{r.saving_pct:.0f}", str(r.gap_to_bound)], (r.key, row)


def test_pdf_mentions_the_largest_first_rule_with_its_own_numbers():
    data, bay, outs, s = _pdf()
    cycles, duals, minutes = E.largest_first_row(bay, 14)
    joined = " ".join(_texts(data))
    assert f"'Größte Entladung zuerst' braucht {cycles} Spiele ({duals} Doppelspiele, {minutes:.0f} min)" in joined


# ---------- Stichprobe, Urteil, Kurve ----------
def test_pdf_sample_section_lists_means_savings_bound_share_and_the_three_verdicts():
    sample = E.sample(10, 6, 50, 50, 14, n_bays=30)
    text = _texts(_pdf(sample=sample)[0])
    assert "Stichprobe und Urteil" in text
    start = text.index("Schranke erreicht (%)") + 1
    assert text[start: start + 4] == [short_name(N_), f"{E.mean_cycles(sample, N_):.1f}", "-", f"{E.at_bound_share(sample, N_) * 100:.0f}"]
    assert text[start + 4: start + 8] == [short_name(B_), f"{E.mean_cycles(sample, B_):.1f}", f"{E.mean_saving_pct(sample, B_):.1f}", f"{E.at_bound_share(sample, B_) * 100:.0f}"]
    joined = " ".join(text)
    for label in ("Johnson gegen Bay-Reihenfolge", "Johnson gegen Kurze Entladung", "Kurze Entladung gegen Bay-Reihenfolge"):
        assert label in joined
    assert "Basis: 30 Bays (Seeds 0-29, nicht der eingestellte Seed)" in joined


def test_pdf_verdicts_pair_each_label_with_its_own_comparison():
    sample = E.sample(10, 6, 50, 50, 14, n_bays=40)
    joined = " ".join(_texts(_pdf(sample=sample)[0]))
    for label, key, ref in (("Johnson gegen Bay-Reihenfolge", J_, B_), ("Johnson gegen Kurze Entladung", J_, S_), ("Kurze Entladung gegen Bay-Reihenfolge", S_, B_)):
        assert verdict_text(sample, label, key, ref) in joined, label


def test_pdf_curve_section_has_one_row_per_ordering_method_and_one_column_per_point():
    pts = (10, 50, 100)
    cv = E.curve_over_load(10, 6, 50, 14, points=pts, n_bays=20)
    text = _texts(_pdf(curve=cv)[0])
    assert "Kranzeit gespart über dem Beladeanteil" in text
    start = text.index("Beladeanteil (%)") + 1
    assert text[start: start + 3] == ["10", "50", "100"]
    assert text[start + 3: start + 7] == [short_name(B_)] + [f"{v:.1f}" for v in E.curve_saving(cv, B_)]
    assert text[start + 7: start + 11] == [short_name(S_)] + [f"{v:.1f}" for v in E.curve_saving(cv, S_)]
    assert text[start + 11: start + 15] == [short_name(J_)] + [f"{v:.1f}" for v in E.curve_saving(cv, J_)]
    assert "Mittel über 20 Bays je Beladeanteil (Seeds 0-19)" in " ".join(text)


@pytest.mark.parametrize("kind", ["better", "worse", "unclear"])
def test_verdict_text_covers_all_states(kind):
    if kind == "better":
        sample = tuple(lr(i, bay=40, johnson=36 + i % 2) for i in range(10))
    elif kind == "worse":
        sample = tuple(lr(i, bay=40, johnson=44 + i % 2) for i in range(10))
    else:
        sample = tuple(lr(i, bay=40, johnson=40 + (i % 2) * 2 - 1) for i in range(10))
    text = verdict_text(sample, "L", J_, B_)
    assert text.startswith("L:") and {"better": "% weniger Spiele", "worse": "% mehr Spiele", "unclear": "kein klarer Unterschied"}[kind] in text
    text.encode("latin-1")


def test_verdict_text_direction_and_reverse_shares():
    mixed_better = tuple(lr(i, bay=40, johnson=(34 if i < 16 else 41)) for i in range(20))
    t = verdict_text(mixed_better, "L", J_, B_)
    assert "weniger Spiele" in t and "in 20 % der Bays ist es umgekehrt" in t
    mixed_worse = tuple(lr(i, bay=40, johnson=(46 if i < 16 else 39)) for i in range(20))
    t = verdict_text(mixed_worse, "L", J_, B_)
    assert "mehr Spiele" in t and "in 20 % der Bays ist es besser" in t


def test_verdict_text_without_a_percentage_when_the_reference_needs_no_cycles():
    sample = tuple(ListResult(i, 0, 1, {N_: 1, B_: 0, S_: 0, J_: 1}, {N_: 10, B_: 0, S_: 0, J_: 10}, 0) for i in range(6))
    t = verdict_text(sample, "L", J_, B_)
    assert "1.0 mehr Spiele" in t and "%" not in t.split("(")[0]


def test_verdict_text_better_without_a_percentage_is_defensive_and_does_not_crash(monkeypatch):
    monkeypatch.setattr(E, "verdict", lambda res, key, ref: E.Verdict("better", -2.0, 0.5, None, 20, 0.25))
    sample = tuple(lr(i) for i in range(4))
    t = verdict_text(sample, "L", J_, B_)
    assert "im Mittel 2.0 weniger Spiele (-2.0 je Bay" in t and "%" not in t.split("(")[0]


# ---------- Ränder ----------
@pytest.mark.parametrize("name", list(C.PRESETS))
def test_pdf_is_generated_for_every_preset_compressed_and_uncompressed(name):
    for compress in (True, False):
        data = _pdf(name, compress=compress)[0]
        assert data.startswith(b"%PDF") and len(data) > 1500


def test_pdf_at_the_limits_stays_valid():
    tiny = _pdf(n_stacks=4, tiers=2, unload_pct=10, load_pct=10, ratio=1.0)[0]
    big = _pdf(n_stacks=20, tiers=10, unload_pct=100, load_pct=100, ratio=1.9)[0]
    one_container = SC.custom_bay([1], [0])
    data = generate_dsp_pdf(one_container, E.run_methods(one_container, 14), dict(ratio10=14), compress=False)
    assert tiny.startswith(b"%PDF") and big.startswith(b"%PDF") and data.startswith(b"%PDF")


def _pages(data):
    """Textstücke je Seite (unkomprimiertes PDF: ein Inhaltsstrom je Seite)."""
    streams = re.findall(rb"stream\r?\n(.*?)endstream", data, re.S)
    return [[t.decode("latin-1") for t in re.findall(rb"\((.*?)\)\s*Tj", s)] for s in streams]


def test_pdf_sections_are_not_split_across_pages():
    sample = E.sample(10, 6, 50, 50, 14)
    cv = E.curve_over_load(10, 6, 50, 14, n_bays=10)
    pages = _pages(_pdf(sample=sample, curve=cv)[0])
    assert len(pages) <= 3
    for head, last in (("Stichprobe und Urteil", "Differenz."), ("Kranzeit gespart über dem Beladeanteil", "Bay-Größe wie eingestellt."), ("Hinweise zum Modell", "echten Kranspielen.")):
        page = next(p for p in pages if head in p)
        assert last in " ".join(page), head
        assert page.index(head) < len(page) - 3, head
