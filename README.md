# NGPV 40/5 — Reparatur & GPIB-Steuerung

Rohde & Schwarz **NGPV 40/5** (40 V / 5 A, Bestellbez. 192.0326.40), Blank-Panel-Variante —
rein IEC-Bus-programmierbar, ohne Display und Bedienelemente.

**Stand: funktional.** Das Gerät nahm über Jahre zwar Spannungssollwerte an, lieferte aber
keinen Strom an die Last. Ursache war kein Bauteildefekt, sondern eine Kombination aus
oxidierten DIN-41612-Backplane-Steckern und einer Fehlinterpretation der Range-Codes.
Nach Steckerreinigung und Referenzjustage arbeitet das Netzteil im Rahmen seiner Spezifikation.

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
