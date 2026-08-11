#!/usr/bin/env python3
"""Generate the moisture-sensor-carrier schematic (nRF54L15 + nPM1300 + FDC1004).

Layout is organised into labelled functional blocks, each drawn with a dashed
box, so passives belonging to different subsystems do not get mixed up.

Connectivity is expressed with global labels on short wire stubs off each pin.
That yields a correct netlist without full wire-routing geometry; positions can
be tidied in Eeschema afterwards.

Run:  python3 tools_gen_sch.py
"""
import math
import re, uuid
import re as _re2

# Derive the project root from this file so the generator writes into whichever
# checkout it is run from. A hardcoded path silently overwrites the main working
# tree when the script is run inside a git worktree.
import os
PROJ = os.path.dirname(os.path.abspath(__file__))
SS = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols"
ROOT_UUID = "29551000-a13a-494c-a3a3-b85b9fc11a3c"
PROJNAME = "moisture-sensor-carrier"

def U():
    return str(uuid.uuid4())

G = 2.54
def snap(v):
    """Snap to 2.54 mm so every derived pin coordinate stays on KiCad's
    1.27 mm connection grid."""
    return round(round(float(v) / G) * G, 4)

# ---------------------------------------------------------------- symbol defs
def top_level_symbols(path):
    s = open(path).read()
    out = {}
    for m in re.finditer(r'\n(\t?)\(symbol "([^"]+)"', s):
        name = m.group(2)
        if re.search(r'_\d+_\d+$', name):
            continue
        start, depth, i = m.start() + 1, 0, m.start() + 1
        while i < len(s):
            if s[i] == '(':
                depth += 1
            elif s[i] == ')':
                depth -= 1
                if depth == 0:
                    out[name] = s[start:i + 1]
                    break
            i += 1
    return out

SRC = {
    "Device":            top_level_symbols(f"{SS}/Device.kicad_sym"),
    "power":             top_level_symbols(f"{SS}/power.kicad_sym"),
    "Connector":         top_level_symbols(f"{SS}/Connector.kicad_sym"),
    "Connector_Generic": top_level_symbols(f"{SS}/Connector_Generic.kicad_sym"),
    "nordic":            top_level_symbols(f"{PROJ}/lib/nordic/NRF54L15-QFAA-R.kicad_sym"),
    "npm1300":           top_level_symbols(f"{PROJ}/lib/nordic/NPM1300-QEAA-R7.kicad_sym"),
    "fdc":               top_level_symbols(f"{PROJ}/lib/FDC1004.kicad_sym"),
    "sht4x":             top_level_symbols(f"{PROJ}/lib/SHT4x.kicad_sym"),
    "tps7a16":           top_level_symbols(f"{PROJ}/lib/TPS7A1650.kicad_sym"),
    # Project power symbols for the rails KiCad's stock library does not carry.
    # Regenerate with tools_gen_power_lib.py.
    "power_local":       top_level_symbols(f"{PROJ}/lib/power_local.kicad_sym"),
}

# Every rail gets a power SYMBOL, never a text label.
#
# A power symbol is checked by ERC as a rail and carries its own graphic, so a
# reader sees "this is the 3V3 supply" rather than having to match a string.
# A plain label is only a name: before this, "+3V3" appeared 21 times as text,
# and a single typo in one of those copies would have silently split the rail
# into two nets that ERC had no reason to complain about.
#
# Maps net name -> (library, symbol). GND is the stock one and points down;
# the rest point up.
RAIL_SYMBOL = {
    "GND":         ("power", "GND"),
    "+3V3":        ("power", "+3V3"),
    "VSYS":        ("power_local", "VSYS"),
    "VBAT":        ("power_local", "VBAT"),
    "VBUS_IN":     ("power_local", "VBUS_IN"),
    "SOLAR_PANEL": ("power_local", "SOLAR_PANEL"),
    "SOLAR_5V":    ("power_local", "SOLAR_5V"),
    "FDC_VDD":     ("power_local", "FDC_VDD"),
}

def pins_of(defn):
    res = []
    for m in re.finditer(
        r'\(pin\s+(\w+)\s+\w+\s*\(at ([-\d.]+) ([-\d.]+) (\d+)\)\s*\(length ([\d.]+)\)(.*?)\n\t\t\t\)',
        defn, re.S):
        typ, x, y, rot, ln, tail = m.groups()
        nm = re.search(r'\(name "([^"]*)"', tail)
        nu = re.search(r'\(number "([^"]*)"', tail)
        if nu:
            res.append((nu.group(1), nm.group(1) if nm else "", typ,
                        float(x), float(y), int(rot)))
    return res


# ---------------------------------------------------------------- footprints
# Hand-solder variants everywhere they exist. The ONE exception is the RF
# matching network (L2/L3/L4/C6/C9/C11): Nordic's component values are matched
# to their reference land pattern, and hand-solder pads add enough parasitic
# capacitance at 2.4 GHz to shift a 0.3 pF cap. Those stay 0201 standard.
HS_C0402 = "Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder"
HS_C0603 = "Capacitor_SMD:C_0603_1608Metric_Pad1.08x0.95mm_HandSolder"
HS_C0805 = "Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder"
HS_R0402 = "Resistor_SMD:R_0402_1005Metric_Pad0.72x0.64mm_HandSolder"
HS_R0603 = "Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder"
HS_L0402 = "Inductor_SMD:L_0402_1005Metric_Pad0.77x0.64mm_HandSolder"
HS_L0603 = "Inductor_SMD:L_0603_1608Metric_Pad1.05x0.95mm_HandSolder"
RF_C0201 = "Capacitor_SMD:C_0201_0603Metric"
RF_L0201 = "Inductor_SMD:L_0201_0603Metric"
TP       = "TestPoint:TestPoint_Pad_D1.0mm"

