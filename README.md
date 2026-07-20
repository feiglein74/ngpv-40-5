# NGPV 40/5 — Reparatur & GPIB-Steuerung

Rohde & Schwarz **NGPV 40/5** (40 V / 5 A, Bestellbez. 192.0326.40), Blank-Panel-Variante —
rein IEC-Bus-programmierbar, ohne Display und Bedienelemente.

**Stand: funktional.** Das Gerät nahm über Jahre zwar Spannungssollwerte an, lieferte aber
keinen Strom an die Last. Ursache war kein Bauteildefekt, sondern das Zusammenspiel von drei
harmlosen Dingen:

1. **Das Gerät startet immer im mA-Bereich.** Manual S. 34: „Nach dem Netzanschalten ist am
   Gerät immer der mA-Bereich gewählt." Ohne ein explizites `1R` liegt der Strom-Endwert bei
   ~999 mA — die damalige Last war für ein Vielfaches ausgelegt.
2. **Das Sollwert-Format ist rechtsbündig.** `5A` programmiert nicht 5 A, sondern 0,05 A —
   im Default-mA-Bereich sogar nur 5 mA.
3. **Oxidierte DIN-41612-Backplane-Kontakte** nach Jahren Standzeit, intermittierend.

Alle drei wirken in dieselbe Richtung, und da die Blank-Panel-Variante kein Display hat, ist
der Wechsel in die Strombegrenzung ohne Multimeter oder Parallel-Poll nicht zu sehen: Das
Gerät regelt korrekt, nur eben auf einen Bruchteil des erwarteten Stroms. Nach
Kontaktreinigung und Referenzjustage arbeitet das Netzteil im Rahmen seiner Spezifikation.

## Aufbau

```
PC (Kali) ──USB── Keysight 82357B ──IEEE-488── NGPV 40/5 ──── Ausgangsklemmen
```

Das NGPV hat eine 24-polige IEEE-488-Buchse (trotz der Manual-Bezeichnung „IEC-625"),
der 82357B passt direkt. GPIB-Adresse **12**, per DIP an der Rückwand gesetzt und nur
beim Power-On gelatcht.

## Bedienung

```bash
ngpv 20v 0.01a     # Spannung + Strombegrenzung setzen
ngpv 5v            # nur Spannung
ngpv 20v 1a on     # Sollwerte + Output ein
ngpv off
```

Voraussetzung ist ein `ngpv`-Eintrag in `/etc/gpib.conf` mit der richtigen GPIB-Adresse
(**PAD 12**, per DIP an der Rückwand, wird nur beim Power-On gelatcht):

```bash
bash setup_ngpv_conf.sh     # legt den Block an oder korrigiert den pad-Wert
```

Das ist kein Selbstzweck: Arbeiten an einem zweiten GPIB-Gerät haben den Wert schon
einmal stillschweigend verstellt, was sich nur als „Gerät antwortet nicht" äußert.

Der Wrapper liegt als `bin/ngpv` im Repo und spricht linux-gpib über `python3-gpib`.
Damit er im PATH liegt, ist er nach `~/.local/bin/ngpv` gesymlinkt:

```bash
ln -sf "$PWD/bin/ngpv" ~/.local/bin/ngpv
```

Das rohe Befehlsformat des Geräts sowie die Eigenheiten des Wrappers stehen in `CLAUDE.md`.

## Aktuelle Genauigkeit

| Bereich | Stand |
|---|---|
| Spannung | ~1 % nach R1162-Justage (35 V Soll → 35,001 V) |
| Strom, A-Bereich | Endwert ~10 % zu hoch — per Sollwert-Reduktion ×0,91 kompensiert |
| Strom, mA-Bereich | ab ~500 mA korrekt; darunter deutlich zu niedrig, bei 50 mA unbrauchbar |

Die mA-Justage (R1163 → R40) ist der nächste offene Arbeitsschritt, siehe `TODO.md`.
Relevant, weil das Gerät für Cap-Reform als 40-V-Quelle genutzt wird.

## Dateien

| Datei | Inhalt |
|---|---|
| `bin/ngpv` | CLI-Wrapper für die GPIB-Steuerung |
| `setup_ngpv_conf.sh` | Trägt den `ngpv`-Block in `/etc/gpib.conf` ein bzw. korrigiert ihn |
| `REPAIR_LOG.md` | Vollständige Reparaturhistorie, Linux-GPIB-Setup, Lessons Learned |
| `TODO.md` | Schritt-für-Schritt-Anleitung für die mA-Bereich-Stromjustage |
| `CLAUDE.md` | Befehlsformat, Fallstricke, Bauteil-Identifikation |
| `MOD_FRONTPANEL_BOM.md` | BOM für die geplante Display-Nachrüstung |
| `build/` | Eigene Diagnose-Skripte, `gpib.conf`, udev-Regeln |

Die Doku verweist an einigen Stellen auf `NGPV_Service_Manual.md` und
`manual_pages/page_NNN.png` — das Service-Manual von Rohde & Schwarz. Es ist aus
Urheberrechtsgründen **nicht Teil dieses Repos**; das PDF findet sich über die
einschlägigen Archive für Vintage-Messtechnik.

Das komplette Linux-GPIB-Setup ist in `REPAIR_LOG.md` reproduzierbar dokumentiert
(Out-of-Tree-Build von linux-gpib, Firmware-Load für den 82357B, udev-Permissions).
