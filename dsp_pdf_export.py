"""PDF-Export des Ergebnisses (fpdf2, Helvetica-Kernschrift, nur Text und Tabellen).

Die Kernschriften kennen nur Latin-1: Umlaute und "×" sind erlaubt, aber "–" (Gedankenstrich), "€", "Σ", "≥", "≤", Emoji usw. lassen fpdf2 abstürzen. Deshalb läuft jeder Text durch
pdf_text(); Verfahren erscheinen mit ihren Kurznamen ohne Emoji."""

import time

import dsp_constants as C
import dsp_evaluation as E
import dsp_rules as R

_REPLACEMENTS = {
    "–": "-", "—": "-", "‑": "-", "−": "-", "Σ": "Summe", "δ": "Delta", "≥": ">=", "≤": "<=", "→": "->", "≈": "ca.", "€": "EUR",
    "·": "-", "“": '"', "”": '"', "„": '"', "’": "'", "‘": "'", "±": "+-", "⚠️": "(!)", "⚠": "(!)",
}
N_, B_, S_, J_ = C.STRAT_NONE, C.STRAT_BAY, C.STRAT_SHORT, C.STRAT_JOHNSON


def pdf_text(text):
    """Text für die Helvetica-Kernschrift: bekannte Sonderzeichen ersetzen, den Rest Latin-1-sicher machen."""
    for old, new in _REPLACEMENTS.items():
        text = text.replace(old, new)
    return text.encode("latin-1", "replace").decode("latin-1")


def short_name(key):
    return C.STRATEGY_PLAIN[key]


def verdict_text(sample, label, key, reference):
    """Ein Satz je Vergleich, wie im Kernabschnitt der App (ohne Emoji)."""
    v = E.verdict(sample, key, reference)
    d = E.distribution(sample, key, reference)
    if v.kind == "better":
        amount = f"{abs(v.pct):.0f} % weniger" if v.pct is not None else f"{abs(v.diff):.1f} weniger"
        return f"{label}: im Mittel {amount} Spiele ({v.diff:.1f} je Bay, Standardfehler {v.se:.2f}); in {d.worse * 100:.0f} % der Bays ist es umgekehrt."
    if v.kind == "worse":
        amount = f"{v.pct:.0f} % mehr" if v.pct is not None else f"{v.diff:.1f} mehr"
        return f"{label}: im Mittel {amount} Spiele ({v.diff:+.1f} je Bay, Standardfehler {v.se:.2f}); in {d.better * 100:.0f} % der Bays ist es besser."
    return (f"{label}: kein klarer Unterschied, die Differenz ({v.diff:+.1f} Spiele je Bay) liegt innerhalb des Rauschens (Standardfehler {v.se:.2f}); "
            f"weniger Spiele in {d.better * 100:.0f} %, mehr in {d.worse * 100:.0f} % der Bays.")


