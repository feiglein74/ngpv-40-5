# NGPV 40/5 Frontpanel-Mod — Stückliste

**Ziel:** Standalone-Bedienung des NGPV mit Display, Encoder, Tasten + Live-Ist-Wert-Anzeige (V/A/Modus).
**Architektur:** AR488 als GPIB-Master, Pico steuert UI, isolierter ADC für Mess-Werte.

---

## 1. GPIB-Master (Kern)

| # | Bauteil | Empf. Typ | Anzahl | Typ. Preis | Notizen |
|---|---|---|---|---|---|
| 1 | Mikrocontroller | **Raspberry Pi Pico** (RP2040) | 1 | 5 € | AR488-Pico-Port existiert. Alt: Pico W (mit WLAN) ~6 €, ESP32 für Web-UI |
| 2 | Bus-Treiber Daten | **SN75160BN** (DIP-20) | 1 | 2 € | Bidirektional 8 Datenleitungen. Pin-kompatibel: TI/ON/Maxim |
| 3 | Bus-Treiber Steuerung | **SN75162BN** (DIP-20) | 1 | 2 € | Steuerleitungen ATN/DAV/NDAC/NRFD/EOI/IFC/REN/SRQ. 162 ist neuer als 161 (TE/REN-Logik korrigiert) |
| 4 | Pull-up-Widerstände | 3 kΩ Metallfilm 1/4 W | 16 | < 1 € | nicht zwingend nötig wenn Bus-Treiber-ICs verwendet — diese haben interne Pull-ups |
| 5 | Entkopplungs-Cs | 100 nF Keramik X7R | 4 | < 1 € | je IC einer + an Pico |
| 6 | IC-Sockel DIP-20 | für 75160 + 75162 | 2 | < 1 € | optional aber empfohlen |

**Verkabelung zum NGPV:** Direkt an die Backplane-Pins der NGPV-IEEE-488-Buchse `BU1` (Print-Stifte). Spart die externe Centronics-Buchse, der AR488 sitzt im NGPV-Gehäuse.

---

## 2. Mess-Sektion (galvanisch isoliert)

NGPV-Output ist potentialfrei, der ADC muss isoliert sein.

| # | Bauteil | Empf. Typ | Anzahl | Typ. Preis | Notizen |
|---|---|---|---|---|---|
| 7 | ADC-Modul | **ADS1115** (4-Kanal, 16-Bit, I²C) | 1 | 3 € | Auflösung: 0.78 mA bei Strom-Ist (Bereich ±0.256 V), 0.2 mV bei Spannungs-Ist |
| 8 | I²C-Isolator | **ADUM1250ARZ** oder **ISO1540DR** | 1 | 3 € | Trennt Mess-GND vom Logik-GND |
| 9 | Iso DC-DC | **B0505S-1W** | 1 | 2 € | 5V→isolierte 5V für Mess-Seite, 1 W ist mehr als ausreichend |
| 10 | Spannungsteiler-Rs | 100 kΩ + 10 kΩ Metallfilm 0.1 % | 2 | 1 € | für 1:11 Spannungsteiler an Ausgangsklemmen (40 V → 3.6 V) |
| 11 | Buffer-OPV (optional) | TLC2272 oder OPA2333 | 1 | 1 € | als Buffer am Monitoring-Ausgang (1 kΩ Innenwiderstand → entkoppelt vom ADC-Eingang) |
| 12 | Entkopplungs-Cs | 100 nF + 10 µF | je 2 | < 1 € | je ADC und OPV |

**Tipp:** Es gibt fertige ADS1115-Breakout-Module auf Aliexpress/Amazon für ~2 € — kann man direkt nehmen.

---

## 3. Bedien-/Display-Sektion

| # | Bauteil | Empf. Typ | Anzahl | Typ. Preis | Notizen |
|---|---|---|---|---|---|
| 13 | Display | **TFT 2.4" 320×240 ILI9341 (SPI)** | 1 | 8 € | zeigt Set/Ist/Modus gleichzeitig. Alt: OLED 128×64 SSD1306 (~3 €) für puristisch |
| 14 | Drehencoder 1 | **EC11 mit Push, 20 Detents** | 1–2 | 2 € je | Wert-Eingabe + Push für Bestätigung. 2 Encoder = direkter Zugriff auf V und A |
| 15 | Encoder-Knopf | Aluminium 6 mm Welle | 1–2 | 3 € je | Optik-Frage. Standard schwarz/silber |
| 16 | Taster | 12×12 mm taktil | 3–4 | < 1 € je | OUTPUT ON/OFF, RANGE (mA/A), LOCAL/REMOTE, evtl. C ON/OFF |
| 17 | Buzzer (optional) | Piezo 3–5 V passiv | 1 | 1 € | für CV/CC-Übergang akustisch |
| 18 | LED Status (optional) | 3 mm rot/grün | 2 | < 1 € | Power-LED + Bus-Aktivitäts-LED |

---

## 4. Power & Mechanik

