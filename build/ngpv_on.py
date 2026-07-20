#!/usr/bin/env python3
"""Erster scharfer Funktionstest: 5V / 500mA programmieren, OUTPUT ON.
Multimeter an Ausgangsklemmen erwartet 5.00 V."""

import time
import Gpib
import gpib as _gpib


def cmd(dev, payload, pause=0.2):
    print(f"  -> {payload!r}")
    dev.write(payload)
    time.sleep(pause)


def main():
    print("=== NGPV-Einschalten ===")
    print("Stelle sicher: Multimeter im V-Bereich an den Ausgangsklemmen.\n")

    # Bus initialisieren
    bd = _gpib.find("gpib0")
    _gpib.interface_clear(bd)
    time.sleep(0.2)

    ngpv = Gpib.Gpib("ngpv")
    ngpv.timeout(_gpib.T3s)

    # Sicher in Standby starten
    print("Standby:")
    cmd(ngpv, b"S")

    # mA-Bereich (sicher fuer ersten Test)
    print("Bereich = mA:")
    cmd(ngpv, b"1R", pause=0.5)   # Relais brauchen Zeit

    # Spannung: 5.00 V (4 Stellen rechtsbuendig: 0500)
    print("Spannung = 5.00V:")
    cmd(ngpv, b"500V")

    # Strombegrenzung: 500 mA (3 Stellen, im mA-Bereich)
    print("Strom-Limit = 500mA:")
    cmd(ngpv, b"500A")

    # OUTPUT ON
    print("OUTPUT ON:")
    cmd(ngpv, b"C", pause=1.0)

    print("\n--- NGPV sollte jetzt 5.00 V an den Klemmen liefern ---")
    print("Was zeigt das Multimeter?")
    print("Tipp: Strg-C abbricht; OUTPUT bleibt dann an. Zum Ausschalten:")
    print("  python3 -c \"import Gpib; n=Gpib.Gpib('ngpv'); n.write(b'S')\"")


if __name__ == "__main__":
    main()
