# Doppelspiel: Was bringt es, beim Löschen gleich zu laden? – Streamlit-Demo

**[→ Demo live ausprobieren](https://sebastianhanisch-doppelspiel-demo.streamlit.app/)**

Interaktive Fall-Demo zum **Doppelspiel am Containerkran**: Ein Kran löscht und lädt meist nacheinander und fährt dabei oft leer zurück. Beim Doppelspiel setzt er nach dem Löschen gleich einen
Container auf das Schiff. Geladen werden darf nur in einen Stapel, der schon leer ist; deshalb entscheidet die **Reihenfolge der Stapel** eines Bays, wie oft sich zwei Aufgaben paaren lassen.
Die Demo beantwortet: **Wie viel Kranzeit spart das Doppelspiel, und wie viel davon hängt an der Reihenfolge?**

Teil des Portfolios für die Website „Sebastian Hanisch – Operations Research und Machine Learning", Zusatz zur Hafen-Linie (Kran; setzt auf der Kran-Demo `quaycrane-demo` auf und koppelt
über die Lade- und Löschlisten an die Stauplanung `stauplanung-demo`).

## Warum dieses Problem

Das Problem ist **polynomial exakt lösbar**: Die Spielzahl zu einer Stapelreihenfolge ist die Laufzeit eines Flow-Shops mit zwei Stufen (Löschen, Laden), und Johnson hat dafür 1954 die beste
Reihenfolge bewiesen (Goodchild und Daganzo 2006 haben es aufs Doppelspiel übertragen). Es braucht keinen Löser. Trotzdem ist die Reihenfolge nicht egal: die naheliegende Bay-Reihenfolge
verschenkt Spiele, und „größte Entladung zuerst“ ist sogar schlechter. Die Demo zeigt, **was das Doppelspiel bringt** (15 bis 28 % Kranzeit je Bay) und **wie viel davon die Reihenfolge ausmacht**.

## Modell

Ein Bay aus *S* Stapeln; Stapel *i* hat *u*<sub>i</sub> zu löschende und *l*<sub>i</sub> zu ladende Container (ganzzahlig, aus dem Seed gezogen: je Lage wird mit dem eingestellten Anteil gelöscht
beziehungsweise geladen). Ein Stapel muss **vollständig gelöscht** sein, bevor in ihn geladen wird. Ein Kranspiel ist ein **Einzelspiel** (löschen oder laden) oder ein **Doppelspiel** (aus einem
Stapel löschen und in einen anderen, schon leeren Stapel laden). Ein Doppelspiel kostet *r* Einzelspiele (Annahme *r* = 1,4, Regler 1,0 bis 1,9); ein Einzelspiel dauert 2 Minuten (30 Spiele je
Stunde, wie in der Kran-Demo). Zeit = *U* + *L* − (2 − *r*)·*D* mit *D* = Zahl der Doppelspiele: für jedes *r* < 2 minimiert dieselbe Reihenfolge Spiele und Zeit. Formal im Expander
„📐 Mathematische Formulierung“.

## Methodik – vier Verfahren und eine Schranke

Alle Verfahren arbeiten denselben Bay ab; Referenz aller Vergleiche ist **Ohne Doppelspiel**.

- **Ohne Doppelspiel**: erst alles löschen, dann alles laden, nur Einzelspiele: so viele Spiele wie Container.
- **Bay-Reihenfolge**: die Stapel von links nach rechts leeren, jedes Löschen paart sich mit einer offenen Ladung eines schon leeren Stapels.
- **Kurze Entladung zuerst**: aufsteigend nach der Löschzahl (die kluge Faustregel).
- **Johnson (exakt)**: erst die Stapel mit *u* ≤ *l* aufsteigend nach *u*, dann die mit *u* > *l* absteigend nach *l*. Beweisbar die wenigsten Spiele.
- **Untere Schranke** (kein Verfahren): max(zu löschen, zu laden), weil jedes Spiel höchstens einen Container löscht und einen lädt.

Die **Gegenprobe** probiert bei bis zu 7 Stapeln alle Reihenfolgen durch und bestätigt Johnson in der App. Die **Stichprobe** (200 Bays mit den Seeds 0 bis 199, nicht der eingestellte Seed) und die
**Kurve** über den Beladeanteil (10 Anteile × 100 Bays) rechnen in Millisekunden und brauchen keinen Knopf. Ein Tab „Eigener Bay“ rechnet eingegebene Löschzahlen und Ladezahlen je Stapel.

## Befunde (gemessen, keine Behauptungen)

10 Stapel, 6 Lagen, Entladeanteil 50 %, *r* = 1,4; Zahlen aus `tools/PRESET_SWEEP.md` und der Vorab-Messreihe (`hafen-planung/messreihe_doppel/ERGEBNIS.md`).