| # | Bauteil | Empf. Typ | Anzahl | Typ. Preis | Notizen |
|---|---|---|---|---|---|
| 19 | Power-Tap | aus NGPV +5VL Logik-Versorgung | 0 | 0 € | siehe Schaltplan / Backplane — abgreifen, ggf. Sicherung 100 mA in Reihe |
| 20 | Spannungsregler 3.3V | AMS1117-3.3 oder MCP1700 | 1 | 1 € | wenn Pico nicht über USB versorgt wird, brauchen wir 3.3 V für ADS1115 + Display Logic |
| 21 | Frontblende | 3D-Druck oder Alu 3 mm CNC | 1 | 5–20 € | Adapter-Platte hinter der existierenden Blank-Blende |
| 22 | Lochraster oder PCB | Lochraster 80×60 mm oder eigene PCB (KiCad → JLCPCB) | 1 | 2–20 € | je nach Anspruch |
| 23 | Verkabelung | Litze 0.25 mm² + Steckverbinder JST-XH oder Dupont | — | < 5 € | für interne Verbindungen |
| 24 | Schrauben/Distanzbolzen | M2.5 / M3 | 8–16 | < 5 € | für Montage |

---

## 5. OVP-Integration (neu hinzu)

NGPV hat einen Hardware-OVP (Manual Section 2.2.7) mit Front-Poti + LED. Lässt sich nicht per GPIB programmieren, aber wir können den Status mitnehmen und Reset bedienen.

| # | Bauteil | Empf. Typ | Anzahl | Typ. Preis | Notizen |
|---|---|---|---|---|---|
| 28 | Optokoppler | **PC817** oder **6N137** | 1 | < 1 € | Greift OVP-LED-Spannung ab und übersetzt zum Pico-GPIO. Galvanisch trennt es auch noch die OVP-LED-Schiene |
| 29 | Vorwiderstand | 1–2 kΩ | 1 | < 1 € | Strombegrenzung Optokoppler-LED |

**OVP-Status:** Optokoppler parallel zur OVP-LED → Pico-GPIO als Eingang → wenn aktiv, Display zeigt Warnsymbol.

**OVP-Reset:** UI-Taste "OVP RESET" (oder Encoder-Push-Long) → AR488 sendet `S` dann `C`.

**Optional — programmierbare OVP-Schwelle (Etappe 2):**

Nach OVP-Schaltungs-Analyse (REPAIR_LOG Phase 19): Original-Poti = **R4 auf Frontplatte, 25 kΩ Draht-Trimmer (R&S 404.012.00)**, sitzt zwischen Punkten OP/OPM auf Reglerkarte 202.236, vergleicht gegen Sensingspannung über B2/B3-Verstärker. Reine Spannungsteiler-Funktion (kein Strompfad), liegt vermutlich an ±15 V Analog-Versorgung an.

| # | Bauteil | Empf. Typ | Notizen |
|---|---|---|---|
| 30 | Digital-Poti (Empfehlung) | **AD5160** (256 Stufen, SPI) oder **AD5260** (256 Stufen, ±15 V tauglich) | **±15 V-fähig** — entscheidend, weil Original-Poti im Analog-Pfad sitzt. 50 kΩ Variante (AD5160BRJZ50 / AD5260BRZ50) gibt's direkt; 25 kΩ-Wert nicht verfügbar, daher mit Halb-Range arbeiten oder Vorwiderstand |
| 30a | Digital-Poti (Alternative) | **AD5263** (Quad, EEPROM) | merkt Setting beim Power-Off — kein Re-Init nötig. ~5 € teurer |
| 30b | Digital-Poti (Budget) | MCP41xxx (SPI) oder DS1804 | nur bis +5 V — funktioniert NICHT direkt am Original-Pfad. Nur mit Pegelwandler einsetzbar |

**Auflösung-Check:** AD5160 mit 256 Stufen × 40 V Bereich = **156 mV pro Schritt** — für OVP-Schwelle völlig ausreichend (Ist-Schwelle gerade ~39.7 V). AD5260 mit ±15 V-Toleranz ist die saubere Lösung.

---

## 6. Erweiterte Mess-Schiene (NGPV-intern, NICHT isoliert)

Diese Mess-Punkte beziehen sich alle auf den **Logik-GND** des NGPV — der ist mit dem Pico-GND identisch (Pico bezieht ja +5VL aus dem NGPV). Daher **keine ISO-Trennung nötig**, alles direkt an Pico-ADC oder zweiten ADS1115 anschließbar.

