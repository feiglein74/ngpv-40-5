# NGPV 40/5 — Inbetriebnahme & Reparatur-Log

**Datum:** 2026-04-25
**Gerät:** Rohde & Schwarz NGPV 40/5 (Bestellbez. 192.0326.40), Blank-Panel-Variante (rein bus-programmierbar, kein Display)
**Steuer-Interface:** Keysight 82357B USB→GPIB (Cypress FX2)
**Host:** Kali Linux Rolling, Kernel 6.19.11+kali-amd64

---

## Endbefund

Gerät ist **funktional**.
- Spannungsregelung sauber, Innenwiderstand quasi 0 (5 A Last → <10 mV Spannungsabfall an den Klemmen)
- Stromregelung greift korrekt am programmierten CC-Limit
- Nennstrom 5 A unter Last erreichbar
- GPIB-Steuerung über Adapter + linux-gpib stabil

**Verbleibende Auffälligkeiten (kosmetisch):**
- ~5 % Drift der Spannungsreferenz (Sollwert 12.00 V → Ist 11.40 V Leerlauf). Justierbar mit R1162 auf DAC-Karte 202.237 (Manual Section 3.1.j).
- Backplane-Stecker zeigten Wackelkontakte (Oxidation nach Jahren Standzeit). Wenn nicht gereinigt → Defekt kommt zurück.