FOOTPRINTS = {
    # MCU support (Nordic QFAA ref topology, sizes relaxed to 0402 for assembly)
    "L1": HS_L0603, "FB1": HS_L0402,
    "C1": HS_C0402, "C2": HS_C0402, "C12": HS_C0402, "C5": HS_C0402,
    "C3": HS_C0603, "C4": HS_C0402, "C7": HS_C0402, "C8": HS_C0402,
    "C10": HS_C0402, "C13": HS_C0402, "R1": HS_R0402,
    # RF matching - standard 0201 pads, see note above
    "L2": RF_L0201, "L3": RF_L0201, "L4": RF_L0201,
    "C6": RF_C0201, "C9": RF_C0201, "C11": RF_C0201,
    # PMIC
    "C20": HS_C0603, "C21": HS_C0603, "C22": HS_C0603, "C23": HS_C0603,
    "C24": HS_C0603, "C25": HS_C0402,
    "L10": "Inductor_SMD:L_Murata_DFE201610P",
    "R20": HS_R0402, "R21": HS_R0402,
    # sense front end
    "C26": HS_C0402, "C27": HS_C0402, "R22": HS_R0402, "R23": HS_R0402,
    # battery / charge status
    "R25": HS_R0402, "R26": HS_R0402,
    "D3": "LED_SMD:LED_0603_1608Metric_Pad1.05x0.95mm_HandSolder",
    "D4": "LED_SMD:LED_0603_1608Metric_Pad1.05x0.95mm_HandSolder",
    "TH1": "footprints:Thermistor_SEMITEC_103JT_Wired",
    # solar pre-regulator + OR-ing. U5's DGN land pattern was checked against
    # TI SBVS171F DGN0008C: 8 pads 1.4 x 0.45 mm on 0.65 mm pitch, rows on
    # 4.4 mm centres, thermal pad metal ~1.6 x 1.92 mm. KiCad's HVSSOP-8 is
    # 1.45 x 0.5 on +/-2.15 with a 1.57 x 1.89 pad - generous on every
    # dimension rather than short, so this one does NOT need a project
    # footprint the way X1/X2 did.
    "U5": "Package_SO:HVSSOP-8-1EP_3x3mm_P0.65mm_EP1.57x1.89mm",
    "C30": HS_C0805, "C31": HS_C0603,
    "D5": "Diode_SMD:D_SOD-323_HandSoldering",
    # clocks. Standard pads on X2 (no hand variant for 2016-4pin exists).
    # Micro Crystal CM8V-T1A. The vendor land pattern (0.8 x 1.5 mm pads on
    # 1.5 mm centres) is what the datasheet specifies; KiCad's generic 2012
    # footprints use 0.6 or 1.05 mm pads on different centres.
    "X1": "footprints:XTAL_CM8V-T1A_2012",
    # Epson's own land pattern. KiCad's generic 2016 4-pin uses 0.90 x 0.80 mm
    # pads on 1.40 x 1.10 centres - a 2.30 mm outer span against Epson's 1.45.
    "X2": "footprints:XTAL_FA-128_2016_4Pin",
    # connectors
    # Connectors. J2/J3/J4 are height-constrained: the Hammond 1551WK leaves
    # 6.70 mm of clear component height under the cell (LAYOUT.md §9), and JST PH
    # is 8 mm mounting height while a 2x5 1.27 mm header is comparable. JST GH is
    # 4.20 mm (measured from the vendor STEP) and rated 1 A, well over the 500 mA
    # charge current; Tag-Connect costs nothing at all in height and uses the
    # standard 10-pin Cortex pinout J4 already had.
    "J1": "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12",
    # Side-entry, not top-entry. Both are 4.2 mm tall on an identical board
    # footprint, so this is not about height: the cell hangs from the lid to
    # within 6.70 mm of the board, and a vertical header sends the lead
    # straight up into it. Horizontal exits parallel and routes underneath.
    "J2": "Connector_JST:JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical",
    "J3": "Connector_JST:JST_GH_SM02B-GHS-TB_1x02-1MP_P1.25mm_Horizontal",
    "J4": "Connector:Tag-Connect_TC2050-IDC-NL_2x05_P1.27mm_Vertical",
    # U.FL receptacle for the antenna. Hirose U.FL-R-SMT-1(10): 50 ohm,
    # DC-8 GHz, VSWR <=1.3 to 3 GHz, mated height 1.9-2.4 mm, 30 mating
    # cycles. Verified against the Hirose catalogue drawing; KiCad's land
    # pattern matches the recommended pattern (4.00 mm GND span, SIG at
    # 1.9 mm) to within the stated +-0.05 mm.
    "J5": "Connector_Coaxial:U.FL_Hirose_U.FL-R-SMT-1_Vertical",
    "TP1": TP, "TP2": TP, "TP3": TP, "TP4": TP, "TP5": TP,
    # RF grounding net ties - see the RF block for what they enforce.
    # NT1 is a project footprint: the gap it has to bridge, between U1's pin-32
    # land and the centre pad, is 0.1905 mm, and a stock 0.5 mm net tie does not
    # fit in it.
    "NT1": "footprints:NetTie_VSSPA",
    "NT2": "NetTie:NetTie-2_SMD_Pad0.5mm",
    # The stock 0.5 mm net tie does not fit between C24 and U2, so NT3 uses a
    # compact project one.
    "NT3": "footprints:NetTie_Small",
}

# ---------------------------------------------------------------- emit buffers
parts, wires, labels, graphics, nocons, junctions = [], [], [], [], [], []
used_lib = {}
conn = []          # (pin_pt, end_pt, netname) for the collision self-check
pwr_n = [0]

def esc(t):
    return t.replace('\\', '\\\\').replace('"', '\\"')

def place(lib, name, ref, value, at, footprint="", dnp=False, rot=0, mpn=""):
    """Place a symbol.

    `value` is the ELECTRICAL value and nothing else - "1.5pF", "4.7uH". The
    part number goes in `mpn`, a hidden property, because Value is the field
    that gets drawn next to the symbol: "1.5pF GJM0335C1E1R5WB01" is 25
    characters of text hung off a 5 mm capacitor, and in a chain drawn on a
    12.7 mm pitch it lands on top of the neighbouring part. It also makes the
    MPN available to the BOM as a field instead of something to string-split.
    """
    footprint = footprint or FOOTPRINTS.get(ref, "")
    mpn_prop = ("" if not mpn else
                f'\n\t\t(property "MPN" "{esc(mpn)}"\n'
                f'\t\t\t(at {snap(at[0])} {snap(at[1])} 0)\n'
                f'\t\t\t(effects (font (size 1.27 1.27)) (hide yes))\n\t\t)')
    lib_id = f"{lib}:{name}"
    defn = SRC[lib][name]
    used_lib[lib_id] = defn
    x, y = snap(at[0]), snap(at[1])
    pl = pins_of(defn)
    pin_uuids = "\n".join(f'\t\t(pin "{p[0]}" (uuid "{U()}"))' for p in pl)
    if len(pl) > 4:
        top_y = y - max(p[4] for p in pl)
        ref_at, val_at = (x, round(top_y - 7.62, 4)), (x, round(top_y - 5.08, 4))
    else:
        ref_at, val_at = (x, round(y - 5.08, 4)), (x, round(y + 5.08, 4))
    parts.append(f'''\t(symbol
\t\t(lib_id "{lib_id}")
\t\t(at {x} {y} {rot})
\t\t(unit 1)
\t\t(exclude_from_sim no)
\t\t(in_bom yes)
\t\t(on_board yes)
\t\t(dnp {"yes" if dnp else "no"})
\t\t(fields_autoplaced yes)
\t\t(uuid "{U()}")
\t\t(property "Reference" "{esc(ref)}"
\t\t\t(at {ref_at[0]} {ref_at[1]} 0)
\t\t\t(effects (font (size 1.27 1.27)) (justify left))
\t\t)
\t\t(property "Value" "{esc(value)}"
\t\t\t(at {val_at[0]} {val_at[1]} 0)
\t\t\t(effects (font (size 1.27 1.27)) (justify left))
\t\t)
\t\t(property "Footprint" "{esc(footprint)}"
\t\t\t(at {x} {y} 0)
\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t){mpn_prop}
{pin_uuids}
\t\t(instances
\t\t\t(project "{PROJNAME}"
\t\t\t\t(path "/{ROOT_UUID}"
\t\t\t\t\t(reference "{esc(ref)}")
\t\t\t\t\t(unit 1)
\t\t\t\t)
\t\t\t)
\t\t)
\t)''')
    return x, y, defn

def _pin(defn, number):
    for p in pins_of(defn):
        if p[0] == number:
            return p
    raise KeyError(f"pin {number} not found")

def _pin_at(x, y, p, srot):
    """Absolute anchor of pin `p` on a symbol placed at (x, y) rotated `srot`.

    Symbol coordinates are Y-up; the sheet is Y-down. Rotate in symbol space
    first, then flip. A capacitor at srot=0 stands upright with pin 1 on top;
    at srot=90 it lies flat with pin 1 on the left, which is what a series
    element in a signal chain has to do.
    """
    _, _, _, px, py, prot = p
    a = math.radians(srot)
    ca, sa = math.cos(a), math.sin(a)
    rx = px * ca - py * sa
    ry = px * sa + py * ca
    return (round(x + rx, 4), round(y - ry, 4)), int((prot + srot) % 360)