| Frage | Befund |
|---|---|
| **Stimmt Johnson?** | Ja: Johnson = bestes Ergebnis über alle 720 Reihenfolgen in 300 von 300 Kleinstbays (6 Stapel); und gleich dem **echten Optimum des Kranmodells** (Zustandssuche über alle Spielfolgen, auch mit teilweisem Löschen mehrerer Stapel) in 60 von 60 Bays mit 4 Stapeln. |
| **Was bringt das Doppelspiel?** | Kranzeit gespart (Bay-Reihenfolge / kurze Entladung / Johnson): bei 20 % Beladung 14,9 / 15,2 / **16,7 %**, bei 50 % 23,7 / 25,4 / **26,7 %**, bei 80 % 20,7 / 22,2 / **22,2 %**. Am größten, wenn Laden und Löschen ausgewogen sind. |
| **Wie viel macht die Reihenfolge aus?** | Bei 50 %: 59,4 Spiele ohne Doppelspiel, 35,9 in Bay-Reihenfolge, 34,2 mit kurzer Entladung, **32,9 mit Johnson**; Johnson braucht in 92 % der Bays weniger Spiele als die Bay-Reihenfolge. „Größte Entladung zuerst“ ist schlechter als die Bay-Reihenfolge. |
| **Reicht die Faustregel?** | Bei viel Beladung (80 %): ja, „kurze Entladung zuerst“ = Johnson in 200 von 200 Bays. Bei wenig Beladung (20 %) liegt Johnson in 140 von 200 Bays vorn. |
| **Erreicht man die untere Schranke?** | Bei wenig Beladung fast immer (94 % der Bays), bei ausgewogener Beladung in 18 %, bei 20 × 8 Stapeln in 6 %: dort ist die Schranke nicht erreichbar, Johnson bleibt das Beste. |
| **Presets** | Eine gemeinsame Bay-Nummer (Seed 657) für alle fünf; jede Kennzahl zwischen dem 10. und 90. Perzentil der Grundgesamtheit. Von 500 Seeds tragen 285 alle fünf Geschichten. |

## Ehrliche Grenzen

- **Vereinfachtes Literaturmodell** (Goodchild und Daganzo 2006): Stapel als Aufträge, ein Stapel wird erst ganz geleert, dann beladen.
- **Keine Fahrzeiten** zwischen Stapeln, **keine Lukendeckel** und keine Trennung Deck/Unterdeck, **keine Stabilität** beim Laden; alle Spiele gleich lang.
- Das **Verhältnis 1,4** (Doppelspiel gegen Einzelspiel) ist eine Annahme; die beste Reihenfolge ist für jedes Verhältnis unter 2 dieselbe, nur die Minuten ändern sich.
- **Kurze Entladung zuerst** ist meine Wahl als Faustregel; die Löschzahlen und Ladezahlen sind zufällig gezogen, nicht aus einem echten Stauplan.
- Alle Zahlen sind **Größenordnungen aus einer Simulation, keine Messung an echten Kranspielen.**

## Design-Entscheidungen und Funde

**Kein Löser, dafür eine Gegenprobe.** Weil Johnson bewiesen optimal ist, gibt es keine Beweislage wie bei den Löser-Demos. Damit die Aussage trotzdem überprüfbar bleibt, probiert die App bei kleinen
Bays alle Reihenfolgen durch, und die Tests vergleichen Johnson mit einer **unabhängigen Zustandssuche** über alle Spielfolgen (nicht nur über Blockreihenfolgen): Die Annahme „Stapel als Blöcke
abarbeiten“ verliert also nichts.

**Der Aufhänger wurde nach der Messung verschoben.** Naheliegend wäre „Faustregel gegen exakten Löser“ gewesen. Gemessen holt die einfache Regel bei viel Beladung fast alles; die Demo fragt deshalb, was das
Doppelspiel bringt und wie viel davon an der Reihenfolge hängt, und sagt im Text, dass die Reihenfolge nur einen Teil des Gewinns ausmacht.

**Alles ganzzahlig, alles deterministisch.** Die Kranzeit rechnet in Zehnteln eines Einzelspiels, das Verhältnis steht in der Adresszeile als ganze Zehntel (14 = 1,4). Es gibt keine Zeitgrenze und keinen Löser:
die Preset-Kriterien und Tests hängen nicht vom Rechner ab (Lehre aus der Schiffsstau- und Bahn-Demo, wo Löser-Zeitlimits auf der CI kippten).

**Preset-Kriterien an Schwellen geprüft.** Jedes Kriterium hat einen Test mit künstlichen Werten, der einzeln an seiner Schwelle kippt; die Schwellen der Presets stehen an den gemessenen Werten mit
Abstand.

