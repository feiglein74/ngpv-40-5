#!/usr/bin/env python3
"""Adapter aus haengendem ATN-Mode rausholen ohne Modul-Reload."""

import time
import gpib as _gpib
import Gpib

LINES = [
    ("DAV",  _gpib.BusDAV),
    ("NDAC", _gpib.BusNDAC),
    ("NRFD", _gpib.BusNRFD),
    ("IFC",  _gpib.BusIFC),
    ("REN",  _gpib.BusREN),
    ("SRQ",  _gpib.BusSRQ),
    ("ATN",  _gpib.BusATN),
    ("EOI",  _gpib.BusEOI),
]


def show(bd, label):
    bits = _gpib.lines(bd)
    s = " ".join(f"{n}={'1' if bits & m else '0'}" for n, m in LINES)
    print(f"[{label:<28}] {s}")


def main():
    bd = _gpib.find("gpib0")
    show(bd, "vorher")

    # 1) Versuch: System-Controller toggle (sollte ATN freigeben)
    print("\n[Aktion] System-Controller off->on Toggle")
    try:
        _gpib.config(bd, _gpib.IbcSC, 0)
        time.sleep(0.05)
        show(bd, "nach SC=0")
        _gpib.config(bd, _gpib.IbcSC, 1)
        time.sleep(0.05)
        show(bd, "nach SC=1")
    except Exception as e:
        print(f"  Exception: {type(e).__name__}: {e}")

    # 2) IFC und dann sicherstellen dass ATN released wird
    print("\n[Aktion] interface_clear()")
    try:
        _gpib.interface_clear(bd)
        time.sleep(0.2)
        show(bd, "nach IFC")
    except Exception as e:
        print(f"  Exception: {type(e).__name__}: {e}")

    # 3) Versuch via Gpib hochlevel: clear() auf Board
    print("\n[Aktion] Gpib(board).clear()  (Selective Device Clear sendung)")
    try:
        b = Gpib.Gpib("gpib0")
        # Nicht moeglich auf Board direkt, also command UNL+UNT senden
        # UNL = 0x3F (Universal Unlisten), UNT = 0x5F (Universal Untalk)
        b.command(bytes([0x3F, 0x5F]))
        time.sleep(0.05)
        show(bd, "nach UNL+UNT")
    except Exception as e:
        print(f"  Exception: {type(e).__name__}: {e}")

    print("\n--- Wenn ATN jetzt = 0 ist, kannst du sauber weitertesten ---")


if __name__ == "__main__":
    main()
