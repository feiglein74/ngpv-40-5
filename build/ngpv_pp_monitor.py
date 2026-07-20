#!/usr/bin/env python3
"""Live-Monitor: pollt CV/CC-Status alle 200 ms und zeigt Übergänge an."""

import ctypes
import time
import Gpib
import gpib as _gpib

libgpib = ctypes.CDLL("/usr/lib/x86_64-linux-gnu/libgpib.so.0")
libgpib.ibppc.argtypes = [ctypes.c_int, ctypes.c_int]
libgpib.ibppc.restype = ctypes.c_int
libgpib.ibrpp.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_char)]
libgpib.ibrpp.restype = ctypes.c_int


def main():
    bd = _gpib.find("gpib0")
    ngpv = Gpib.Gpib("ngpv")
    ngpv.timeout(_gpib.T3s)

    libgpib.ibppc(ngpv.id, 0x6E)
    time.sleep(0.1)

    print("Live-Monitor (Strg-C zum Beenden):")
    print("  Punkt = unverändert, V/C = Wechsel\n")

    result = ctypes.c_char(b'\x00')
    last = None
    t0 = time.time()
    try:
        while True:
            libgpib.ibrpp(bd, ctypes.byref(result))
            byte = ord(result.value) if result.value else 0
            cv = bool(byte & 0x40)
            mark = "V" if cv else "C"
            if last != cv:
                print(f"\n  t={time.time()-t0:6.2f}s  → {'CV' if cv else 'CC'}", end="", flush=True)
                last = cv
            else:
                print(".", end="", flush=True)
            time.sleep(0.2)
    except KeyboardInterrupt:
        print("\n\n[abgebrochen]")


if __name__ == "__main__":
    main()