| # | Signal | Was es sagt | Anschluss | Hardware |
|---|---|---|---|---|
| 31 | **Lüfter-Modus** (Teil/Voll) | Lastwechsel / Wärmestress | Spannung am Lüfter-Versorgungspin → Spannungsteiler 1:5 → Pico-ADC oder GPIO (digital high/low) | 2 Widerstände |
| 32 | **DC-Bus Endstufe** (~50 V Roh-DC) | Trafo/Brücke/Hauptelko-Zustand. Bricht ein bei Elko-Defekt | Spannungsteiler 1:20 (z. B. 200k+10k) → ADC-Kanal | 2 Präzisionswiderstände 0.1 % |
| 33 | **+15 V Analog-Versorgung** | OPVs der Regelkreise versorgt? | Spannungsteiler 1:5 → ADC | 2 R |
| 34 | **−15 V Analog-Versorgung** | analog | Spannungsteiler + Inverter (oder Diff-OPV) | 2 R + 1 OPV |
| 35 | **+5 V Logik** | Sanity-Check Pico-Versorgung | direkt an ADC | – |
| 36 | **Bereichs-Relais-Status** (mA/A) | echter Zustand nach Power-Cycle | Pin am Flip-Flop B505b (auf 202.234), evtl. via Pull-Down | 1 R |
| 37 | **OUTPUT ON/OFF Status** | echter Zustand | Pin am OUTPUT-FF (auf 202.234) | 1 R |

Wenn alle Signale rein sollen → 4 zusätzliche ADC-Kanäle nötig. Pico hat schon 3–4 frei (GP26–GP29). Falls die belegt sind, **zweiter ADS1115** (Adress-Pin auf VDD/GND/SCL/SDA → bis zu 4 ICs auf einem Bus).

| # | Bauteil | Notiz |
|---|---|---|
| 38 | ADS1115 #2 (optional) | wenn Pico-ADC belegt |
| 39 | OPV für −15V-Inversion | TLC2272 / OPA2333 (eh schon da als Buffer) — ein Kanal frei für negativ |

---

## 7. Optional / Komfort

| # | Bauteil | Empf. Typ | Notizen |
|---|---|---|---|
| 25 | NTC-Temperatursensor (Kühlkörper) | 10 kΩ B3950 oder **DS18B20** (1-Wire) | mit Wärmeleitkleber am Stellglied-Kühlkörper. Zeigt analog vor dem Thermoschalter-Schwellwert |
| 26 | NTC-Temperatursensor (Gehäuse) | gleicher Typ | Umgebungstemperatur, Lüftungs-Indikator |
| 27 | uSD-Karte + Modul | SPI-Modul + 8 GB Karte | für Mess-Logging — sehr nett für lange Versuche |
| 28 | RTC | DS3231 I²C | wenn Logging mit Zeitstempel gewünscht |

---

## Geschätzte Gesamtkosten

| Variante | Pflicht-Teile | mit 2 Encoder + TFT |
|---|---|---|
| **Minimal** (OLED, 1 Encoder, ohne Mess-ADC) | ~25 € | — |
| **Standard** (TFT, 2 Encoder, isolierter ADC) | ~50 € | ✓ |
| **Erweitert** (+ DC-Bus + ±15V + Lüfter-Monitor) | ~60 € | ✓ |
| **Komfort** (alles + Temp + RTC + uSD) | ~80 € | ✓ |

Plus Frontblende (Material + Bearbeitung) und Verbrauchsmaterial.

---

## Software-Komponenten (alles Open-Source, kein Kauf)

- **AR488-Firmware**: Twilight-Logic GitHub, Pico-Port verfügbar
- **PlatformIO** oder Arduino IDE als Build-Toolchain
- **TFT_eSPI** (Bodmer) für TFT-Display-Treiber
- **Adafruit_ADS1X15** für ADC
- **eigene UI-Schicht** (NGPV-spezifischer Wrapper) — ein paar hundert Zeilen C++

---

## Was du wahrscheinlich schon im Schrank hast

- ✅ Pico / Arduino / ESP32
- ✅ Display (irgendein OLED / TFT)
- ✅ Encoder, Taster
- ✅ Lochraster / PCB-Material
- ✅ Widerstände, Kondensatoren, Sockel

## Was wahrscheinlich beschafft werden muss

- 🛒 SN75160 + SN75162 (GPIB-Bus-Treiber, kein Hobby-Standard)
- 🛒 ADS1115 (falls noch nicht da)
- 🛒 ADUM1250 oder ISO1540 (I²C-Isolator)
- 🛒 B0505S-1W (Iso-DC-DC)

Diese vier Spezialteile sind die "GPIB- + Isolation-Spezial-Sache" — der Rest ist Allerwelts-Hobby-Bestand. Optokoppler PC817/6N137 hat man meistens, sonst unkritischer 1-€-Standard.

---

## Reihenfolge für Beschaffung & Aufbau

1. GPIB-Master-Block (Pico + 75160 + 75162) zuerst auf Lochraster — mit AR488-Firmware testen, ob NGPV ansprechbar ist (`++addr 12`, `1200V`, `C`).
2. Mess-Block (ADS1115 isoliert) — separat testen, Werte plausibilisieren.
3. UI-Block (Display + Encoder) — separat als "leerer Editor" mit Encoder-Eingabe.
4. Alles zusammenkleben, Frontblende bauen.
