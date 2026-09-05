#!/usr/bin/env python3
"""Guard the board's copper against accidental scripted replacement.

    python3 tools_route_guard.py check    # exit 1 if the board has hand edits
    python3 tools_route_guard.py stamp    # record the current copper as ours

WHY THIS EXISTS. The historical route driver deleted every track and via before
re-adding them from a route table. The production route is now maintained in
the board itself, and the route driver is retired; this guard remains as a
read-only copper fingerprint check plus an explicit stamp operation.

So the copper gets fingerprinted into .routed-by-script after each scripted
run. If the board no longer matches, someone has routed by hand and a run
would throw it away.

WHY IT IS A SEPARATE FILE. pcbnew's SWIG bindings segfault at interpreter
shutdown on this build - exit 139, reliably, after the board is safely written.
A crash takes buffered stdout and any unflushed file with it, so a stamp
written inside tools_route.py came out zero bytes every time, and an empty
stamp then blocks every subsequent run. Nothing here imports pcbnew, so
nothing here can crash that way.
"""

import hashlib
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BOARD = os.path.join(HERE, "moisture-sensor-carrier.kicad_pcb")
STAMP = os.path.join(HERE, ".routed-by-script")

# Tracks and vias only. Zone fills are derived, footprints and graphics are not
# this script's business, and both change for reasons that have nothing to do
# with routing.
COPPER = re.compile(r'\(segment.*?\n\t\)|\(via\b.*?\n\t\)', re.S)


def fingerprint(path=BOARD):
    items = COPPER.findall(open(path).read())
    return hashlib.sha256("".join(sorted(items)).encode()).hexdigest()[:16], len(items)


def stamp():
    fp, n = fingerprint()
    with open(STAMP, "w") as fh:
        fh.write(fp + "\n")
        fh.flush()
        os.fsync(fh.fileno())
    print("stamped %s  (%d copper items)" % (fp, n))
    return 0


def check(quiet=False):
    if not os.path.exists(STAMP):
        if not quiet:
            print("no stamp yet - run 'stamp' after the next scripted route")
        return 0
    want = open(STAMP).read().strip()
    have, n = fingerprint()
    if not want:
        print("ABORT: .routed-by-script is empty, so nothing can be verified.\n"
              "  Re-stamp deliberately if the board is known good:\n"
              "    python3 tools_route_guard.py stamp")
        return 1
    if want != have:
        print("ABORT: the board's copper is not what the last stamped baseline recorded.\n"
              "  stamped %s   board %s  (%d copper items)\n"
              "  The production board is hand-routed and the historical route driver\n"
              "  is retired, so no scripted overwrite is available. Options:\n"
              "    this script  stamp        accept the board as the new baseline"
              % (want, have, n))
        return 1
    if not quiet:
        print("board matches the stamp (%s, %d copper items)" % (have, n))
    return 0


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "check"
    if mode not in ("check", "stamp"):
        raise SystemExit(__doc__)
    sys.exit(stamp() if mode == "stamp" else check())