def _endpoint(x, y, p, length, srot=0):
    """Pin anchor and the far end of its stub.

    KiCad pin rotation is the direction the pin extends from its anchor toward
    the symbol body, and schematic Y grows downward:
      0 -> body right, wire leaves -X      180 -> body left, wire leaves +X
      90 -> body up (-Y), wire leaves +Y   270 -> body down, wire leaves -Y
    """
    (ax, ay), rot = _pin_at(x, y, p, srot)
    if rot == 0:     return (ax, ay), (round(ax - length, 4), ay), "right", 0
    if rot == 180:   return (ax, ay), (round(ax + length, 4), ay), "left", 180
    if rot == 90:    return (ax, ay), (ax, round(ay + length, 4)), "right", 0
    return (ax, ay), (ax, round(ay - length, 4)), "left", 180

def _wire(a, b):
    wires.append(f'\t(wire (pts (xy {a[0]} {a[1]}) (xy {b[0]} {b[1]}))\n'
                 f'\t\t(stroke (width 0) (type default))\n\t\t(uuid "{U()}")\n\t)')

def stub(x, y, defn, number, net, length=5.08, srot=0):
    """Wire stub off `number` carrying a plain (local) net label.

    Single sheet, so local labels are sufficient - global labels would only add
    hierarchy machinery this design does not use.
    """
    p = _pin(defn, number)
    a, b, just, rot = _endpoint(x, y, p, length, srot)
    _wire(a, b)
    labels.append(
        f'\t(label "{esc(net)}"\n\t\t(at {b[0]} {b[1]} {rot})\n'
        f'\t\t(fields_autoplaced yes)\n'
        f'\t\t(effects (font (size 1.27 1.27)) (justify {just} bottom))\n'
        f'\t\t(uuid "{U()}")\n\t)')
    conn.append((a, b, net))

def junction(pt):
    junctions.append(f'\t(junction (at {pt[0]} {pt[1]}) (diameter 0)\n'
                     f'\t\t(color 0 0 0 0)\n\t\t(uuid "{U()}")\n\t)')


def terminal(pt, net, side="left"):
    """Name a free wire end -- a rail symbol if it is a rail, else a label.

    A chain has to start and end somewhere. The net it comes from lives on
    another block's IC pin, so the end carries the name across.
    """
    if net in RAIL_SYMBOL:
        lib, sym = RAIL_SYMBOL[net]
        place_power(sym, pt, lib)
    else:
        rot, just = (180, "left") if side == "right" else (0, "right")
        labels.append(
            f'\t(label "{esc(net)}"\n\t\t(at {pt[0]} {pt[1]} {rot})\n'
            f'\t\t(fields_autoplaced yes)\n'
            f'\t\t(effects (font (size 1.27 1.27)) (justify {just} bottom))\n'
            f'\t\t(uuid "{U()}")\n\t)')


def chain(blk, origin, net_in, items, pitch=17.78, drop=7.62):
    """Draw a series signal chain left to right, shunt legs hanging down.

    This is what a reference schematic looks like and what a label-per-pin
    schematic cannot show: the ORDER of a chain, and which node each shunt
    element sits on. The RF match is the case that matters -- Nordic draws
    ANT -> L2 -> L3 -> L4 with C6, C9 and C11 hanging off the nodes between
    them, and that ordering is the whole design. Spelling it as six parts each
    carrying two net labels is the same netlist and tells the reader nothing.

    items: ("series", ref, sym, value, net_after, mpn)
           ("shunt",  ref, sym, value, net_below, mpn)
    The MPN is optional and lands in a hidden property, not in Value.
    A shunt attaches to the node the chain is currently sitting on.
    """
    node_x, y = snap(origin[0]), snap(origin[1])
    net = net_in
    terminal((round(node_x - 5.08, 4), y), net, "left")
    _wire((round(node_x - 5.08, 4), y), (node_x, y))

    for item in items:
        kind, ref, sym, val, arg = item[:5]
        mpn = item[5] if len(item) > 5 else ""
        if kind == "series":
            cx = snap(node_x + pitch / 2)
            place("Device", sym, ref, val, (cx, y), rot=90, mpn=mpn)
            d = SRC["Device"][sym]
            (p1, _), (p2, _) = (_pin_at(cx, y, _pin(d, "1"), 90),
                                _pin_at(cx, y, _pin(d, "2"), 90))
            nxt = round(node_x + pitch, 4)
            _wire((node_x, y), p1)
            _wire(p2, (nxt, y))
            conn.append((p1, (node_x, y), net))
            conn.append((p2, (nxt, y), arg))
            node_x, net = nxt, arg
            # Name the node the element just created. Without this KiCad
            # auto-names it Net-(C6-Pad1), which is the same net electrically
            # but drops it out of every netclass pattern and DRU rule keyed on
            # RF_A / RF_B - silently, because an auto-named net is not an error.
            #
            # A rail gets its symbol here, not a label: BUCK2's output node IS
            # +3V3, and naming it with text would have been the one place on
            # the sheet where the 3V3 rail did not look like a rail.
            terminal((node_x, y), net, "left")
        else:
            cy = round(y + drop + 2.54, 4)
            place("Device", sym, ref, val, (node_x, cy), rot=0, mpn=mpn)
            d = SRC["Device"][sym]
            (p1, _) = _pin_at(node_x, cy, _pin(d, "1"), 0)
            _wire((node_x, y), p1)
            junction((node_x, y))
            conn.append((p1, (node_x, y), net))
            wire_pin(node_x, cy, d, "2", arg)
            blk.note(cy + 12)
        blk.maxx = max(blk.maxx, node_x + 16)
    # No terminal on the right: the last series element already labelled the
    # node it created, and a second name on the same point is just clutter.
    blk.note(y)
    return node_x, y


def place_power(sym, at, lib="power"):
    """Place a power symbol (a rail, GND, or PWR_FLAG). Its pin sits at the origin."""
    defn = SRC[lib][sym]
    used_lib[f"{lib}:{sym}"] = defn
    x, y = at
    pwr_n[0] += 1
    parts.append(f'''\t(symbol
\t\t(lib_id "{lib}:{sym}")
\t\t(at {x} {y} 0)
\t\t(unit 1)
\t\t(exclude_from_sim no)
\t\t(in_bom yes)
\t\t(on_board yes)
\t\t(dnp no)
\t\t(uuid "{U()}")
\t\t(property "Reference" "#PWR{pwr_n[0]:03d}"
\t\t\t(at {x} {y} 0)
\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t)
\t\t(property "Value" "{sym}"
\t\t\t(at {x} {y + 3.5} 0)
\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t)
\t\t(pin "1" (uuid "{U()}"))
\t\t(instances
\t\t\t(project "{PROJNAME}"
\t\t\t\t(path "/{ROOT_UUID}"
\t\t\t\t\t(reference "#PWR{pwr_n[0]:03d}")
\t\t\t\t\t(unit 1)
\t\t\t\t)
\t\t\t)
\t\t)
\t)''')

