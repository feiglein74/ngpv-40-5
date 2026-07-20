# CLAUDE.md — Arbeitsanweisungen für dieses Projekt

Reparatur/Betrieb eines **Rohde & Schwarz NGPV 40/5** (40 V / 5 A), Blank-Panel-Variante:
rein IEC-Bus-programmierbar, **kein Display, keine Bedienelemente**. Jeder Status muss über
GPIB (Parallel-Poll) oder ein Multimeter an den Klemmen ermittelt werden — nichts ist ablesbar.

## Befehlsformat — die häufigste Fehlerquelle

Kein SCPI. Kein Read-back. Rechtsbündige Ziffernfolge + Buchstabe:

| Zweck | Format | Beispiele |
|---|---|---|
| Spannung | 4-stellig, Skala x.xx V | `1200V` = 12,00 V · `0500V` = 5,00 V |
| Strom | 3-stellig | `499A` = 4,99 A (A-Bereich) bzw. 499 mA (mA-Bereich) |
| Bereich | — | `0R` = mA/COFF · `1R` = A/COFF · `2R` = mA/CON · `3R` = A/CON |
| Output | — | `C` = ON · `S` = OFF |

**Fallen:**
- `12V` heißt **0,12 V**, nicht 12 V. Immer auf 4 Stellen denken.
- `1R` ist der **A-Bereich**, nicht mA. Kontraintuitiv, hat schon eine Fehldiagnose verursacht.
- Nach Power-On ist per Default der **mA-Bereich** aktiv.
- Ein Bereichswechsel wirft den Ausgang auf Standby → danach Setpoint neu + `C` senden.

## Steuerung

`ngpv` (Wrapper: `bin/ngpv` im Repo, via Symlink als `~/.local/bin/ngpv` im PATH; GPIB-PAD 12):

```bash
ngpv 20v 0.01a     # Spannung + Strombegrenzung
ngpv 250ma         # Strom in mA-Schreibweise
ngpv 20v 1a on     # alles in einem
ngpv off
```

Zwei Dinge, die der Wrapper **nicht** tut — bei Bedarf von Hand:
- Er sendet **nie** ein Range-Kommando. `250ma` wird als `025A` im gerade aktiven Bereich
  geschickt. Wer echten mA-Bereich braucht, muss `0R` separat senden.
- Er wendet die **×0,91-Kompensation nicht** an (siehe unten).

## Bekannte Abweichungen des Geräts

- **Strom-Endwert ~10 % zu hoch:** `100A` (1,00 A Soll) triggert CC erst bei 1,10 A.
  Workaround: Sollwert ÷ 1,10 — `091A` ergibt CC bei 1,00 A. Dauerfix wäre R1164.
- **mA-Bereich bei kleinen Strömen unbrauchbar:** 100 mA Soll → CC bei ~90 mA;
  50 mA Soll → in einem Test CC bei ~5 mA. Ab ~500 mA stimmt es. Justage steht in `TODO.md`.
- Spannung nach R1162-Justage innerhalb ~1 %; Restfehler nicht-linear (12 V schlechter als 5 V).

## Arbeitsweise

- **Minimale Änderungen.** Keine „Aufräum"-Edits zusammen mit dem eigentlichen Fix bündeln.
- **Keine Diagnosefragen während einer laufenden Cap-Reform-Rampe** — das Gerät wird als
  40-V-Quelle gebraucht (das BK1788 reicht nur bis 32 V), die Rampe läuft dann durch.
- **Nach Hardware-Eingriffen** (Karte gezogen o. ä.): GPIB-Adress-DIP **und** Steckersitz
  aktiv kontrollieren, bevor „antwortet nicht" als Defekt interpretiert wird.
- **Cermet-Trimmer settlen mechanisch.** Nach dem Drehen 1–2 min beobachten und nachjustieren,
  bevor eine Position als final gilt — die erste Einstellung wandert um bis zu 0,5 %.
- **Warm justieren.** Kalt driften Referenz und Trimmer; 30 min Warmlauf vor jeder Justage.
- Bei Vintage-Geräten gilt: erst Format, Stecker und Bedienung quervalidieren, dann Hardware
  verdächtigen. Das ursprüngliche „liefert keinen Strom" war kein Bauteildefekt.

## Bauteil-Identifikation

Die Trimmer auf DAC-Karte 202.237 haben **keinen Silkscreen** — Identifikation über den
Werte-Aufdruck (`102` = 1 kΩ, `501` = 500 Ω, `503` = 50 kΩ), ggf. mit dem Multimeter
zwischen Schleifer und Endanschlag verifizieren.

| Trimmer | Wert | Funktion |
|---|---|---|
| R1158 | 50 kΩ (18 mm) | Spannungs-DAC Offset |
| R1163 | 50 kΩ (19 mm) | Strom-DAC Offset |
| R1161 | 500 Ω | Bit-Trim (einziges 500-Ω-Poti) |
| R1159/R1160/R1162/R1164 | 1 kΩ | Bit-Trim / Spannungs-Endwert / Strom-Endwert |

**Nicht verwechseln:** R43 (Reglerkarte 202.236) ist der Trim für den **Monitoring-Ausgang**,
nicht für die Stromregelung. Für genauere kleine Ströme sind R1163 + R40 zuständig.

## Quellen

`NGPV_Service_Manual.md` ist OCR'd und stellenweise unsauber — bei kritischen Werten die
Originalseite unter `manual_pages/page_NNN.png` gegenlesen. Justage-Sektion: Manual Section 3.

Beide liegen lokal im Arbeitsverzeichnis, sind aber nicht Teil des öffentlichen Repos
(© Rohde & Schwarz) — gesichert in `feiglein74/ngpv-40-5-private`.