## Tests

`python -m pytest tests/ -v` – 495 Tests, rund 3 Minuten. Zusammensetzung:

- **Regeln:** Spielfolge Zug für Zug, unabhängige Prüfung jeder Fehlerklasse (`verify`), Johnson gegen Brute Force auf 200 Kleinstbays und gegen die **Zustandssuche** auf 60, Gruppen und Gleichstände, Randfälle (nur Löschen, nur Laden, ein Stapel).
- **Auswertung:** Kennzahlen, Stichprobe, Kurve gegen Direktrechnungen, Urteil in drei Zuständen und genau an der Schwelle, Verteilung.
- **Figuren:** Spielfolge aus den Ergebnisobjekten (Breite je Spiel = Kranzeit, Farben, Löschquelle und Ladeziel, Hover über das ganze Spiel), Kurve, Verteilung.
- **Presets:** Geschichte am gezeigten Bay, im Mittel von 200 Bays, typisch je Kennzahl; alle Kriterien einzeln an ihren Schwellen mit künstlichen Werten.
- **PDF:** Inhalt Zelle für Zelle, genaue Sonderzeichen (fpdf2 stürzt bei „–“, „€“ und Emoji ab), Abschnitte nicht über Seitenumbrüche zerteilt.
- **End-to-End (AppTest):** Skelett und Footer, jedes Preset, Permalink (auch das Verhältnis in Zehnteln), alle Regler an Min und Max, Urteil in allen Zuständen, Johnson-Tab mit Gegenprobe, eigener Bay, PDF.

Zusätzlich wurde jedes Modul mit **eingebauten Fehlern** geprüft; die verbleibenden Überlebenden sind nachweislich gleichwertig oder betreffen reine Seitenumbruch-Schutzabstände.

## Dateistruktur

| Datei | Inhalt |
|---|---|
| `app.py` | Streamlit-Hauptablauf: Presets, Sidebar, Hauptansicht, Bay-Blick, Kernabschnitt, Methodenvergleich, Texte |
| `dsp_constants.py` | Regler-Grenzen, `PRESETS`, Verfahren, Farben, feste Parameter |
| `dsp_presets.py` | `SETTING_SPECS`, Permalink (Begrenzen und Einrasten, Verhältnis in Zehnteln), Presets, Seed-Knopf |
| `dsp_scenario.py` | Bay aus den Reglern (Löschzahl, Ladezahl je Stapel), eigener Bay, Eingabe zerlegen |
| `dsp_rules.py` | Spielfolgen, Reihenfolgen (Bay, kurze Entladung, Johnson, größte zuerst), unabhängige Prüfung, Durchprobieren, Schranken |
| `dsp_evaluation.py` | Kennzahlen, Stichprobe, Kurve über den Beladeanteil, gepaarte Differenz, Verteilung, Urteil |
| `dsp_visualization.py` | Spielfolge, Stapel, Kurve, Verteilung, Vergleich (alle Achsen fest) |
| `dsp_ui_panel.py` | Panel je Verfahren und Johnson-Tab mit Gegenprobe |
| `dsp_pdf_export.py` | PDF-Ergebnis (`fpdf2`, Kernschrift, Sonderzeichen-Bereinigung) |
| `dsp_stories.py` | Abnahmekriterien der Presets (Quelle für Werkzeug und Tests) |
| `tools/tune_presets.py`, `tools/PRESET_SWEEP.md` | Preset-Abstimmung und ihr Bericht |
| `tests/` | siehe oben |

## Bewusst nicht umgesetzt (mögliche Erweiterungen)

- **Fahrzeiten zwischen Stapeln** (Trolley/Portal) und eine Ausbaustufe mit Portalfahrt-Kosten.
- **Lukendeckel und Deck/Unterdeck als Ebenen** (die Erweiterung, für die Johnson allein nicht mehr genügt).
- **Mehrere Bays und Kräne** (Kopplung an die Kran-Demo: kleinere Bay-Arbeitslast) und **Stauplan-Kopplung** (welche Container wohin).
- **Stabilität beim Laden** (Reihenfolge des Ladens ändert den Schwerpunkt).

## Lokal ausführen

```bash
pip install -r requirements-dev.txt
streamlit run app.py
```

Tests: `python -m pytest tests/ -v`. Preset-Abstimmung: `python tools/tune_presets.py population|seeds`.

---

Teil des [Operations-Research-Demo-Portfolios](https://sebastianhanisch.net/demos.html) von
[Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning.
Interesse an einer maßgeschneiderten Lösung? [Kontakt aufnehmen](https://sebastianhanisch.net/kontakt.html).