def rail(x, y, defn, number, net, length=5.08, srot=0):
    """Stub to a real power symbol rather than a text label.

    Used for every net in RAIL_SYMBOL. The symbol carries the net name itself,
    so no label is emitted and there is no string to get wrong.
    """
    lib, sym = RAIL_SYMBOL[net]
    p = _pin(defn, number)
    a, b, _, _ = _endpoint(x, y, p, length, srot)
    _wire(a, b)
    place_power(sym, b, lib)
    conn.append((a, b, net))

def nc(x, y, defn, number, srot=0):
    """No-connect flag directly on an intentionally unused pin."""
    p = _pin(defn, number)
    a, _, _, _ = _endpoint(x, y, p, 0, srot)
    nocons.append(f'\t(no_connect (at {a[0]} {a[1]}) (uuid "{U()}"))')

def wire_pin(x, y, defn, number, net, srot=0):
    """Dispatch: None -> no-connect, a rail -> power symbol, else net label.

    Signals still use labels: a label is the right tool for a point-to-point
    net that crosses the sheet. Rails do not, because a rail is a rail
    everywhere it appears and should look like one.
    """
    if net is None:
        nc(x, y, defn, number, srot)
    elif net in RAIL_SYMBOL:
        rail(x, y, defn, number, net, srot=srot)
    else:
        stub(x, y, defn, number, net, srot=srot)

