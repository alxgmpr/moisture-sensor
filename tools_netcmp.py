#!/usr/bin/env python3
"""Canonical netlist fingerprint, for proving a schematic redraw changed only drawing.

    python3 tools_netcmp.py save  <file.json>   # snapshot current netlist
    python3 tools_netcmp.py check <file.json>   # diff current netlist against it

Nets are compared as sets of (ref, pin), keyed by net name. Auto-generated
"unconnected-(...)" names are normalised to the single pin they carry, so a
no-connect keeps its identity even if KiCad renumbers it.
"""
import json
import os
import re
import subprocess
import sys
import tempfile

KICAD_CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
SCH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "nrf-moisture-sensor.kicad_sch")


def tokenize(text):
    return re.findall(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()"]+', text)


def parse(text):
    stack = [[]]
    for t in tokenize(text):
        if t == '(':
            stack.append([])
        elif t == ')':
            v = stack.pop()
            stack[-1].append(v)
        elif t.startswith('"'):
            stack[-1].append(t[1:-1])
        else:
            stack[-1].append(t)
    return stack[0][0]


def find(node, key):
    return [c for c in node if isinstance(c, list) and c and c[0] == key]


def first(node, key):
    r = find(node, key)
    return r[0] if r else None


def netlist():
    with tempfile.NamedTemporaryFile(suffix=".net", delete=False) as fh:
        tmp = fh.name
    try:
        subprocess.run([KICAD_CLI, "sch", "export", "netlist",
                        "--format", "kicadsexpr", "-o", tmp, SCH],
                       check=True, capture_output=True)
        root = parse(open(tmp).read())
    finally:
        os.unlink(tmp)

    out = {}
    for n in find(first(root, 'nets'), 'net'):
        name = first(n, 'name')[1]
        nodes = sorted((first(nd, 'ref')[1], first(nd, 'pin')[1])
                       for nd in find(n, 'node'))
        if name.startswith('unconnected-'):
            name = "NC:%s.%s" % nodes[0]
        # A local label on the root sheet is named "/FOO"; a global power symbol
        # names the same net "FOO". That prefix is a sheet-path artifact, not a
        # connectivity change, so it is stripped before comparing.
        name = name.lstrip('/')
        out[name] = ["%s.%s" % rp for rp in nodes]
    return out


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'check'
    path = sys.argv[2] if len(sys.argv) > 2 else 'netlist-fingerprint.json'
    cur = netlist()

    if mode == 'save':
        json.dump(cur, open(path, 'w'), indent=1, sort_keys=True)
        print("saved %d nets to %s" % (len(cur), path))
        return 0

    old = json.load(open(path))
    added = sorted(set(cur) - set(old))
    removed = sorted(set(old) - set(cur))
    changed = sorted(k for k in set(cur) & set(old) if cur[k] != old[k])

    if not (added or removed or changed):
        print("netlist identical: %d nets, drawing-only change" % len(cur))
        return 0

    print("NETLIST CHANGED  (%d nets before, %d after)" % (len(old), len(cur)))
    for k in removed:
        print("  - %-26s %s" % (k, " ".join(old[k])))
    for k in added:
        print("  + %-26s %s" % (k, " ".join(cur[k])))
    for k in changed:
        print("  ~ %s" % k)
        print("      was: %s" % " ".join(old[k]))
        print("      now: %s" % " ".join(cur[k]))
    return 1


if __name__ == '__main__':
    sys.exit(main())
