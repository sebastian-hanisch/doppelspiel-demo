# Preset-Abstimmung (AP 5)

Werkzeug: `tools/tune_presets.py` (Modi `population`, `seeds`); Kriterien in `dsp_stories.py`, Abnahme in `tests/test_preset_stories.py` (echte Daten) und `tests/test_stories.py`
(künstliche Werte an den Schwellen). Alles ganzzahlig und deterministisch, kein Löser: die Ergebnisse hängen nicht vom Rechner ab (anders als bei den Löser-Demos).

Messbasis: 10 Stapel, 6 Lagen, Entladeanteil 50 %, Doppelspiel kostet 1,4 Einzelspiele (Große Bays: 20 Stapel, 8 Lagen); Bays mit den Seeds 0 bis 199 (Grundgesamtheit) und 200 bis 699 (Suche nach dem Preset-Seed).

## Grundgesamtheit (200 Bays je Preset, Spiele im Mittel)

| Preset | Beladeanteil | Ohne Doppelspiel | Bay-Reihenfolge | Kurze Entladung | Johnson | Kranzeit gespart (Bay / Kurze / Johnson) | Johnson auf der Schranke |
|---|---|---|---|---|---|---|---|
| Nur Löschen | 10 % | 36,1 | 30,9 | 30,7 | 30,2 | 8,7 / 8,9 / 9,8 % | 100 % |
| Ausgewogen | 50 % | 59,4 | 35,9 | 34,2 | 32,9 | 23,7 / 25,4 / 26,7 % | 18 % |
| Viel Laden | 80 % | 78,1 | 51,1 | 49,1 | 49,1 | 20,7 / 22,2 / 22,2 % | 11 % |
| Wenig Laden | 20 % | 42,0 | 31,5 | 31,3 | 30,2 | 14,9 / 15,2 / 16,7 % | 94 % |
| Große Bays | 50 %, 20 × 8 | 160,3 | 89,8 | 86,5 | 85,1 | 26,4 / 27,6 / 28,2 % | 6 % |

Johnson spart 16,4 % (Nur Löschen), 44,5 % (Ausgewogen), 37,0 % (Viel Laden), 27,9 % (Wenig Laden) und 46,9 % (Große Bays) der Spiele.

## Befunde und Abweichungen vom Plan

- **Die Zufallsziehung weicht von der Vorab-Messreihe ab.** Die Messreihe zog die Löschzahl je Stapel gleichverteilt von 0 bis 6; die App zieht je Lage mit der eingestellten Wahrscheinlichkeit
  (binomial), damit Entlade- und Beladeanteil einheitliche Regler sind. Die Zahlen liegen ähnlich (Johnson spart bei 50/50 gut 44 % der Spiele), im Detail nicht gleich: Die Untere Schranke wird bei
  Ausgewogen seltener getroffen (18 % statt 82 % bei 10 × 6 in der Messreihe), weil die Ladezahlen hier stärker streuen. Die Schranke ist deshalb nur bei wenig Beladung (94 %) die Geschichte; bei „Ausgewogen“ zählt der
  Abstand zur Bay-Reihenfolge.
- **Kurze Entladung gegen Johnson:** bei viel Beladung gleichauf (200 von 200 Bays gleich), bei wenig Beladung liegt Johnson in 140 von 200 Bays vorn, bei Ausgewogen in 121 von 200.
- **Nur Löschen:** Bei 10 % Beladung liegt jede Regel auf der Schranke; Ersparnis 16 % der Spiele (die Messreihe sagte 17,1 %).
- **Große Bays:** Die Schranke wird nur noch in 6 % der Bays erreicht; Johnson bleibt bewiesen optimal, die Schranke ist dort nicht erreichbar.

## Gewählt

- Eine gemeinsame Bay-Nummer für alle Presets: **Seed 657** (10 Stapel, 6 Lagen, 50 %/50 %; „Große Bays“ 20 × 8; „Nur Löschen“ 10 %, „Viel Laden“ 80 %, „Wenig Laden“ 20 % Beladung).
  Alle fünf Geschichten tragen an diesem Bay, und jede Kennzahl liegt zwischen dem 10. und 90. Perzentil der 200 Grundgesamtheits-Bays. Der Preset-Seed liegt außerhalb der Stichprobe (Seeds ab 200).
  Von 500 Seeds tragen 285 alle fünf Geschichten; Seed 657 liegt mit 0,14 (Summe der Logarithmen) am nächsten am Median der Kennzahlen.
- An Seed 657 (Ohne / Bay / Kurze / Johnson, Schranke): Nur Löschen 34 / 31 / 30 / 30 (30), Ausgewogen 60 / 36 / 33 / 31 (30), Viel Laden 78 / 52 / 49 / 49 (48), Wenig Laden 42 / 32 / 31 / 30 (30),
  Große Bays 160 / 93 / 85 / 85 (84).