# ------------------------------------------------------------------- blocks
class Block:
    """A titled region that sizes itself to its contents.

    The rectangle is emitted by finalize() once every part is placed, so adding
    a component can never silently overflow the box.
    """
    ALL = []

    # A passive row wider than this reads as a queue rather than a group. Five
    # keeps every block's passives inside one glance; the earlier code derived
    # the count from the block WIDTH, so a wide column strung all thirteen MCU
    # support parts out in a single line 300 mm long.
    MAX_COLS = 5

    def __init__(self, title, x0, y0, cols=MAX_COLS):
        self.title, self.x0, self.y0 = title, x0, y0
        self.cols = max(1, cols)
        self.step_x, self.step_y = 11 * G, 11 * G
        self.cx, self.cy = snap(x0 + 16), snap(y0 + 26)
        self.n = 0
        self.maxy = y0 + 26
        # Width is content-driven like the height. A fixed x1 leaves a box
        # several times wider than what is in it, which is what made the first
        # A1 attempt unreadable.
        self.maxx = x0 + 40
        Block.ALL.append(self)

    def next_pos(self):
        p = (self.cx + (self.n % self.cols) * self.step_x,
             self.cy + (self.n // self.cols) * self.step_y)
        self.n += 1
        self.maxy = max(self.maxy, p[1])
        self.maxx = max(self.maxx, p[0])
        return p

    @property
    def x1(self):
        return snap(self.maxx + 22)

    def note(self, y):
        self.maxy = max(self.maxy, y)

    def note_symbol(self, x, y, defn, stub=5.08):
        """Record an explicitly placed symbol's full extent, stubs included.

        Grid-placed parts size the block through next_pos(); anything placed
        with an explicit coordinate has to report itself or the box closes
        across it. U1 is 60 mm of pins and would otherwise sit half outside.
        """
        pl = pins_of(defn)
        if not pl:
            return
        xs = [p[3] for p in pl]
        ys = [p[4] for p in pl]
        self.maxx = max(self.maxx, x + max(xs) + stub + 12)
        self.maxy = max(self.maxy, y - min(ys) + stub)
        self.miny_hint = min(getattr(self, 'miny_hint', y), y - max(ys) - stub)

    def at(self, dx, dy):
        """Absolute sheet coordinate from a block-relative offset.

        Positions are declared relative to the block that owns them, so moving
        a block moves its contents. Absolute coordinates silently detach when
        a block moves, which is how J1 ended up 300 mm from its own box.
        """
        return (snap(self.x0 + dx), snap(self.y0 + dy))

    def grid_below(self, gap=14.0):
        """Start the auto-placed grid below everything placed so far.

        Derived from the block's recorded extent rather than a hand-picked
        offset: a large IC is placed explicitly, then its passives flow
        underneath it. A constant here goes stale the moment a symbol changes
        size or a block moves, and the failure is a silent stub-end collision
        rather than an error.
        """
        self.cy = snap(self.maxy + gap)

    def add(self, lib, sym, ref, val, netmap, fp="", dnp=False, at=None, rot=0,
            mpn=""):
        pos = at or self.next_pos()
        x, y, d = place(lib, sym, ref, val, pos, fp, dnp, rot, mpn)
        self.note(y)
        seen = set()
        for num, nm, typ, px, py, prot in pins_of(d):
            if num not in netmap or (px, py) in seen:
                continue
            seen.add((px, py))
            wire_pin(x, y, d, num, netmap[num], rot)
        return x, y, d

    def finalize(self):
        y1 = snap(self.maxy + 20)
        graphics.append(
            f'\t(rectangle\n\t\t(start {snap(self.x0)} {snap(self.y0)})\n'
            f'\t\t(end {self.x1} {y1})\n'
            f'\t\t(stroke (width 0.254) (type dash))\n\t\t(fill (type none))\n'
            f'\t\t(uuid "{U()}")\n\t)')
        graphics.append(
            f'\t(text "{esc(self.title)}"\n\t\t(exclude_from_sim yes)\n'
            f'\t\t(at {snap(self.x0 + 3)} {snap(self.y0 + 6)} 0)\n'
            f'\t\t(effects (font (size 2.2 2.2) (bold yes)) (justify left))\n'
            f'\t\t(uuid "{U()}")\n\t)')
        return y1

# =============================================================== PLACEMENT ===
# A1 = 841 x 594 mm. Three columns x three bands, read in the normal order:
# left to right, then down.
#
# THE BLOCK ORDER IS THE BOARD ORDER. Reading the sheet walks the PCB from the
# antenna end to the probe tip:
#
#   board y   block                        sheet slot
#   -------   ---------------------------  ----------
#    12-17    RF MATCH + ANTENNA           band 1, col A
#    17-30    MCU - nRF54L15               band 1, col B
#    17-30    MCU SUPPORT                  band 1, col C   (sits against the MCU)
#    17-30    CLOCKS                       band 2, col A   (X1/X2 flank the MCU)
#    33-36    SWD                          band 2, col B
#    41-64    PMIC - nPM1300               band 2, col C
#    41-64    USB-C + SOLAR INPUT          band 3, col A
#    41-64    BATTERY + CHARGE STATUS      band 3, col B
#    63-73    SENSE FRONT END              band 3, col C
#
# The board is 42 x 155 mm - a vertical strip. Reproducing that proportion on a
# sheet would give an unreadable column, so what is preserved is the ORDER and
# the adjacency, not the aspect ratio. A part that neighbours another on the
# board neighbours it here.
#
# A2 does not fit this: the three bands need 448 mm of the 420 mm A2 height.

COL_A, COL_A_END = 18, 290
COL_B, COL_B_END = 298, 570
COL_C, COL_C_END = 578, 830

BAND_1, BAND_2, BAND_3 = 20, 172, 348

# The RF chain is a signal path, so it stays one row: ANT -> L2 -> L3 -> L4 ->
# ANT_FEED reads as the chain it is. Everything else groups into a rectangle.
B_RF    = Block("RF MATCH + ANTENNA",                          COL_A, BAND_1, cols=7)
B_MCU   = Block("MCU - nRF54L15-QFAA",                         COL_B, BAND_1)
B_SUP   = Block("MCU SUPPORT (Nordic ref cfg 1)",              COL_C, BAND_1)
B_XTAL  = Block("CLOCKS",                                      COL_A, BAND_2, cols=2)
B_SWD   = Block("SWD",                                         COL_B, BAND_2, cols=2)
B_PMIC  = Block("PMIC - nPM1300 (charger / power path / ADC)", COL_C, BAND_2)
B_USB   = Block("USB-C + SOLAR INPUT",                         COL_A, BAND_3)
B_BATT  = Block("BATTERY + CHARGE STATUS",                     COL_B, BAND_3, cols=3)
B_SENSE = Block("SENSE FRONT END - FDC1004",                   COL_C, BAND_3)

# ---- USB-C + solar -----------------------------------------------------------
# Solar is fitted on every board. It was briefly DNP-by-default on the theory
# that most units ship without a panel, but the parts are three cheap passives
# and an LDO in the space that was already reserved for them, and a board that
# ships populated can be upgraded by plugging a panel in rather than by
# reworking. J3, D5, U5, C30 and C31 are all populated.
SOLAR_DNP = False

_x, _y, USBD = place("Connector", "USB_C_Receptacle", "J1", "USB-C receptacle",
                     B_USB.at(16, 32), "", mpn="TYPE-C-31-M-12")
for num, nm, typ, px, py, rot in pins_of(USBD):
    n = nm.upper()
    net = ("VBUS_IN" if n.startswith("VBUS")
           else "GND" if n.startswith("GND") or n.startswith("SHIELD")
           else "USB_CC1" if n == "CC1" else "USB_CC2" if n == "CC2"
           else None)
    wire_pin(_x, _y, USBD, num, net)
B_USB.note_symbol(_x, _y, USBD)
# CC1/CC2 go straight to the PMIC - it has internal 5.1k Rd pulldowns (sec 6.1.3).
# Do NOT fit the usual discrete 5.1k pair.
B_USB.grid_below()
B_USB.add("Device", "C_Small", "C20", "1uF/10V X5R", {"1": "VBUS_IN", "2": "GND"})
# Solar -> 5 V pre-regulator -> D5 -> VBUS. Pin 1 = K, pin 2 = A.
B_USB.add("Device", "D_Schottky_Small", "D5", "RB751V-40 Schottky",
          {"1": "VBUS_IN", "2": "SOLAR_5V"}, dnp=SOLAR_DNP,
          mpn="RB751V-40_R1_00001")
# J3 stays a JST GH. The barrel jack the user plugs into lives on the panel
# pigtail, not on the board: a 5.5 x 2.1 mm jack is 11.0 mm tall (CUI PJ-102AH)
# against 6.90 mm of clearance under the cell here, so putting it on the board
# would have forced the whole solar block into the y 62-74 end band.
B_USB.add("Connector_Generic", "Conn_01x02", "J3", "Solar panel",
          {"1": "SOLAR_PANEL", "2": "GND"}, dnp=SOLAR_DNP)
# C30 is rated for whatever gets plugged into the barrel jack, not for the
# panel. The Voltaic P126 is 9.2 V at its cold open-circuit worst case, but a
# user-accessible DC jack is an unqualified input, and U5 itself is good to
# 60 V. A 50 V input cap moves the ceiling off the capacitor and onto U5's
# thermal limit (~19 V at the 100 mA VBUS current limit).
# TI SBVS171F section 8.2.1.2.1.3: C_IN >= 0.1 uF required, 10 uF recommended;
# C_OUT >= 2.2 uF required, 10 uF recommended. C30 uses 0805 to improve
# effective capacitance, availability and voltage margin over a 50 V 0603.
B_USB.add("Device", "C_Small", "C30", "4.7uF/50V X7R 0805",
          {"1": "SOLAR_PANEL", "2": "GND"}, dnp=SOLAR_DNP,
          mpn="GRM21BR61H475KA12L")
B_USB.add("Device", "C_Small", "C31", "10uF/25V X5R",
          {"1": "SOLAR_5V", "2": "GND"}, dnp=SOLAR_DNP,
          mpn="CL10A106MA8NRNC")

# U5 - solar 5 V pre-regulator. Placed explicitly rather than through the block
# grid: the symbol is 40 mm wide and would overrun a grid cell.
#
# LDO, not the buck. With the Voltaic P126 the TPS62122 does now clear the
# 1.5x V_IN rule (1.5 x 9.23 V = 13.9 V against 15 V operating), so this is a
# judgement call rather than a disqualification. It stays an LDO because the
# thing on the other end of that cable is a barrel jack: 17 V of headroom is
# thin against whatever adapter someone finds in a drawer, and the buck's ~1.3x
# harvest advantage buys nothing when the panel already makes 1700-35000x the
# board's average load. See HARDWARE.md section 4.
u5_x, u5_y, LDOD = place("tps7a16", "TPS7A1650", "U5", "TPS7A1650 5V LDO",
                         B_USB.at(22, 142), dnp=SOLAR_DNP)
for _n, _net in {
    "8": "SOLAR_PANEL",    # IN
    # EN tied to IN. SBVS171F Pin Functions: "If not used, the EN pin can be
    # connected to IN. Make sure that VEN <= VIN at all times" - tying them
    # together satisfies that identically, and EN-to-IN abs max is -62/+0.3 V.
    "5": "SOLAR_PANEL",
    "1": "SOLAR_5V",       # OUT
    "4": "GND",
    "9": "GND",            # PowerPAD - "TI highly recommends connecting to GND"
    # Pin 2 is FB/DNC. On the FIXED-output versions the datasheet is explicit:
    # "Do not connect to this pin. Do not route this pin to any electrical net,
    # not even GND or IN." So this is a real no-connect, not a convenience one.
    "2": None,
    "3": None,             # PG open-drain, unused -> leave open
    "6": None,             # NC
    "7": None,             # DELAY, no reset function needed -> leave open
}.items():
    wire_pin(u5_x, u5_y, LDOD, _n, _net)
B_USB.note_symbol(u5_x, u5_y, LDOD)

# ---- PMIC --------------------------------------------------------------------
npm_x, npm_y, NPMD = place("npm1300", "NPM1300-QEAA-R7", "U2", "nPM1300-QEAA",
                           B_PMIC.at(38, 26), "footprints:QFN32_5X5_NOR")
for n, net in {
    "1": None, "2": "GND", "3": None, "4": "VSYS", "5": "SW2",
    # Pin 6 is PVSS2, the BUCK2 POWER ground - not a general ground pin.
    # Nordic's reference schematic annotates it "Net tie" and "Via to
    # GND-layer", i.e. it reaches the plane at one controlled point rather
    # than merging into the top-layer pour. Split out and tied by NT3.
    # PVSS1 (pin 2) stays on GND: BUCK1 is disabled, so it carries nothing.
    "6": "GND_PVSS2", "7": None, "8": "PMIC_INT", "9": None,
    "10": None, "11": None, "12": "+3V3", "13": "SDA",
    "14": "SCL", "15": "SHPHLD", "16": "VSET2", "17": "VSET1", "18": "NTC",
    "19": "VBAT", "20": "VSYS", "21": "VBUS_IN", "22": None,
    "23": "USB_CC1", "24": "USB_CC2", "25": "LED0_K", "26": "LED1_K",
    "27": None, "28": "+3V3", "29": "FDC_VDD", "30": None,
    "31": None, "32": "+3V3", "33": "GND",
}.items():
    wire_pin(npm_x, npm_y, NPMD, n, net)
B_PMIC.note_symbol(npm_x, npm_y, NPMD)

B_PMIC.grid_below()

# BUCK2, drawn as the loop it is: SW2 -> L10 -> VOUT2(+3V3), with C24 returning
# to PVSS2 rather than to the plane. That return is the whole point - it closes
# the high-di/dt path locally instead of through the ground pour - and it is
# invisible when C24 is one more capacitor in a grid with a "GND_PVSS2" label
# on its lower pin.
#
# The audit measured this loop at 5.50 mm2 on the board, with L10 turned around
# so the switch node runs 4.69 mm instead of 3.62 mm. See docs/audit-2026-07-31.md.
chain(B_PMIC, B_PMIC.at(126, 34), "SW2", [
    # No MPN field: L10 is still specified by constraint rather than selected,
    # so the saturation current stays in Value where a reader sees it. Putting
    # "Isat>350mA DCR<400m" in MPN would hand the BOM a part number that does
    # not exist. See BOM.md.
    ("series", "L10", "L_Small", "2.2uH Isat>350mA", "+3V3"),
    ("shunt",  "C24", "C_Small", "10uF/25V X5R",              "GND_PVSS2"),
])

for ref, sym, val, nm in [
    ("C21", "C_Small", "10uF/25V X5R", {"1": "VSYS", "2": "GND"}),
    ("C22", "C_Small", "10uF/25V X5R", {"1": "VSYS", "2": "GND"}),
    ("C23", "C_Small", "2.2uF/16V X7R", {"1": "VBAT", "2": "GND"}),
    ("C25", "C_Small", "100nF X5R", {"1": "+3V3", "2": "GND"}),
    ("R20", "R_Small", "470k 1% VSET2=3.3V", {"1": "VSET2", "2": "GND"}),
    ("R21", "R_Small", "0R disables BUCK1", {"1": "VSET1", "2": "GND"}),
]:
    B_PMIC.add("Device", sym, ref, val, nm)

# ---- MCU ---------------------------------------------------------------------
nrf_x, nrf_y, NRFD = place("nordic", "NRF54L15-QFAA-R", "U1", "nRF54L15-QFAA",
                           B_MCU.at(90, 40), "footprints:QFN48_6X6_NOR")
for n, net in {
    "1": "XL1", "2": "XL2", "3": None, "4": None, "5": None,
    "6": None, "7": None, "8": None, "9": None,
    "10": "+3V3", "11": None, "12": None, "13": None,
    "14": None, "15": None, "16": None, "17": None,
    "18": "P2.07_SWO", "19": None, "20": None, "21": None,
    "22": "+3V3", "23": "PMIC_INT", "24": None, "25": "SWDIO",
    "26": "SWDCLK", "27": None, "28": None, "29": None,
    # Pin 32 is VSS_PA and sits on GND_PA, not GND. It reaches the centre pad
    # only underneath the package - see the RF block.
    "30": "NRESET", "31": "ANT", "32": "GND_PA", "33": "DECA", "34": "XC1",
    "35": "XC2", "36": "+3V3", "37": None, "38": "SDA",
    "39": "SCL", "40": None, "41": None,
    "42": None, "43": "DECA", "44": "GND", "45": "DECD",
    "46": "DCC", "47": "+3V3", "48": "+3V3", "49": "GND",
}.items():
    wire_pin(nrf_x, nrf_y, NRFD, n, net)
B_MCU.note_symbol(nrf_x, nrf_y, NRFD)

# ---- MCU support -------------------------------------------------------------
# Topology is Nordic QFAA reference layout 0.8, NOT a generic decoupling
# scheme. The DC/DC output goes DCC -> L1 -> DECD, then DECD -> FB1 -> DECA,
# and DECA is the same net as DECRF. VDD is fed directly from the rail with no
# ferrite in the supply path.
# The DC/DC chain, drawn in the order the current flows:
#   DCC -> L1 -> DECD -> FB1 -> DECA(=DECRF)
# with C1 on DECD and C2/C12/C5 on DECA. This is the part of the sheet that
# most needed drawing rather than labelling: DECA and DECRF being the same net
# is unusual enough that it reads as a mistake, and three capacitors sitting in
# a grid each carrying a "DECA" label gives a reader no way to see that they
# are the DECA bank. Nordic's own reference draws it exactly this way.
#
# TDK MLZ1608M4R7WT000 for L1, not the Murata LQM18PN4R7M. The Murata publishes
# no saturation current at all - only a 620 mA temperature-rise rating - and
# saturation is the parameter that matters in a buck. The TDK publishes both
# (Isat 120 mA at 50 % L drop, Itemp 350 mA typ). See BOM.md.
chain(B_SUP, B_SUP.at(34, 30), "DCC", [
    ("series", "L1",  "L_Small", "4.7uH",          "DECD", "MLZ1608M4R7WT000"),
    ("shunt",  "C1",  "C_Small", "2.2uF/2.5V X6T", "GND"),
    ("series", "FB1", "L_Small", "FB 120R@100MHz", "DECA", "MMZ1005S121CT000"),
    ("shunt",  "C2",  "C_Small", "2.2uF/2.5V X6T", "GND"),
    ("shunt",  "C12", "C_Small", "10nF/6.3V X7R",  "GND"),
    ("shunt",  "C5",  "C_Small", "2.2nF X7R",      "GND"),
])
B_SUP.grid_below()

# The VDD bypass bank and the reset network. These are genuinely parallel parts
# on one rail, so a row is the honest drawing - there is no order to show.
for ref, sym, val, nm in [
    ("C3",  "C_Small", "10uF/6.3V X6S 0402",{"1": "+3V3", "2": "GND"}),
    ("C4",  "C_Small", "100nF X7R",         {"1": "+3V3", "2": "GND"}),
    ("C7",  "C_Small", "100nF X7R",         {"1": "+3V3", "2": "GND"}),
    ("C8",  "C_Small", "100nF X7R",         {"1": "+3V3", "2": "GND"}),
    ("C10", "C_Small", "100nF X7R",         {"1": "+3V3", "2": "GND"}),
    ("R1",  "R_Small", "1k 1%",             {"1": "NRESET", "2": "SWD_RST"}),
    ("C13", "C_Small", "3.9pF C0G",         {"1": "NRESET", "2": "GND"}),
]:
    B_SUP.add("Device", sym, ref, val, nm)

# ---- battery + charge status -------------------------------------------------
# 2-pin JST PH so an Adafruit cell plugs straight in - their whole range ships
# with a PH plug. That drops the pack-NTC pin, which costs nothing here: the
# Adafruit cells are 2-wire and have no thermistor (HARDWARE.md section 3), so
# the NTC path was always going to be TH1.
#
# PH is 8 mm tall against 6.90 mm of clearance under the cell, so J2 MUST sit
# outside the cell footprint. The cell is only 36 mm of the 74 mm board, leaving
# the y 62-74 band at full 11.70 mm height - that is where J2 goes.
B_BATT.add("Connector_Generic", "Conn_01x02", "J2", "Battery - Adafruit 1578",
           {"1": "VBAT", "2": "GND"})
# The pack has no thermistor, so TH1 is fitted, not DNP. Couple it to the cell
# body - a board-mounted NTC measures board temperature and partly defeats
# JEITA. A leaded NTC taped to the cell and soldered to these pads is better
# than the 0603 land.
B_BATT.add("Device", "Thermistor_NTC", "TH1", "10k B3435 - couple to cell",
           {"1": "NTC", "2": "GND"}, mpn="103JT-025")
# LEDs sink into the PMIC drivers, fed from VSYS. Pin 1 = K, pin 2 = A.
B_BATT.add("Device", "R_Small", "R25", "1k", {"1": "VSYS", "2": "LED0_A"})
B_BATT.add("Device", "LED_Small", "D3", "GREEN", {"1": "LED0_K", "2": "LED0_A"},
           mpn="LTST-C190KGKT")
B_BATT.add("Device", "R_Small", "R26", "1k", {"1": "VSYS", "2": "LED1_A"})
B_BATT.add("Device", "LED_Small", "D4", "RED", {"1": "LED1_K", "2": "LED1_A"},
           mpn="LTST-C190KRKT")

# ---- sense front end ---------------------------------------------------------
# Pinout per TI SNOSCY5 Table 4-1. CIN3/CIN4 unused -> datasheet says leave open.
fd_x, fd_y, FDCD = place("fdc", "FDC1004", "U3", "FDC1004",
                         B_SENSE.at(30, 26), "Package_SO:MSOP-10_3x3mm_P0.5mm")
for n, net in {"1": "SHLD", "2": "SENSE1", "3": "SENSE2", "4": None,
               "5": None, "6": "SHLD", "7": "GND", "8": "FDC_VDD",
               "9": "SCL", "10": "SDA"}.items():
    wire_pin(fd_x, fd_y, FDCD, n, net)
B_SENSE.note_symbol(fd_x, fd_y, FDCD)
B_SENSE.grid_below()
B_SENSE.add("Device", "C_Small", "C26", "1uF/10V X7R", {"1": "FDC_VDD", "2": "GND"})
# TWI pull-ups sit on the ALWAYS-ON +3V3 rail, NOT on the switched FDC_VDD.
# Putting them on FDC_VDD deadlocks the board: LOADSW1 is commanded over TWI, so
# with the switch off there are no pull-ups, the bus cannot go high, the PMIC is
# unreachable and the switch can never be turned on.
# Safe because FDC1004 SCL/SDA are rated to 6 V INDEPENDENT of VDD (sec 5.1),
# i.e. there is no ESD diode from those pins to VDD, so holding them at 3.3 V
# while the part is unpowered does not back-power it.
B_SENSE.add("Device", "R_Small", "R22", "4.7k to +3V3", {"1": "+3V3", "2": "SDA"})
B_SENSE.add("Device", "R_Small", "R23", "4.7k to +3V3", {"1": "+3V3", "2": "SCL"})
# SHT45-AD1F ambient RH/T. Sits on the ALWAYS-ON +3V3, never on the gated
# FDC_VDD: Table 6 rates every pin at VSS-0.3 .. VDD+0.3 with no independent I/O
# rating, so an unpowered SHT4x with the bus pull-ups high would violate abs max
# on every sleep cycle. Idle is 80 nA typ, about 0.7 mAh/yr - cheaper than the
# level shifting the alternative would need.
sht_x, sht_y, SHTD = place("sht4x", "SHT4x", "U4", "SHT45-AD1F",
                           B_SENSE.at(110, 26),
                           "Sensor_Humidity:Sensirion_DFN-4_1.5x1.5mm_P0.8mm_SHT4x_NoCentralPad")
for n, net in {"1": "SDA", "2": "SCL", "3": "+3V3", "4": "GND"}.items():
    wire_pin(sht_x, sht_y, SHTD, n, net)
B_SENSE.note_symbol(sht_x, sht_y, SHTD)
B_SENSE.add("Device", "C_Small", "C27", "100nF X7R", {"1": "+3V3", "2": "GND"})

for ref, net in [("TP1", "SENSE1"), ("TP2", "SENSE2"), ("TP3", "SHLD")]:
    B_SENSE.add("Connector", "TestPoint", ref, net, {"1": net})

# ---- SWD ---------------------------------------------------------------------
B_SWD.add("Connector_Generic", "Conn_02x05_Odd_Even", "J4", "SWD 10p 1.27mm",
          {"1": "+3V3", "2": "SWDIO", "3": "GND", "4": "SWDCLK", "5": "GND",
           "6": "P2.07_SWO", "7": None, "8": None, "9": "GND",
           "10": "SWD_RST"}, at=B_SWD.at(52, 30))

# ---- clocks ------------------------------------------------------------------
# No discrete load caps: both oscillators use the nRF54L15 internal trim banks.
B_XTAL.add("Device", "Crystal_Small", "X1", "CM8V-T1A 32.768kHz CL=7pF 20ppm",
           {"1": "XL1", "2": "XL2"})
B_XTAL.add("Device", "Crystal_GND24_Small", "X2", "FA-128 32MHz CL=8pF",
           {"1": "XC1", "3": "XC2", "2": "GND"})

# ---- RF ----------------------------------------------------------------------
# GND_PA and GND_C9 are DELIBERATELY separate nets. Nordic requires C6 to ground
# only at pin 32 (VSS_PA) on the top layer, with pin 32 reaching pin 49 only
# underneath the package, and C9 to ground only on the bottom ground layer.
# Electrically these are all the same node; the isolation is a LAYOUT rule, and
# it is invisible in a netlist. The net ties below make the DRC police it instead
# of a comment in a markdown file. Do not merge them into GND.
# Drawn as the chain it is, not as six parts each carrying two labels. Compare
# Nordic's reference sheet: ANT -> L2 -> L3 -> L4 -> ANT_FEED along one line,
# with C6, C9 and C11 hanging off the nodes between them. The ORDER of a
# matching network is the design; a netlist has it but a reader cannot see it.
chain(B_RF, B_RF.at(34, 30), "ANT", [
    ("series", "L2",  "L_Small", "2.7nH", "RF_A",     "LQP03HQ2N7B02"),
    ("shunt",  "C6",  "C_Small", "1.5pF", "GND_PA",   "GJM0335C1E1R5WB01"),
    ("series", "L3",  "L_Small", "3.5nH", "RF_B",     "LQP03HQ3N5B02"),
    ("shunt",  "C9",  "C_Small", "2.0pF", "GND_C9",   "GJM0335C1E2R0WB01"),
    ("series", "L4",  "L_Small", "3.5nH", "ANT_FEED", "LQP03HQ3N5B02"),
    ("shunt",  "C11", "C_Small", "0.3pF C0G", "GND", "GRM0335C1ER30BA01D"),
])
B_RF.grid_below()
# The antenna is an external adhesive part on a U.FL pigtail, not PCB copper.
# That makes Nordic's matching values correct rather than a starting point: the
# QFAA reference layout has no PCB antenna either - its chain runs
# ANT -> L2 -> C6 -> L3 -> C9 -> L4 -> C11 and terminates at a board-edge pad for
# a coax or connector launch, which is exactly what this is. See LAYOUT.md.
B_RF.add("Connector", "Conn_Coaxial", "J5", "U.FL-R-SMT-1(10) antenna",
         {"1": "ANT_FEED", "2": "GND"})

# NT1 joins GND_PA to GND. Place it UNDER the U1 centre pad on F.Cu, so the only
# path from pin 32 to pin 49 is the one Nordic specifies.
# NT2 joins GND_C9 to GND. Place it on B.Cu, so C9's only route to ground is a
# via down to the bottom layer.
B_RF.add("Device", "NetTie_2", "NT1", "GND_PA to GND (under U1, F.Cu)",
         {"1": "GND_PA", "2": "GND"})
B_RF.add("Device", "NetTie_2", "NT2", "GND_C9 to GND (B.Cu only)",
         {"1": "GND_C9", "2": "GND"})

# NT3 joins the BUCK2 power ground to the plane. Place it at the via that
# drops PVSS2 to the ground layer, right at U2 pin 6 - see LAYOUT.md.
B_PMIC.add("Device", "NetTie_2", "NT3", "GND_PVSS2 to GND (at the via)",
           {"1": "GND_PVSS2", "2": "GND"})

# ---- net drivers -------------------------------------------------------------
# A PWR_FLAG lives in the block that owns its net, rather than in one anonymous
# pile. Each of these nets is driven only by connector or passive pins, so ERC
# needs the flag to treat it as powered.
# GND_PA needs one because U1 pin 32 (VSS_PA) is a power INPUT and splitting it
# off GND left it with nothing but passive pins to drive it. GND_C9 does not -
# it carries only C9 pin 2 and the net tie, both passive. GND_PVSS2 needs one
# for the same reason as GND_PA: U2 pin 6 is a power input.
# SOLAR_5V no longer needs a flag: U5 pin 1 is a power OUTPUT and drives it.
# Leaving the flag in place would put two power outputs on one net, which ERC
# reports as a conflict.
for blk, net in [(B_USB, "VBUS_IN"), (B_USB, "SOLAR_PANEL"),
                 (B_BATT, "VBAT"), (B_PMIC, "GND"), (B_PMIC, "VSYS"),
                 (B_SUP, "SWD_RST"), (B_RF, "GND_PA"),
                 (B_PMIC, "GND_PVSS2")]:
    blk.add("power", "PWR_FLAG", f"#FLG_{net.strip('+')}", "PWR_FLAG", {"1": net})
B_PMIC.add("Connector", "TestPoint", "TP4", "SHPHLD", {"1": "SHPHLD"})
B_USB.add("Connector", "TestPoint", "TP5", "SOLAR_5V", {"1": "SOLAR_5V"})

# ---- size every block to its contents, then check the columns do not collide
_col = {}
for _b in Block.ALL:
    _y1 = _b.finalize()
    print("  block %-34s x %3d..%-3d  y %5.1f..%-5.1f  (h %5.1f)"
          % (_b.title, _b.x0, _b.x1, _b.y0, _y1, _y1 - _b.y0))
    _col.setdefault(_b.x0, []).append((_b.y0, _y1, _b.title))
for _x0, _spans in _col.items():
    _spans.sort()
    for (_a0, _a1, _at), (_b0, _b1, _bt) in zip(_spans, _spans[1:]):
        if _a1 >= _b0:
            raise SystemExit(
                f"ABORT: block '{_at}' (ends y{_a1}) overlaps '{_bt}' (starts y{_b0})")

# Boxes size themselves to their contents in x as well as y now, so a block can
# grow sideways into its neighbour. That is invisible in the netlist and only
# shows up as two dashed rectangles crossing, so check it here.
for _a in Block.ALL:
    for _b in Block.ALL:
        if _a is _b or _a.x0 >= _b.x0:
            continue
        if _a.x1 > _b.x0 and not (_a.maxy + 20 < _b.y0 or _b.maxy + 20 < _a.y0):
            raise SystemExit(
                f"ABORT: block '{_a.title}' (ends x{_a.x1}) overlaps "
                f"'{_b.title}' (starts x{_b.x0}) and they share rows")

_sheet_w, _sheet_h = 841, 594
_over = [(b.title, b.x1, snap(b.maxy + 20)) for b in Block.ALL
         if b.x1 > _sheet_w - 8 or b.maxy + 20 > _sheet_h - 8]
if _over:
    raise SystemExit("ABORT: block runs off the A1 sheet: %s" % _over)
print("layout: blocks sized, no overlap, all inside A1")

# ---------------------------------------------------------------- self-check
import collections as _c
_end, _pinpt = _c.defaultdict(set), _c.defaultdict(set)
for _a, _b, _n in conn:
    _pinpt[(round(_a[0], 3), round(_a[1], 3))].add(_n)
    _end[(round(_b[0], 3), round(_b[1], 3))].add(_n)
_fail = False
for tag, d in (("STUB-END", _end), ("PIN", _pinpt)):
    for k, v in d.items():
        if len(v) > 1:
            print(f"  !! {tag} COLLISION at {k}: {sorted(v)}"); _fail = True
for pt in set(_end) & set(_pinpt):
    if _end[pt] != _pinpt[pt]:
        print(f"  !! STUB-END on foreign PIN at {pt}: {sorted(_end[pt])} vs {sorted(_pinpt[pt])}")
        _fail = True
_ncpts = {_re2.search(r'\(at ([-\d.]+) ([-\d.]+)\)', _s).groups() for _s in nocons}
_ncpts = {(round(float(a), 3), round(float(b), 3)) for a, b in _ncpts}
_clash = _ncpts & set(_pinpt)
if _clash:
    print(f"  !! NO-CONNECT on a wired pin: {sorted(_clash)}"); _fail = True
if _fail:
    raise SystemExit("ABORT: net collisions detected")
print(f"self-check: ok  ({len(conn)} wired pins, {len(nocons)} no-connects)")

# =============================================================== EMIT FILE ===
def emit_lib_symbol(lib_id, defn):
    """Top-level entry is keyed by the FULL lib_id ("Device:C_Small"); sub-unit
    symbols inside keep bare names ("C_Small_0_1"). Get this wrong and KiCad
    cannot bind instance pins to library pins."""
    lib, name = lib_id.split(":", 1)
    lines = defn.split("\n")
    base = len(lines[0]) - len(lines[0].lstrip("\t"))
    out = [("\t\t" + (ln[base:] if ln[:base] == "\t" * base else ln.lstrip("\t")))
           if ln.strip() else "" for ln in lines]
    return "\n".join(out).rstrip().replace(
        f'(symbol "{name}"', f'(symbol "{lib}:{name}"', 1)

doc = f'''(kicad_sch
\t(version 20260306)
\t(generator "eeschema")
\t(generator_version "10.0")
\t(uuid "{ROOT_UUID}")
\t(paper "A1")
\t(title_block
\t\t(title "Indoor Capacitive Soil Moisture Sensor")
\t\t(date "2026-07-31")
\t\t(rev "C")
\t\t(comment 1 "nRF54L15-QFAA + nPM1300-QEAA + FDC1004 - BTHome v2 over BLE")
\t\t(comment 2 "Block order is board order: antenna end top-left to probe tip bottom-right")
\t\t(comment 3 "Rails are power symbols; labels are signals. Generated by tools_gen_sch.py")
\t\t(comment 4 "See HARDWARE.md for rationale, LAYOUT.md for the zone map")
\t)
\t(lib_symbols
{chr(10).join(emit_lib_symbol(k, used_lib[k]) for k in sorted(used_lib))}
\t)
{chr(10).join(graphics)}
{chr(10).join(wires)}
{chr(10).join(nocons)}
{chr(10).join(junctions)}
{chr(10).join(labels)}
{chr(10).join(parts)}
\t(sheet_instances
\t\t(path "/" (page "1"))
\t)
\t(embedded_fonts no)
)
'''
out = f"{PROJ}/moisture-sensor-carrier.kicad_sch"
open(out, "w").write(doc)
print(f"wrote {out}")
print(f"  symbols {len(parts)}   stubs {len(wires)}   blocks {len(graphics)//2}   lib_symbols {len(used_lib)}")
