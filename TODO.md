# TODO — Strom-Regelkreis-Justage für genaue kleine Ströme (mA-Bereich)

## Ziel
mA-Bereich-Setpoints (10 mA bis 999 mA) auf <5 % Abweichung bringen. Aktueller Stand
(2026-05-16, Verifikation per Live-Test):

| Setpoint | echte CC | Fehler |
|---|---|---|
| 500 mA | ~500 mA | ~0 % |
| 100 mA | ~90 mA | −10 % |
| 50 mA  | ~5 mA (in einem Test) | extrem — nicht praxistauglich |

Anwendung: Cap-Reform für 63 V-Elkos und ähnliche Prozeduren, wo Strombegrenzungen
im einstelligen bis zweistelligen mA-Bereich gebraucht werden.

## Hintergrund
Manual §3.2 beschreibt die Stromregelkreis-Justage. Niedrige Ströme leiden unter
DAC- und Sense-**Offset** (additive Fehler), nicht primär unter Gain — daher zuerst
R1163 + R40 abgleichen, dann optional die Gain-Trimmer.

**Nicht verwechseln:** R43 ist der Monitoring-Offset (§3.3.c), wirkt sich auf die
zurückgelesene Strommessung am Monitor-Ausgang aus, **nicht** auf die Regelung.

## Werkzeug
- [ ] DVM mit mV-Auflösung (Brymen reicht)
- [ ] Strommeßwiderstand / Shunt zum Kurzschließen der Ausgangsklemmen.
      Bei mA-Bereich-Endwert (~999 mA) und ~1 V Burden: 1 Ω/2 W geht (1 W Verlust)
- [ ] Optional: zweites DVM in Reihe als unabhängige Strom-Ist-Messung
- [ ] Zugang zu DAC-Karte 202.237 und Reglerkarte 202.236
      (R1163 + R40 sind auf zwei verschiedenen Karten — Karten ggf. ziehen
      oder Verlängerungsadapter, falls vorhanden)
- [ ] GPIB-Steuerung via `ngpv`-Wrapper (vorhanden)

## Vorbereitung
- [ ] Gerät 30 min warmlaufen lassen (Erfahrung von R1162-Justage 2026-04-25:
      Cermet-Trimmer driften kalt; warm justieren)
- [ ] Karten-Stecker-Sitz aktiv prüfen (DIN-41612-Oxidation-Erfahrung)
- [ ] Nach Power-On daran denken: Default ist mA-Bereich (Manual Z.1714)

## Schritt 1 — R1163: DAC-Strom-Nullpunkt (DAC-Karte 202.237)
Manual §3.2 c–d.

- [ ] Ausgangsbuchsen über Shunt kurzschließen
- [ ] `ngpv 5v on` (Output an, irgendein V — Strom-Setpoint folgt)
- [ ] A-Bereich aktivieren: `1R` senden (Stand A-Bereich ist wichtig für die
      „000"-Einstellung; alternativ wenn Manual mA verlangt → `0R`. Manual ist
      bei §3.2.c nicht explizit — wahrscheinlich mA, da nachher §3.2.e den
      mA-Bereich für Full-Scale-Trim setzt; aber Setpoint 0 wirkt gleich)
- [ ] Strom-Setpoint: `000A` schicken
- [ ] DVM zwischen Testpunkten **+I** und **RI** auf DAC-Karte 202.237
- [ ] R1163 drehen, bis Offsetspannung dort = 0 mV
- [ ] **Cermet-Settling:** nach mechanischem Drehen 1–2 min beobachten, dann
      nochmal nachjustieren falls nötig (siehe R1162-Erfahrung vom 2026-04-25)

## Schritt 2 — R40: Sense-Nullpunkt (Reglerkarte 202.236)
Manual §3.2 f.

- [ ] Setpoint bleibt `000A`, Ausgang noch über Shunt kurzgeschlossen
- [ ] DVM zwischen Testpunkten **IR** und **IS** auf Reglerkarte 202.236
- [ ] R40 drehen, bis Offsetspannung = 0 mV (Manual nennt keine Toleranz für
      diesen Punkt explizit — pragmatisch <2 mV nehmen analog zu R43)
- [ ] Cermet-Settling wieder beobachten

## Schritt 3 — Verifikation
Vor weiterer Justage erst messen, ob Schritt 1+2 bereits gereicht haben.

- [ ] Last anschließen, die bei der Testspannung den jeweiligen CC-Setpoint
      ziehen würde (z.B. 100 Ω/5 W → bei 5 V zieht 50 mA, perfekt zum Testen
      von 10–50 mA Limits)
- [ ] mA-Bereich aktiv: `0R` schicken (Output geht auf Standby), dann
      Setpoint + `C` zum Wiedereinschalten
- [ ] DVM in Reihe als Strom-Ist-Referenz
- [ ] Stichproben: 10 mA, 20 mA, 50 mA, 100 mA, 500 mA, 999 mA
- [ ] **Akzeptanz:** <5 % Abweichung über alle Stichproben in mA-Bereich

Falls nach Schritt 1+2 noch >5 % Fehler bei hohen mA-Werten (>500 mA) übrig
sind, ist das ein Gain-Problem → Schritt 4.

## Schritt 4 (optional) — Gain-Trim für Full-Scale
Manual §3.2 e + g + h.

- [ ] R1164 (DAC Full-Scale, 1 kΩ am „Ti"-Punkt auf DAC-Karte 202.237):
      Setpoint `999A` im mA-Bereich → DVM am Messpunkt soll **10,3896 V**
      anzeigen (für 40/5; andere Modelle: 10,2 V / 9,4 V — Manual §3.2.e)
- [ ] R68 oder R66 (Hilfskarte II 202.238 oder 202.241): Strom-Endwert
      mA-Bereich, Ausgangsstrom durch DVM-Reihe oder Shunt prüfen
- [ ] R67 oder R65 (gleiche Karte): Strom-Endwert A-Bereich
      *(Hier bestand vor der Reparatur ein bekanntes 10 %-Problem:
      `100A` Soll → 1,10 A CC-Trigger. Workaround per Sollwert-Reduktion
      ×0,91 ist aktiv; Justage hier macht den Workaround überflüssig.)*

## Schritt 5 (optional, kosmetisch) — Monitoring-Output
Manual §3.3 c.

- [ ] DVM zwischen Messpunkt **IM** auf Reglerkarte 202.236 und
      Buchse **+AUSGANG**
- [ ] R43 abgleichen, sodass Offset <2 mV
- [ ] Ergebnis: Monitor-Ausgang liest auch bei kleinen Strömen sauber

## Notizen
- R1163 ist 50 kΩ-Cermet auf DAC-Karte 202.237 (Repair-Memory Identifikation
  „Strom-DAC Offset"). Direkt neben R1158 (Spannungs-DAC-Offset).
- R40 auf Reglerkarte 202.236 — Pin-Beschriftung auf der Karte ablesen
  (Bestückungsplan im Manual, Section 5.x — bei Bedarf nachschlagen).
- Reihenfolge wichtig: erst Offset (Step 1+2), dann Gain (Step 4). Andersrum
  führt zu interagierenden Justagen.