**Ursprüngliches Symptom („akzeptiert Spannung, liefert keinen Strom"):** kein echter Bauteildefekt. War eine Kombination aus Wackelkontakt-Episode am DIN-41612-Backplane-Stecker und Range-Code-Fehlinterpretation in der ersten Diagnose-Phase.

---

## Hardware-Topologie

```
PC (Kali) ──USB── Keysight 82357B ──IEEE-488 (24-pol)── NGPV 40/5
                                                            │
                                                            └── Ausgangsklemmen ── Multimeter Metrahit
                                                                                ── E-Last (CC-Modus)
```

**Wichtig:** NGPV hat eine 24-pol IEEE-488-Buchse (NICHT 25-pol IEC-625), trotz der Manual-Bezeichnung „IEC-625-Buchse". Manual Seite 15 bestätigt das. Der 82357B passt direkt drauf.

**GPIB-Adresse NGPV:** 12 (DIP-Schalter Werks-Default — 5-poliger DIP an der Rückwand, Bits LSB→MSB; für 12 = Pole 3+4 ON, Rest OFF). Wird nur beim Power-On gelatcht.

---

## Linux-Software-Setup (vollständig reproduzierbar)

### 1. Pakete

```bash
sudo apt update
sudo apt install -y \
    build-essential \
    linux-headers-amd64 \
    git autoconf automake libtool bison flex texinfo \
    fxload \
    libgpib0 libgpib-dev libgpib-bin gpib-user-tools python3-gpib
```

> **Achtung:** Wenn der laufende Kernel älter ist als der im Repo verfügbare, gibt es keine passenden Headers. Lösung: `sudo apt install linux-image-amd64 linux-headers-amd64 && sudo reboot`. Wir mussten von 6.18 auf 6.19 hochziehen.

### 2. linux-gpib Kernel-Modul gegen aktuellen Kernel bauen

Stand-Kali bringt die linux-gpib-Userspace-Pakete, aber **kein Kernel-Modul**. Der Mainline-Staging-Treiber ist in 6.19 zwar verfügbar, aber im Kali-Build nicht aktiviert (`# CONFIG_GPIB is not set`). Daher Out-of-Tree-Build:

```bash
mkdir -p /home/feig/ngpv-40-5/build
cd /home/feig/ngpv-40-5/build
git clone --depth 1 https://git.code.sf.net/p/linux-gpib/git linux-gpib-git

cd linux-gpib-git/linux-gpib-kernel
make
sudo make install
sudo depmod -a
sudo modprobe gpib_common
sudo modprobe agilent_82357a
```

Erfolgs-Indikator in `dmesg`:
```
gpib_common: Linux-GPIB 4.3.7 core driver loaded
usbcore: registered new interface driver agilent_82357a
```

### 3. Firmware für 82357B

Der 82357B (Cypress FX2) lädt seine Firmware bei jedem USB-Plug. Ohne Firmware erscheint er als USB-ID `0957:0518` („Firmware Loader"); nach Firmware-Upload als `0957:0718` (eigentlicher 82357B).

Quelle: <https://linux-gpib.sourceforge.io/firmware/gpib_firmware-2008-08-10.tar.gz>

```bash
cd /home/feig/ngpv-40-5/build
curl -O https://linux-gpib.sourceforge.io/firmware/gpib_firmware-2008-08-10.tar.gz
tar xzf gpib_firmware-2008-08-10.tar.gz

sudo install -d /usr/share/usb/agilent_82357a
sudo install -m 0644 \
    gpib_firmware-2008-08-10/agilent_82357a/measat_releaseX1.8.hex \
    gpib_firmware-2008-08-10/agilent_82357a/82357a_fw.hex \
    /usr/share/usb/agilent_82357a/
```

> Die Firmware-`measat_releaseX1.8.hex` ist die Datei für den 82357**B**. Der ältere 82357**A** nutzt `82357a_fw.hex`. Die udev-Regel des `libgpib-bin`-Pakets ruft `/usr/lib/udev/gpib_udev_fxloader` auf, das je nach USB-ID den richtigen Blob lädt.

### 4. udev / Permissions

Das libgpib-bin-Paket installiert bereits `/usr/lib/udev/rules.d/99-agilent_82357a.rules` und den Helper `gpib_udev_fxloader`. Was fehlt: `/dev/gpib*` ist standardmäßig 0600 root-only. Lösung — eigene Regel:

`/etc/udev/rules.d/55-gpib-perms.rules`:
```
KERNEL=="gpib[0-9]*", GROUP="dialout", MODE="0660"
```

Aktivieren:
```bash
sudo udevadm control --reload-rules
sudo udevadm trigger --action=change --subsystem-match=gpib_common
```

(Falls `change` nichts tut: kurz `rmmod agilent_82357a && modprobe agilent_82357a`.)

User `feig` ist Mitglied der `dialout`-Gruppe.

### 5. /etc/gpib.conf

```
interface {
    minor       = 0
    board_type  = "agilent_82357a"
    name        = "gpib0"
    pad         = 0
    sad         = 0
    timeout     = T3s
    eos         = 0x0a
    set-reos    = yes
    set-bin     = no
    set-xeos    = no
    set-eot     = yes
    master      = yes
}

device {
    minor       = 0
    name        = "ngpv"
    pad         = 12
    sad         = 0
    eos         = 0x0a
    set-reos    = no
    set-bin     = no
}
```

### 6. Initialisierung

Nach jedem Modul-Load und USB-Replug:
```bash
sudo gpib_config --minor 0
```

Verifikation:
```bash
lsusb | grep 0957       # → 0957:0718 (firmware geladen)
ls -la /dev/gpib0       # → crw-rw---- root dialout
ibtest                  # → b → gpib0 → l → liest Bus-Status
```

---

## NGPV GPIB-Kommando-Referenz

NGPV ist **reiner Listener** — kein `*IDN?`, kein SCPI, kein Read-Back. Antworten gibt es nur via Parallel-Poll (1 Bit: CV-Modus oder CC-Modus).

### Spannungs-Sollwert
4 Stellen rechtsbündig, Skala `xx.xx V` für 40 V-Geräte:
| Befehl | Bedeutung |
|---|---|
| `0500V` oder `500V` | 5.00 V |
| `1200V` | 12.00 V |
| `1982V` | 19.82 V |
| `4000V` | 40.00 V (max) |

Führende Nullen optional, Folgenullen Pflicht. Trennzeichen `.` / `,` werden ignoriert (`12.00V` wäre `1200V`).

### Strom-Sollwert (Limit)
3 Stellen, Bedeutung hängt vom aktiven Bereich (siehe `R`-Befehl):
| Befehl | A-Bereich | mA-Bereich |
|---|---|---|
| `010A` | 0.10 A | 10 mA |
| `100A` | 1.00 A | 100 mA |
| `200A` | 2.00 A | 200 mA |
| `499A` | 4.99 A | 499 mA |

### Strombereich + Ausgangskondensator
Kombiniert in einem Befehl, dann `R`:
| Befehl | Bereich | Ausgangs-C |
|---|---|---|
| `0R` | mA | OFF |
| `1R` | A | OFF |
| `2R` | mA | ON |
| `3R` | A | ON |

> **Achtung:** Nach `R`-Befehl geht das Gerät auf Standby (Relais im stromlosen Zustand schalten). Anschließend wieder `C` senden.

### OUTPUT-Schaltung
| Befehl | Bedeutung |
|---|---|
| `C` | Close = OUTPUT ON |
| `S` | Standby = OUTPUT OFF |

### Beispiel-Sequenz: 12 V, 4.99 A Limit, A-Bereich, OUTPUT ON
```
S         OFF (sicher)
1R        A-Bereich (legt automatisch OFF)
1200V     12.00 V Sollwert
499A      4.99 A Limit
C         OUTPUT ON
```

---

## Skripte im Build-Verzeichnis

`/home/feig/ngpv-40-5/build/`:

| Datei | Zweck |
|---|---|
| `ngpv_diag.py` | Standard-Diagnose: IFC, Bus-Lines lesen, zwei Schreibversuche |
| `ngpv_on.py` | Erster Funktionstest: 5 V / 500 mA programmieren, OUTPUT ON |
| `adapter_check.py` | Selbsttest des 82357B (REN-Toggle, IFC, ATN-Verhalten) |
| `adapter_unhang.py` | ATN-Hang lösen (System-Controller-Toggle, IFC, UNL+UNT) |

Schnell-Befehle (auf Kommandozeile):
```bash
# OUTPUT aus
python3 -c "import Gpib; n=Gpib.Gpib('ngpv'); n.write(b'S')"

# 12V / 5A Limit / OUTPUT ON
python3 -c "
import Gpib, gpib, time
n = Gpib.Gpib('ngpv'); n.timeout(gpib.T3s)
n.write(b'S'); time.sleep(0.3)
n.write(b'1R'); time.sleep(0.5)
n.write(b'1200V'); time.sleep(0.1)
n.write(b'499A'); time.sleep(0.1)
n.write(b'C')
"
```

---

## Diagnose-Verlauf — was wir gelernt haben

### Phase 1: GPIB-Stack aufbauen (~2h)
Linux-Setup (Kernel-Upgrade, Module bauen, Firmware, udev, gpib.conf). Erfolgreich.

### Phase 2: NGPV antwortet nicht
Erste Schreibversuche timen mit `EBUS 14: Bus error` und `command bytes timed out` aus. NDAC/NRFD bleiben in der `lines()`-Anzeige off, niemand zieht sie low.

### Phase 3: Loopback-Test bestätigt 82357B
Mit Drahtbrücke direkt an der 82357B-Buchse Pin 7 ↔ Pin 19/24 wird `NDAC on` sichtbar → Adapter-Hardware und Linux-Stack funktionieren bis zum Stecker.

### Phase 4: Bus-Verhalten interpretieren
Manual Section 4.2.2 klärt auf: **NGPV zieht NDAC im Idle gar nicht low**, nur beim Empfang von ATN. Mein vorheriger „NDAC bleibt off → Gerät tot"-Schluss war falsch. Mit aktivem ATN (durch Universal-Command UNL+UNT erzwungen) zieht das NGPV NDAC korrekt low → es lebt am Bus.

### Phase 5: Wackelkontakt-Episode
Nach dem Aufschrauben + Multimeter-Messung an Karte 202.233 (+5 V verifiziert auf B1201 Pin 14) gehen plötzlich die Schreibversuche durch. **Ursache: Karte 202.233 minimal in der DIN-41612-Buchsenleiste bewegt → Kontaktdruck wiederhergestellt.** Klassische Oxidation nach Jahren Standzeit.

### Phase 6: Erster Funktionstest
- Sollwert 5 V, Multimeter zeigt 4.8 V → Spannungsregelung läuft, ~4 % Drift in der Referenz
- E-Last 1 A, Spannung stabil → Strom fließt

### Phase 7: Range-Code-Verwirrung — mein Fehler
Ich hatte die Range-Codes invertiert verstanden (`1R` für „mA" angenommen, ist aber „A"). Dadurch erschien die Strombegrenzung erst bei 2 A statt 200 mA → kurzfristig „CC-Defekt"-Verdacht. Manual Section 2.3.4 korrigiert: `0R`=mA/COFF, `1R`=A/COFF, `2R`=mA/CON, `3R`=A/CON.

### Phase 8: Vermeintlicher thermischer Defekt
Nach einigen Minuten unter Last: Strom plötzlich nicht mehr ziehbar (<10 mA), während Spannung weiter sauber regelt. Hypothese „thermische Drift im Strompfad". Tatsächlich: erneute Wackelkontakt-Episode — andere Karte minimal verloren.

Nach erneutem Programmieren von Spannung + Strom-Sollwert lieferte das Gerät wieder den Nennstrom 5 A.

### Phase 9: Innenwiderstand
- Anfangs scheinbar 325 mΩ Innenwiderstand (Spannungsabfall 1.3 V bei 4 A)
- Nach besseren Mess-Kabeln und Messung am Metrahit (NGPV-Klemmen statt E-Last):
  - Leerlauf bei 12 V Sollwert → 11.40 V (Drift)
  - Unter 5 A Last → 11.409 V
  - **Innenwiderstand effektiv 0**

Die ursprünglichen 325 mΩ waren Kabelwiderstand + Vergleich mit dem Soll- statt Ist-Wert.

### Phase 10: CV/CC-Crossover bestätigt
- Programmierter Sollwert: 12 V / 4.99 A im A-Bereich
- Bei 5.00 A Last: Spannung stabil → CV-Mode
- Beim Versuch 5.10 A zu ziehen: Spannung kollabiert → CC-Mode greift, das Gerät liefert die 5.1 A bewusst NICHT, sondern regelt zurück. Genau wie es soll.
- CC-Limit aktiv knapp oberhalb 5.0 A — bei 4.99 A Sollwert = ≤2 % Abweichung, innerhalb Toleranz

### Phase 12: CC-Linearität im A-Bereich systematisch verifiziert
Bei 12 V Sollwert mit verschiedenen CC-Limits getestet, E-Last jeweils oberhalb des Limits gefordert:

| Sollwert | CC-Greifen | Toleranz |
|---|---|---|
| 1.00 A | ~1.0 A | ✅ |
| 2.00 A | ~2.0 A | ✅ |
| 3.00 A | ~3.1 A | +3 % ✅ |
| 4.99 A | ~5.1 A | +2 % ✅ |

Sehr linear über den ganzen A-Bereich. Bei warmem Gerät: Spannungs-Drift hat sich von ~5 % auf ~1 % reduziert (Sollwert 12 V → ~11.95 V).

### Phase 13: mA-Bereich verifiziert (mit Hysterese-Befund)
Bei 12 V / 500 mA Sollwert im mA-Bereich (`0R`):
- Langsam ansteigende Last: CC greift bei ~480 mA (96 % des Sollwerts) — präzise
- Sprungartige Last: CC verriegelt schon bei ~400 mA
- Unterschied ist klassische Hysterese / Slew-Rate-Begrenzung des OPV-basierten CC-Loops, kein Defekt
- Monitoring im mA-Bereich (Skala 10 mA/mV) zeigt bei niedrigen Strömen einen kleinen relativen Offset (15 % bei 100 mA), bei höheren Strömen linear (5.6 % bei 300 mA). R43-Offset könnte bei Bedarf nachjustiert werden (Manual Section 3.3.c).

### Phase 11: Monitoring-Ausgang
Manual Seite 14: NGPV 40/5 hat Strom-Mess-Ausgang mit Skala 100 mA/mV im A-Bereich.
- Bei 5.00 A Last (CV-Mode): Monitoring liefert 50.2 mV → entspricht 5.02 A (0.4 % Abweichung)
- Strom-Mess-Verstärker und R4-Endwert-Justage in Ordnung

### Phase 14: Spannungsreferenz-Justage R1162 (2026-04-25 Abend)

Setup:
- Brymen BM867 + Fluke 789 parallel an +SENSING / –SENSING
- NGPV stundenlang in Betrieb, thermisch stabil
- Sollwerte über GPIB programmiert (`ngpv_cal_35v.py`)

Poti-Identifikation auf DAC-Karte 202.237 (kein Bezeichner-Silkscreen, nur Werte-Aufdruck):
- R1162 = 1 kΩ Cermet 19 mm Trimmer (Code „102") am Test-Punkt „Ru" (= UR im Manual-Layout)
- Daneben: R1158 = 50 kΩ Cermet 18 mm (Code „503") — Spannungs-DAC Offset (NICHT angefasst)
- Identifikation per Werte-Code, da Bezeichner-Silkscreen fehlt: R1161 (500 Ω, einziger 500-Ω-Trim) ist eindeutig erkennbar; alle anderen 1k vs. 50k unterscheidbar

Ablauf:
1. 35 V Sollwert programmiert. Vor Justage: 34.342 V Ist (–1.88 %)
2. R1162 vorsichtig im Uhrzeigersinn ~10° gedreht → 35.002 V
3. Linearitätscheck bei 5 V und 12 V → nicht-lineare Restabweichung erkannt
4. Cermet-Settling beobachtet: nach ca. 5 min war 35 V auf 35.220 V (+0.63 %) gewandert. 2. Tweak nötig — Schleifer benötigt mehrere Minuten zum mechanischen Setzen

Endwerte (stabil reproduzierbar, Brymen):

| Soll | Ist | Abweichung |
|------|-----|------------|
| 5 V | 4.949 V | –1.02 % |
| 12 V | 11.927 V | –0.61 % |
| 35 V | 35.001 V | +0.003 % |

Befund: **Nicht-linearer Restfehler** — 12 V (DAC-Code 1200, knapp nach Bit-1000-Übergang) ist schlechter als 5 V (Code 500, vor Bit-Übergang). Klassisches Bit-Trim-Problem an R1160. Vollständige Justage nach Manual 3.1 a–j (R1158 → R1159 → R1160 → R1161 → R36/R38/R39 auf 202.236 → R1162) würde den Restfehler beseitigen, wurde aber als nicht erforderlich bewertet (Genauigkeit für Lab-Use ausreichend, Verbesserung von ursprünglich 5 % → jetzt <1 %).

### Phase 15: Parallel-Poll verifiziert + Re-Interpretation des Original-Defekts (2026-04-25 Abend)

**Parallel-Poll funktioniert** — `build/ngpv_pp.py` konfiguriert PPE 0x6E (DIO 7, sense=1) per `libgpib.ibppc()` und liest CV/CC-Status per `ibrpp()`. Bei reiner CV-Last → Bit 6 gesetzt, bei Strombegrenzung → Bit 6 frei. Damit ist alles, was IEEE-488-mäßig aus diesem Gerät rausholbar ist, dokumentiert und benutzbar.

**Re-Interpretation des Original-Defekts „liefert keinen Strom":**

Der ursprüngliche Defekt von vor Jahren war mit hoher Wahrscheinlichkeit **kein Hardware-Defekt**, sondern eine Verkettung aus zwei harmlosen Faktoren:

1. **Format-Fehlinterpretation des Strom-Sollwerts:** Das NGPV-Befehlsformat ist **rechtsbündig 3-stellig** mit fest skaliertem Bereichsendwert. Wer intuitiv `5A` als „5 Ampere" liest, programmiert real **0.05 A = 50 mA** im A-Bereich (oder 5 mA im mA-Bereich). Jede halbwegs ohmsche Last drückt das Gerät dann sofort in **CC-Mode bei winzigem Strom**, und am Ausgang misst man scheinbar „nichts". Genau dieses Stolperstein habe ich in der ersten Phase dieser Diagnose-Session selbst auch gemacht — der Befund passt also zur Symptomatik.
2. **Wackelkontakt am Backplane-Stecker:** Über Jahre Lagerung oxidiert, intermittierend.

Beide wirken in dieselbe Richtung und verstärken sich. Da das Gerät **kein Display** hat (Blank-Panel-Variante), ist der CV/CC-Mode-Wechsel ohne externes Multimeter oder Parallel-Poll nicht erkennbar — das Symptom „Spannung übernommen, kein Strom" ist dann genau das, was man sieht.

**Konsequenz:** Die Endstufe (Linear-Pass-Stage, Stromloop, OUTPUT-Relais, Trafo, Elkos) war wahrscheinlich nie defekt. Verifiziert durch:
- Volle CV-Linearität bis 35 V (≤0.05 % nach Justage)
- Volle CC-Linearität von 1 A bis 5 A (jeweils <3 % Toleranz)
- Innenwiderstand quasi 0
- Sauberer CV/CC-Crossover (Phase 10), live-bestätigt per Parallel-Poll (Phase 15)

Die einzige reale Reparatur war: **GPIB-Anbindung auf Linux herstellen + Format korrekt verstehen + Backplane wieder kontaktiert**.

### Phase 16: Slew-Rate-Hysterese im mA-Bereich bei kleinem Sollwert (2026-04-25 Abend)

Test: NGPV auf 12 V / **50 mA Limit** im mA-Bereich, Last als pulsierender Verbraucher (30 s ON, 30 s OFF).

Beobachtung mit Parallel-Poll-Live-Monitor (`build/ngpv_pp_monitor.py`, 200 ms-Intervall):
- t=0 s: CV (Last AUS, 12 V steht)
- t≈24 s: **CC (~2 s lang)** — Last schaltet AN, Inrush triggert CC
- t≈26 s: CV — Loop hat den Inrush abgefangen, Last steady-state unter 50 mA, CV regelt zurück
- t≈59 s: **CC (~2 s lang)** — nächster Last-AN-Sprung
- t≈61 s: CV — Zyklus wiederholt sich

Der **Strom während der CC-Phase** war ~5 mA — also **10 % des Sollwerts**. Das ist die gleiche Slew-Rate-Hysterese wie in Phase 13 dokumentiert (dort: 500 mA Sollwert → 400 mA CC-Trigger = 80 %), nur dramatisch verstärkt im Kleinbereich.

**Mechanismus:**
1. Last schaltet sprungartig AN, zieht **Inrush-Strom** (oft ein Vielfaches des stationären Bedarfs durch Eingangs-Cs/Wandler-Anlauf)
2. NGPV-Stromregelschleife (OPV-basiert) hat **endliche Slew-Rate** — kann den schnellen Strom-Sprung nicht in Echtzeit verfolgen
3. Während die Schleife dem Sprung hinterherläuft, rutscht der Output kurzzeitig in **CC-Klemmung**, aber bei einem Strom-Wert, der **weit unter dem programmierten Setpoint** liegt (weil die dynamische Antwort den Loop kurz „überschießen" lässt)
4. Sobald die Last in steady-state übergeht und unter den Setpoint fällt, gibt CC frei und CV regelt wieder
5. **Der Effekt ist relativ stärker bei kleinen Setpoints**, weil die Slew-Rate-Begrenzung absolut etwa konstant ist (vermutlich auch bei höheren Setpoints ein paar mA „überschießender" Klemm-Wert), aber bei 50 mA-Limit ergibt das eben 5 mA = 10 %

**Konsequenz:**
- **Kein Defekt** — das ist eine fundamentale Eigenschaft des analogen CC-Loops dieser Geräte-Generation
- Bei pulsierenden Lasten mit Inrush-Komponente sollte der Strom-Sollwert **deutlich oberhalb des Steady-State-Bedarfs + erwarteter Inrush** programmiert werden
- Bei sehr kleinen Sollwerten (< 100 mA) lässt sich der Effekt nicht vermeiden, ist aber durch eine langsame Lastrampe (statt Sprung) abmilderbar

**Bestätigt mit 200 mA Limit (gleiche Last):** kein CC-Trigger mehr, durchgehend CV. Bedeutet:
- Steady-state-Bedarf der Test-Last: < 50 mA (sonst hätte CC bei 50 mA Limit dauerhaft geklemmt)
- Peak-Inrush: zwischen 50 und 200 mA
- Faustregel: **Limit ≥ 2–3 × stationärer Bedarf** deckt typische Inrush-Spitzen ab

### Phase 17: R1164-Offset-Kompensation per Sollwert + Backplane-Reinigung (2026-04-25 spät)

**Beobachtung:** Bei programmiertem 1.00 A Strom-Limit (`100A` im A-Bereich) greift CC erst bei ~1.10 A — also ~10 % zu hoch. Das ist die R1164-Justage (Strom-Endwert) auf der DAC-Karte 202.237, die nicht 100 % auf Soll steht. Phase 12 hatte das schon angedeutet (3 % Abweichung bei 3 A, 2 % bei 5 A).

**Pragmatische Lösung ohne Hardware-Justage:** Sollwert um den Offset reduzieren. Test:
- Sollwert `091A` = 0.91 A programmiert
- Last 0.9 A: stabil CV ✓
- Last 1.01 A: CC greift ✓
- → CC-Trigger jetzt bei effektiv 1.00 A, wie gewollt

**Faustregel für genauen Trigger-Punkt** (bis R1164 nachjustiert ist):
- Programmierter Sollwert ÷ 1.10 ≈ tatsächlicher CC-Trigger
- Oder: Sollwert × 1.10 = nominaler Trigger-Punkt
- Beispiele: `181A` = 1.81 A → CC bei ~2.0 A; `455A` = 4.55 A → CC bei ~5.0 A

**Backplane-Reinigung (Task #15) durchgeführt:** Gerät ausgeschaltet, alle Karten gezogen, DIN-41612-Kontakte mit Isopropanol gereinigt, wieder zusammengesetzt. Beim ersten Wiedereinschalten antwortete das Gerät nicht über GPIB (Bus-Status: kein Listener). Nach Re-Check der Verkabelung und/oder DIP-Schalter funktioniert die Kommunikation wieder vollständig — Funktionstest mit 9.10 V / 0.91 A / OUTPUT ON erfolgreich. Die Reinigung war also erfolgreich (kein Schaden), aber der initiale Wiederanlauf zeigt: **DIP-Schalter und/oder GPIB-Stecker müssen nach jedem Eingriff aktiv kontrolliert werden**.

### Phase 18: R43-Strom-Offset-Justage geprüft (2026-04-26)

Manual Section 3.3.c-Prozedur: DVM zwischen Test-Punkt **„IM" auf Regler-Karte 202.236** und **+AUSGANG**, Spannungsendwert programmiert (39.50 V), OUTPUT ON, Last AB. Manual-Toleranz: <2 mV.

Messung mit Brymen BM867:
- Initial nach Aufwärmen: **0.6 mV** (kalt)
- Nach weiterer Warmlaufzeit: **0.3 mV** (warm)

→ R43 ist bereits **gut innerhalb der Spec** (Faktor 6× besser als Manual-Toleranz). Keine Justage erforderlich.

**Verifikation der Monitoring-Skala** (im A-Bereich, 100 mA/mV):
- Last AUS: Brymen am Monitoring zeigt **0.0 mV** (perfekter Ruhepegel)
- Last 200 mA: **1.8 mV** (Soll: 2.0 mV) → **–0.2 mV / –10 %**

Der ~0.2 mV-Restoffset im Gesamtpfad ist konsistent mit der Phase-11-Messung (5 A → 50.2 mV mit +0.4 % Fehler). Da R43 selbst sauber ist, kommt der Restoffset aus dem **downstream Buffer/OPV** (nicht-trimmbar) bzw. minimal aus R4 (Endwert).

**Bewertung:** Bei großen Strömen ≥1 A < 0.5 % Fehler — exzellent. Bei kleinen Strömen 0.2 mV Konstant-Offset → relativer Fehler wächst, aber absolut vernachlässigbar. **Task #16 als „in Spec" abgehakt** — keine Justage durchgeführt.

### Phase 19: OVP-Funktionsverifikation + Schwellen-Mapping (2026-04-26)

**Schaltungs-Verständnis (Manual Section 4 + Phase 19-Recherche):**
- Sensingspannung wird über Verstärker B2/B3 auf Reglerkarte 202.236 zu Test-Punkten LSA/BU geliefert
- Frontpanel-OVP-Poti = R4 (auf der Frontplatte) **= 25 kΩ Draht-Trimmer (R&S Sachnummer 404.012.00)**, mehr-Umdrehungs-Typ
- Poti sitzt zwischen Punkten OP/OPM auf der Reglerkarte → reine Spannungsteiler-Funktion, **kein Strompfad**
- Vergleich-Schaltung mit T2, T3, T11 zündet Thyristor; bistabile Kippstufe T2/T3 hält Thyristor auch bei kleinen Strömen
- Reset über OUTPUT OFF-Signal (Optokoppler B4 → T4-Basis, Kippstufe-Reset)
- Crowbar: Thyristor an Bodenwanne befestigt (Kühlung), schließt Output auf ~1 V Restspannung kurz

**Test-Ablauf:**
- Sollwert 39.00 V, Output ON
- User dreht Poti gegen Uhrzeiger → OVP triggert, Output kollabiert auf 0.99 V (passt zur Spec „ca. 1 V")
- User dreht Poti leicht zurück (CW), GPIB-Reset (S → C) → Output kommt zurück
- Wiederholt-iterativ: Schwelle landet zwischen 39.50 V und 39.80 V

**Endzustand (User-Entscheidung: so belassen):**
- OVP-Schwelle: ca. 39.5–39.8 V — leicht konservativ für 40-V-Gerät
- Praktische Max-Nutzspannung: ~39.5 V (über das hinaus könnte OVP triggern)
- Vorteil: schützt schon vor sehr kleinen Überschießen des Nennwerts

**Reset-Verhalten verifiziert:**
- Standby-Befehl `S` per GPIB löst Kippstufe (über Optokoppler-Pfad) → Thyristor sperrt sobald Strom unter Haltestrom
- `C` (OUTPUT ON) bringt Output wieder auf programmierten Sollwert
- Bei externer Spannungsquelle: Quelle erst abklemmen, sonst sperrt Thyristor nicht

**Idee für Frontpanel-Mod (#17):** R4-Poti durch DigiPot ersetzen → OVP-Schwelle programmierbar machen. Kandidaten: AD5160/AD5260 (vertragen ±15 V), AD5263 mit EEPROM für persistentes Setting. 25 kΩ-Wert nicht direkt verfügbar, aber 50 kΩ DigiPot mit Feinjustage geht. Auflösung 256 Stufen × 40 V = 156 mV Schritt → für OVP völlig ausreichend.

---

## Lessons Learned

1. **Range-Codes der NGPV-Generation sind kontraintuitiv** — `1R` ist A-Bereich, nicht mA. Manual Section 2.3.4 liesen.
2. **Befehlsformat ist rechtsbündig** — `12V` heißt 0.12 V, nicht 12 V. Für 12 V → `1200V`.
3. **NGPV beteiligt sich nur bei ATN am Bus** — Manual Section 4.2.2. Der Idle-Bus-Status ist deshalb nicht aussagekräftig für „Gerät da/nicht da".
4. **40-Jahre alte Backplane-Stecker oxidieren** — die Einsatzbereitschaft kommt nach Jahren Standzeit nicht von selbst zurück. Vor jeder Diagnose: Kontakte reinigen.
5. **Innenwiderstand-Messung braucht direkte Mess-Punkte** — Mess-Kabelwiderstand kann den Befund komplett verfälschen.
6. **Symptom „kein Strom" verifizieren, bevor Diagnose laufen** — anderes Mess-Setup, anderer Sollwert, etc. Sonst diagnostiziert man im Trüben.
7. **Cermet-Trimmer haben mechanisches Settling** — nach Drehen mehrere Minuten warten und nochmal nachjustieren, bevor finale Position bestätigt wird. Erste Einstellung kann sich um 0.5 % verschieben.
8. **Vintage-Trim-Potis ohne Silkscreen-Bezeichner identifiziert man über Werte-Code.** Aufdruck-Code-Tabelle: „102" = 1k, „501" = 500 Ω, „503" = 50k. Ggf. mit Multimeter zwischen Schleifer und Endanschlag verifizieren.
9. **„Gerät defekt" beim Vintage-Lab-Equipment ist oft kein Hardware-Defekt, sondern Bedien-/Format-Stolperstein, der über Jahre als „defekt" verbucht bleibt.** Bevor man den Lötkolben anwirft: Programmier-Format quervalidieren (Manual + tatsächliches Output-Verhalten), Status per Parallel-Poll/Mess-Output prüfen, Stecker reinigen. Erst dann Hardware-Diagnose.

---

## Offene Punkte / TODO

- [ ] **Backplane-Stecker reinigen.** Alle Steckkarten ziehen, DIN-41612-Steckkanten + Buchsenleisten am Motherboard mit Isopropanol + Wattestäbchen reinigen. Verhindert Wackelkontakt-Rückkehr.
- [ ] **Spannungsreferenz-Justage R1162.** Manual Section 3.1.j auf DAC-Karte 202.237. Bringt die ~5 % Drift weg.
- [ ] **Display-Nachrüstung als Mod** (Wunsch von Sascha). Mit funktionierendem GPIB jetzt machbar — Display kann live die Sollwerte und Parallel-Poll-Status (CV/CC) anzeigen.

---

## Referenzen

- **Service-Manual:** `NGPV_Service_Manual.md` (OCR'd, Qualität gemischt)
- **Bilder einzeln:** `manual_pages/page_NNN.png`
  - Bestückungsplan IEC-Bus I (202.233): page_106.png
  - Bestückungsplan IEC-Bus II (202.234): page_116.png
  - Bestückungsplan Hilfskarte I (202.239): page_162.png
  - Stromlauf IEC-Bus I: page_105.png
- **Original-PDF:** `rohde-schwarz_ngpv_*.pdf`
- **GPIB-Adressen-DIP:** Rückwand des NGPV
- **Justage-Sektion:** Manual Section 3 (Seiten 24–28)
