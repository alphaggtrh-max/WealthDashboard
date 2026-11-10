# WealthDashboard

Lokaler Portfolio-Tracker als einzelne HTML-Datei, ohne Server und ohne Internet.

**Starten:** `portfolio-tracker.html` im Browser öffnen. Die Daten bleiben im Browser-Speicher (localStorage). Mit Export/Import im Menü (⋯ oben rechts) sicherst du sie als JSON. Tasten 1, 2, 3 wechseln die Bereiche.

## Funktionen

**Übersicht**
- Großer Depotwert mit animierter Verlaufskurve, darunter Eingezahlt, Gewinn und nächste Sparrate
- Aufteilung (Donut mit Hover), Ist vs. Soll, Verlauf
- Meilensteine mit Prognosedatum, Sparplan-Disziplin mit Nachtragen fälliger Raten
- Rebalancing-Vorschlag: wohin die nächste Rate fließen sollte, ohne zu verkaufen
- Gebühren-Überblick (z. B. 0,5 % FX-Gebühr bei Fremdwährungs-Positionen)

**Rechner**
- Prognose mit Inflation, Kosten, Ratensteigerung, Steuer und FX-Gebühr (nur für Positionen in Fremdwährung, z. B. Nu; Xetra-Positionen wie Alphabet bleiben gebührenfrei)
- Zeitreise-Animation mit Meilenstein-Flaggen und Konfetti beim Ziel, Monte-Carlo-Simulation, Ziel-Rechner
- Heatmap (Rate × Laufzeit) mit Wellen-Animation, Crash-Test

**Daten**
- Sparplan, Buchungen, Depotwerte, Soll-Verteilung

**Sicherheit**
- Rückgängig nach Löschen, Reset, Demo und Import
- Backup-Erinnerung, wenn der letzte Export über 30 Tage her ist

Keine Anlageberatung. Prognosen sind hypothetisch und vereinfacht.