def generate_dsp_pdf(bay, outcomes, settings, sample=None, curve=None, compress=True):
    """Ergebnis der aktuellen Einstellung als PDF: Szenario, Zusammenfassung, Verfahrensvergleich, optional Stichprobe/Urteil und Kurve, Hinweise.

    `outcomes`: die vier Outcomes; `settings`: dict mit den Reglerwerten (n_stacks, tiers, unload_pct, load_pct, ratio, seed) oder None für einen eigenen Bay (dann nur Stapelzahlen);
    `sample`: Tupel von ListResult oder None; `curve`: E.Curve oder None."""
    from fpdf import FPDF
    from fpdf.enums import XPos, YPos

    by_key = {o.key: o for o in outcomes}
    ref, best = by_key[N_], by_key[J_]
    bound = R.lower_bound(bay)

    pdf = FPDF()
    pdf.set_compression(compress)
    pdf.add_page()

    def line(text, height=7, width=0):
        pdf.cell(width, height, pdf_text(text), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def heading(text):
        pdf.set_font("Helvetica", "B", 12)
        line(text, 8)
        pdf.set_font("Helvetica", "", 10)

    def pairs(rows):
        for label, value in rows:
            pdf.cell(70, 6, pdf_text(label), border=0)
            line(value, 6)

    def table(headers, widths, rows):
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_fill_color(230, 230, 230)
        for header, width in zip(headers, widths):
            pdf.cell(width, 7, pdf_text(header), border=1, fill=True, new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.ln(7)
        pdf.set_font("Helvetica", "", 9)
        for row in rows:
            for value, width in zip(row, widths):
                pdf.cell(width, 7, pdf_text(str(value)), border=1, new_x=XPos.RIGHT, new_y=YPos.TOP)
            pdf.ln(7)

    def keep_together(height):
        """Beginnt einen Abschnitt auf einer neuen Seite, wenn er sonst über den Seitenumbruch liefe (keine halb abgeschnittenen Listen)."""
        if pdf.get_y() + height > pdf.h - pdf.b_margin:
            pdf.add_page()

    def note(text, size=8):
        pdf.set_font("Helvetica", "I", size)
        pdf.set_text_color(110, 110, 110)
        pdf.multi_cell(0, 5, pdf_text(text), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(0, 0, 0)

    pdf.set_font("Helvetica", "B", 16)
    line("Doppelspiel: Was bringt es, beim Löschen gleich zu laden?", 10)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(120, 120, 120)
    line(f"Erstellt: {time.strftime('%d.%m.%Y %H:%M')}  -  sebastianhanisch.net", 6)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(3)

    s = settings
    r10 = s["ratio10"]
    heading("Szenario")
    rows = [("Bay", f"{bay.n_stacks} Stapel")]
    if s.get("tiers") is not None:
        rows += [("Lagen", str(s["tiers"])), ("Entladeanteil", f"{s['unload_pct']} %"), ("Beladeanteil", f"{s['load_pct']} %"), ("Seed des Bays", str(s["seed"]))]
    else:
        rows += [("Herkunft", "eigener Bay (Eingabe)")]
    rows += [("Zu löschen / zu laden", f"{bay.unloads} / {bay.loads} Container"), ("Doppelspiel kostet", f"{r10 / 10:.1f} Einzelspiele (Annahme)")]
    pairs(rows)
    pdf.ln(3)

    heading("Zusammenfassung")
    pairs([(short_name(o.key), f"{o.cycles} Spiele" + ("" if o.key == N_ else f" ({o.cycles - ref.cycles:+d}), {E.saving_pct(o, ref):.0f} % Kranzeit gespart")) for o in outcomes])
    note(f"Ohne Doppelspiel {ref.cycles} Spiele ({E.minutes(ref.time10):.0f} min), mit der besten Reihenfolge {best.cycles} ({E.minutes(best.time10):.0f} min): "
         f"{E.minutes(ref.time10 - best.time10):.0f} min weniger Kranzeit. Untere Schranke der Spiele: {bound}.", 9)
    pdf.ln(3)

    heading("Verfahrensvergleich")
    table_rows = [[short_name(r.key), r.cycles, r.singles, r.duals, f"{r.minutes:.0f}", f"{r.saving_pct:.0f}", r.gap_to_bound] for r in E.comparison_rows(bay, outcomes)]
    table(["Verfahren", "Spiele", "Einzelspiele", "Doppelspiele", "Minuten", "Zeit gespart (%)", "über Schranke"], [44, 18, 26, 26, 20, 30, 26], table_rows)
    lf_cycles, lf_duals, lf_min = E.largest_first_row(bay, r10)
    note(f"Zum Vergleich: 'Größte Entladung zuerst' braucht {lf_cycles} Spiele ({lf_duals} Doppelspiele, {lf_min:.0f} min) und ist meist schlechter als die Bay-Reihenfolge. "
         "Die Johnson-Regel ist bewiesen optimal (Flow-Shop mit zwei Stufen).")
    pdf.ln(3)

    if sample is not None:
        keep_together(95)
        heading("Stichprobe und Urteil")
        table(["Verfahren", "Spiele im Mittel", "Zeit gespart (%)", "Schranke erreicht (%)"], [50, 40, 42, 42],
              [[short_name(k), f"{E.mean_cycles(sample, k):.1f}", "-" if k == N_ else f"{E.mean_saving_pct(sample, k):.1f}", f"{E.at_bound_share(sample, k) * 100:.0f}"] for k in C.STRATEGY_KEYS])
        pdf.ln(2)
        pdf.set_font("Helvetica", "", 9)
        for label, key, reference in (("Johnson gegen Bay-Reihenfolge", J_, B_), ("Johnson gegen Kurze Entladung", J_, S_), ("Kurze Entladung gegen Bay-Reihenfolge", S_, B_)):
            pdf.multi_cell(0, 5, pdf_text("- " + verdict_text(sample, label, key, reference)), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        note(f"Basis: {len(sample)} Bays (Seeds 0-{len(sample) - 1}, nicht der eingestellte Seed) mit den eingestellten Werten. Klar heißt: Unterschied größer als zwei Standardfehler der gepaarten Differenz.")
        pdf.ln(3)

    if curve is not None:
        keep_together(70)
        heading("Kranzeit gespart über dem Beladeanteil")
        pts = curve.points
        cw = [44] + [max(14, int(146 / len(pts)))] * len(pts)
        rows = [[short_name(k)] + [f"{v:.1f}" for v in E.curve_saving(curve, k)] for k in (B_, S_, J_)]
        table(["Beladeanteil (%)"] + [str(p) for p in pts], cw, rows)
        note(f"Kranzeit gespart in %, Mittel über {curve.n_bays} Bays je Beladeanteil (Seeds 0-{curve.n_bays - 1}), Entladeanteil und Bay-Größe wie eingestellt.")
        pdf.ln(3)

    keep_together(70)
    heading("Hinweise zum Modell")
    pdf.set_font("Helvetica", "", 9)
    for text in [
        "Vereinfachtes Literaturmodell (Goodchild und Daganzo 2006): Stapel als Jobs; ein Stapel muss vollständig geleert sein, bevor in ihn geladen wird.",
        "Keine Fahrzeiten zwischen Stapeln, keine Lukendeckel, keine Trennung Deck/Unterdeck, keine Stabilität; alle Spiele gleich lang, das Doppelspiel kostet r Einzelspiele (Annahme).",
        "Die Regel 'Kurze Entladung zuerst' ist eine eigene Wahl als Faustregel; die Johnson-Regel ist beweisbar optimal und braucht keinen Löser.",
        "Alle Zahlen sind Größenordnungen aus einer Simulation mit zufälligen Bays, keine Messung an echten Kranspielen.",
    ]:
        pdf.multi_cell(0, 5, pdf_text("- " + text), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    return bytes(pdf.output())
