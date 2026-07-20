#!/usr/bin/env python3
"""Diagnose-Skript fuer NGPV ueber Linux-GPIB / 82357B.

Setzt am Start IFC, damit der Adapter nicht in einem haengenden ATN-Zustand
aus einem vorigen TIMO-Schreibversuch sitzt.
"""

import sys
import time

import Gpib
import gpib as _gpib


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


def show_lines(bd, label):
    bits = _gpib.lines(bd)
    print(f"\n[{label}] lines=0x{bits:04x}")
    for name, mask in LINES:
        a = "ON " if bits & mask else "off"
        print(f"  {name:<4} {a}")


def try_write(name, payload, timeout_const=_gpib.T3s):
    print(f"\n[Schreibversuch] '{payload.decode()}' -> {name}")
    try:
        dev = Gpib.Gpib(name)
        dev.timeout(timeout_const)
        dev.write(payload)
        print(f"  OK, ibsta=0x{dev.ibsta():04x}, ibcnt={dev.ibcnt()}")
        return True
    except _gpib.GpibError as e:
        print(f"  GpibError: {e}")
        return False
    except Exception as e:
        print(f"  {type(e).__name__}: {e}")
        return False


def main():
    print("=== NGPV-Diagnose ueber 82357B ===")

    bd = _gpib.find("gpib0")
    print(f"Board-Descriptor: {bd}")

    # Sauberer Start: IFC, damit ein evtl. haengender ATN-Zustand zerstoert wird
    print("\n[Init] interface_clear() um Adapter-Hang zu loesen")
    _gpib.interface_clear(bd)
    time.sleep(0.2)
    show_lines(bd, "Nach Reset-IFC")

    try_write("ngpv", b"12V")
    show_lines(bd, "Nach 12V")

    # IFC zwischendrin um sauberen Bus zu garantieren
    _gpib.interface_clear(bd)
    time.sleep(0.2)

    try_write("ngpv", b"5A")
    show_lines(bd, "Nach 5A")

    # Final-Reset, damit Adapter sauber bleibt fuer den naechsten Lauf
    _gpib.interface_clear(bd)
    return 0


if __name__ == "__main__":
    sys.exit(main())
