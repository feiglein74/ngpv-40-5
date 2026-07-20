#!/usr/bin/env python3
"""Selbsttest des 82357B: jede Steuerleitung, die der Adapter aktiv treibt,
wird umgeschaltet und die line()-Anzeige verifiziert."""

import time
import gpib as _gpib

LINES = [
    ("DAV",  _gpib.ValidDAV,  _gpib.BusDAV),
    ("NDAC", _gpib.ValidNDAC, _gpib.BusNDAC),
    ("NRFD", _gpib.ValidNRFD, _gpib.BusNRFD),
    ("IFC",  _gpib.ValidIFC,  _gpib.BusIFC),
    ("REN",  _gpib.ValidREN,  _gpib.BusREN),
    ("SRQ",  _gpib.ValidSRQ,  _gpib.BusSRQ),
    ("ATN",  _gpib.ValidATN,  _gpib.BusATN),
    ("EOI",  _gpib.ValidEOI,  _gpib.BusEOI),
]


def board_descriptor():
    # Board-Descriptor 'gpib0' aus gpib.conf
    return _gpib.find("gpib0")


def show(label, board_id):
    bits = _gpib.lines(board_id)
    states = {n: bool(bits & b) for n, _, b in LINES}
    state_str = " ".join(f"{n}={'1' if v else '0'}" for n, v in states.items())
    print(f"[{label:<24}] {state_str}")
    return states


def main():
    bd = board_descriptor()
    print(f"Board-Descriptor: {bd}")
    print(f"linux-gpib version: {_gpib.version()}\n")

    print("== Initialer Status ==")
    s0 = show("init", bd)

    # --- REN-Test ---
    print("\n== REN-Toggle ==")
    _gpib.remote_enable(bd, 0)
    time.sleep(0.05)
    s = show("REN auf 0 gesetzt", bd)
    assert not s["REN"], "FEHLER: REN sollte off sein, ist on"
    _gpib.remote_enable(bd, 1)
    time.sleep(0.05)
    s = show("REN auf 1 gesetzt", bd)
    assert s["REN"], "FEHLER: REN sollte on sein, ist off"
    print("  -> REN-Treiber + Read OK")

    # --- IFC-Test (Pulse, schnell samplen) ---
    print("\n== IFC-Puls (mehrere Reads) ==")
    import threading

    samples = []
    stop = [False]

    def sampler():
        while not stop[0]:
            samples.append(_gpib.lines(bd))

    t = threading.Thread(target=sampler)
    t.start()
    _gpib.interface_clear(bd)
    time.sleep(0.05)
    stop[0] = True
    t.join()

    ifc_seen = sum(1 for v in samples if v & _gpib.BusIFC)
    print(f"  Samples insgesamt: {len(samples)}, IFC asserted in: {ifc_seen}")
    if ifc_seen > 0:
        print("  -> IFC-Treiber + Read OK")
    else:
        print(f"  -> WARNUNG: IFC-Puls nicht erfasst (zu schnell oder Treiber tot)")

    # --- ATN-Test via command-Modus ---
    # Wenn man ein Command schickt, geht ATN aktiv. Wir senden DCL (Device Clear,
    # universal command 0x14 = 20). DCL trifft alle Geraete, kein Listener noetig.
    print("\n== ATN-Test via Command-Write (DCL universal) ==")
    try:
        # Vor command:
        s = show("vor DCL", bd)
        # In linux-gpib gibt es .command() auf dem Board
        import Gpib
        board = Gpib.Gpib("gpib0")
        # 0x14 = DCL (Device Clear)
        board.command(bytes([0x14]))
        time.sleep(0.05)
        s = show("nach DCL", bd)
    except Exception as e:
        print(f"  Command-Write Exception: {type(e).__name__}: {e}")

    # --- Schreibversuch ohne Listener: was sagt der Bus dabei? ---
    print("\n== Schreibversuch (Listener pad=12) mit Sampling ==")
    try:
        import Gpib
        ngpv = Gpib.Gpib("ngpv")
        ngpv.timeout(_gpib.T1s)

        samples = []
        stop = [False]

        def sampler2():
            while not stop[0]:
                samples.append(_gpib.lines(bd))
                time.sleep(0.001)

        t = threading.Thread(target=sampler2)
        t.start()
        try:
            ngpv.write(b"12V")
        except _gpib.GpibError as e:
            print(f"  Write-Error (erwartet): {e}")
        stop[0] = True
        t.join()

        # ATN-Aktivierung waehrend des Versuchs?
        atn_seen = sum(1 for v in samples if v & _gpib.BusATN)
        ndac_seen = sum(1 for v in samples if v & _gpib.BusNDAC)
        nrfd_seen = sum(1 for v in samples if v & _gpib.BusNRFD)
        print(f"  Samples: {len(samples)}, "
              f"ATN_on: {atn_seen}, NDAC_on: {ndac_seen}, NRFD_on: {nrfd_seen}")
        if atn_seen == 0:
            print("  -> Adapter hat ATN nicht aktiviert. Treiber-Problem!")
        elif ndac_seen == 0 and nrfd_seen == 0:
            print("  -> ATN aktiviert, aber kein Geraet zog NDAC/NRFD low.")
            print("     -> Bus-Empfaenger der angeschlossenen Geraete antwortet nicht.")
        else:
            print("  -> Geraet hat sich gemeldet")
    except Exception as e:
        print(f"  Exception: {type(e).__name__}: {e}")

    print("\n== fertig ==")


if __name__ == "__main__":
    main()
