#!/usr/bin/env python3
"""Parallel-Poll des NGPV: liest CV/CC-Status (1 Bit) per IEEE-488 PP-Mechanismus.

Manual Section 2.3.7: PPE auf DIO 7 mit Sense=1 → wenn CV aktiv, ist Bit 6 gesetzt.
"""

import ctypes
import time
import Gpib
import gpib as _gpib

libgpib = ctypes.CDLL("/usr/lib/x86_64-linux-gnu/libgpib.so.0")

libgpib.ibppc.argtypes = [ctypes.c_int, ctypes.c_int]
libgpib.ibppc.restype = ctypes.c_int

libgpib.ibrpp.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_char)]
libgpib.ibrpp.restype = ctypes.c_int


def pp_once(board, label):
    result = ctypes.c_char(b'\x00')
    rc = libgpib.ibrpp(board, ctypes.byref(result))
    pp_byte = ord(result.value) if result.value else 0
    cv_bit = bool(pp_byte & 0x40)
    mode = "CV  (Konstantspannung)" if cv_bit else "CC  (Konstantstrom)"
    print(f"  [{label}] ibrpp rc=0x{rc:08x}  byte=0x{pp_byte:02x} ({pp_byte:08b})  → {mode}")
    return cv_bit


def main():
    print("=== NGPV Parallel-Poll: CV/CC-Status ===\n")

    bd = _gpib.find("gpib0")
    ngpv = Gpib.Gpib("ngpv")
    ngpv.timeout(_gpib.T3s)

    # PPE byte = 0110 SPPP
    #   sense (S) = 1: Bit asserted when CV true
    #   position (PPP) = 110 = 6 → DIO 7
    # → 0110 1110 = 0x6E
    PPE = 0x6E
    print(f"PPC/PPE: 0x{PPE:02x}  (DIO 7, sense=1)")
    rc = libgpib.ibppc(ngpv.id, PPE)
    print(f"  ibppc rc=0x{rc:08x}\n")
    time.sleep(0.1)

    print("Drei aufeinanderfolgende Polls:")
    for i in range(3):
        pp_once(bd, f"#{i+1}")
        time.sleep(0.5)


if __name__ == "__main__":
    main()
