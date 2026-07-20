#!/usr/bin/env python3
"""Kalibrierungs-Setup: 35.00 V / 1.00 A im A-Bereich, OUTPUT ON.
Brymen + Fluke an +SENSING/-SENSING; R1162 (1k bei Ru) drehen, bis 35.000 V."""

import time
import Gpib
import gpib as _gpib


def cmd(dev, payload, pause=0.2):
    print(f"  -> {payload!r}")
    dev.write(payload)
    time.sleep(pause)


def main():
    print("=== NGPV Kalibrierungs-Setup: 35.00 V ===\n")

    bd = _gpib.find("gpib0")
    _gpib.interface_clear(bd)
    time.sleep(0.3)

    ngpv = Gpib.Gpib("ngpv")
    ngpv.timeout(_gpib.T3s)

    print("Standby:")
    cmd(ngpv, b"S", pause=0.5)

    print("Bereich = A (1R):")
    cmd(ngpv, b"1R", pause=0.5)

    print("Spannung = 35.00 V:")
    cmd(ngpv, b"3500V")

    print("Strom-Limit = 1.00 A:")
    cmd(ngpv, b"100A")

    print("OUTPUT ON:")
    cmd(ngpv, b"C", pause=1.0)

    print("\n--- NGPV liefert jetzt 35.00 V an +/- SENSING ---")
    print("Drehe R1162 (1k-Poti am Ru-Punkt), bis Brymen 35.000 V zeigt.")


if __name__ == "__main__":
    main()
