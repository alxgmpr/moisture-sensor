#!/usr/bin/env python3
"""Generate the moisture-sensor-carrier schematic (nRF54L15 + nPM1300 + FDC1004).

Layout is organised into labelled functional blocks, each drawn with a dashed
box, so passives belonging to different subsystems do not get mixed up.

Connectivity is expressed with global labels on short wire stubs off each pin.
That yields a correct netlist without full wire-routing geometry; positions can
be tidied in Eeschema afterwards.

Run:  python3 tools_gen_sch.py
"""
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
    "TH1": HS_R0603,
    # solar OR-ing
    "D5": "Diode_SMD:D_SOD-323_HandSoldering",
    # clocks. Standard pads on X2 (no hand variant for 2016-4pin exists).
    # Micro Crystal CM8V-T1A. The vendor land pattern (0.8 x 1.5 mm pads on
    # 1.5 mm centres) is what the datasheet specifies; KiCad's generic 2012
    # footprints use 0.6 or 1.05 mm pads on different centres.
    "X1": "footprints:XTAL_CM8V-T1A_2012",
    "X2": "Crystal:Crystal_SMD_2016-4Pin_2.0x1.6mm",
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
    "J5": TP,
    "TP1": TP, "TP2": TP, "TP3": TP, "TP4": TP, "TP5": TP,
    # RF grounding net ties - see the RF block for what they enforce.
    # NT1 is a project footprint: the gap it has to bridge, between U1's pin-32
    # land and the centre pad, is 0.1905 mm, and a stock 0.5 mm net tie does not
    # fit in it.
    "NT1": "footprints:NetTie_VSSPA",
    "NT2": "NetTie:NetTie-2_SMD_Pad0.5mm",
}

# ---------------------------------------------------------------- emit buffers
parts, wires, labels, graphics, nocons = [], [], [], [], []
used_lib = {}
conn = []          # (pin_pt, end_pt, netname) for the collision self-check
pwr_n = [0]

def esc(t):
    return t.replace('\\', '\\\\').replace('"', '\\"')

def place(lib, name, ref, value, at, footprint="", dnp=False):
    footprint = footprint or FOOTPRINTS.get(ref, "")
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
\t\t(at {x} {y} 0)
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
\t\t)
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

def _endpoint(x, y, p, length):
    """Pin anchor and the far end of its stub.

    KiCad pin rotation is the direction the pin extends from its anchor toward
    the symbol body, and schematic Y grows downward:
      0 -> body right, wire leaves -X      180 -> body left, wire leaves +X
      90 -> body up (-Y), wire leaves +Y   270 -> body down, wire leaves -Y
    """
    _, _, _, px, py, rot = p
    ax, ay = x + px, y - py
    if rot == 0:     return (ax, ay), (ax - length, ay), "right", 0
    if rot == 180:   return (ax, ay), (ax + length, ay), "left", 180
    if rot == 90:    return (ax, ay), (ax, ay + length), "right", 0
    return (ax, ay), (ax, ay - length), "left", 180

def _wire(a, b):
    wires.append(f'\t(wire (pts (xy {a[0]} {a[1]}) (xy {b[0]} {b[1]}))\n'
                 f'\t\t(stroke (width 0) (type default))\n\t\t(uuid "{U()}")\n\t)')

def stub(x, y, defn, number, net, length=5.08):
    """Wire stub off `number` carrying a plain (local) net label.

    Single sheet, so local labels are sufficient - global labels would only add
    hierarchy machinery this design does not use.
    """
    p = _pin(defn, number)
    a, b, just, rot = _endpoint(x, y, p, length)
    _wire(a, b)
    labels.append(
        f'\t(label "{esc(net)}"\n\t\t(at {b[0]} {b[1]} {rot})\n'
        f'\t\t(fields_autoplaced yes)\n'
        f'\t\t(effects (font (size 1.27 1.27)) (justify {just} bottom))\n'
        f'\t\t(uuid "{U()}")\n\t)')
    conn.append((a, b, net))

def place_power(sym, at):
    """Place a power symbol (GND, PWR_FLAG). Its pin sits at the origin."""
    defn = SRC["power"][sym]
    used_lib[f"power:{sym}"] = defn
    x, y = at
    pwr_n[0] += 1
    parts.append(f'''\t(symbol
\t\t(lib_id "power:{sym}")
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

def gnd(x, y, defn, number, length=5.08):
    """Stub to a real GND power symbol rather than a text label."""
    p = _pin(defn, number)
    a, b, _, _ = _endpoint(x, y, p, length)
    _wire(a, b)
    place_power("GND", b)
    conn.append((a, b, "GND"))

def nc(x, y, defn, number):
    """No-connect flag directly on an intentionally unused pin."""
    p = _pin(defn, number)
    a, _, _, _ = _endpoint(x, y, p, 0)
    nocons.append(f'\t(no_connect (at {a[0]} {a[1]}) (uuid "{U()}"))')

def wire_pin(x, y, defn, number, net):
    """Dispatch: None -> no-connect, "GND" -> ground symbol, else net label."""
    if net is None:
        nc(x, y, defn, number)
    elif net == "GND":
        gnd(x, y, defn, number)
    else:
        stub(x, y, defn, number, net)

# ------------------------------------------------------------------- blocks
class Block:
    """A titled region that sizes itself to its contents.

    The rectangle is emitted by finalize() once every part is placed, so adding
    a component can never silently overflow the box.
    """
    ALL = []

    def __init__(self, title, x0, y0, x1):
        self.title, self.x0, self.y0, self.x1 = title, x0, y0, x1
        self.cx, self.cy = snap(x0 + 16), snap(y0 + 26)
        self.step_x, self.step_y = 11 * G, 11 * G
        self.cols = max(1, int((x1 - x0 - 26) // self.step_x))
        self.n = 0
        self.maxy = y0 + 26
        Block.ALL.append(self)

    def next_pos(self):
        p = (self.cx + (self.n % self.cols) * self.step_x,
             self.cy + (self.n // self.cols) * self.step_y)
        self.n += 1
        self.maxy = max(self.maxy, p[1])
        return p

    def note(self, y):
        self.maxy = max(self.maxy, y)

    def add(self, lib, sym, ref, val, netmap, fp="", dnp=False, at=None):
        pos = at or self.next_pos()
        x, y, d = place(lib, sym, ref, val, pos, fp, dnp)
        self.note(y)
        seen = set()
        for num, nm, typ, px, py, rot in pins_of(d):
            if num not in netmap or (px, py) in seen:
                continue
            seen.add((px, py))
            wire_pin(x, y, d, num, netmap[num])
        return x, y, d

    def finalize(self):
        y1 = snap(self.maxy + 20)
        graphics.append(
            f'\t(rectangle\n\t\t(start {snap(self.x0)} {snap(self.y0)})\n'
            f'\t\t(end {snap(self.x1)} {y1})\n'
            f'\t\t(stroke (width 0.254) (type dash))\n\t\t(fill (type none))\n'
            f'\t\t(uuid "{U()}")\n\t)')
        graphics.append(
            f'\t(text "{esc(self.title)}"\n\t\t(exclude_from_sim yes)\n'
            f'\t\t(at {snap(self.x0 + 3)} {snap(self.y0 + 6)} 0)\n'
            f'\t\t(effects (font (size 2.2 2.2) (bold yes)) (justify left))\n'
            f'\t\t(uuid "{U()}")\n\t)')
        return y1

# =============================================================== PLACEMENT ===
# A2 = 594 x 420 mm. Three columns x three bands; title block bottom-right.

COL_A, COL_A_END = 18, 150
COL_B, COL_B_END = 158, 345
COL_C, COL_C_END = 353, 578

B_USB   = Block("USB-C + SOLAR INPUT",                        COL_A,  20, COL_A_END)
B_PMIC  = Block("PMIC - nPM1300 (charger / power path / ADC)", COL_B, 20, COL_B_END)
B_MCU   = Block("MCU - nRF54L15-QFAA",                        COL_C,  20, COL_C_END)
B_BATT  = Block("BATTERY + CHARGE STATUS",                    COL_A, 190, COL_A_END)
B_SENSE = Block("SENSE FRONT END - FDC1004",                  COL_B, 190, COL_B_END)
B_SUP   = Block("MCU SUPPORT (Nordic ref cfg 1)",             COL_C, 190, COL_C_END)
B_SWD   = Block("SWD",                                        COL_A, 316, COL_A_END)
B_XTAL  = Block("CLOCKS",                                     COL_B, 316, COL_B_END)
B_RF    = Block("RF MATCH + ANTENNA",                         COL_C, 316, COL_C_END)

# ---- USB-C + solar -----------------------------------------------------------
_x, _y, USBD = place("Connector", "USB_C_Receptacle", "J1", "USB-C receptacle",
                     (34.0, 52.0), "")
for num, nm, typ, px, py, rot in pins_of(USBD):
    n = nm.upper()
    net = ("VBUS_IN" if n.startswith("VBUS")
           else "GND" if n.startswith("GND") or n.startswith("SHIELD")
           else "USB_CC1" if n == "CC1" else "USB_CC2" if n == "CC2"
           else None)
    wire_pin(_x, _y, USBD, num, net)
B_USB.note(_y - min(p[4] for p in pins_of(USBD)))
# CC1/CC2 go straight to the PMIC - it has internal 5.1k Rd pulldowns (sec 6.1.3).
# Do NOT fit the usual discrete 5.1k pair.
B_USB.cy = snap(106.0)
B_USB.add("Device", "C_Small", "C20", "1uF/10V X5R", {"1": "VBUS_IN", "2": "GND"})
# Solar -> 5 V pre-regulator (TBD) -> D5 -> VBUS. Pin 1 = K, pin 2 = A.
B_USB.add("Device", "D_Schottky_Small", "D5", "RB751V-40 Schottky",
          {"1": "VBUS_IN", "2": "SOLAR_5V"})
B_USB.add("Connector_Generic", "Conn_01x02", "J3", "Solar panel",
          {"1": "SOLAR_PANEL", "2": "GND"})

# ---- PMIC --------------------------------------------------------------------
npm_x, npm_y, NPMD = place("npm1300", "NPM1300-QEAA-R7", "U2", "nPM1300-QEAA",
                           (196.0, 46.0), "footprints:QFN32_5X5_NOR")
for n, net in {
    "1": None, "2": "GND", "3": None, "4": "VSYS", "5": "SW2",
    "6": "GND", "7": None, "8": "PMIC_INT", "9": None,
    "10": None, "11": None, "12": "+3V3", "13": "SDA",
    "14": "SCL", "15": "SHPHLD", "16": "VSET2", "17": "VSET1", "18": "NTC",
    "19": "VBAT", "20": "VSYS", "21": "VBUS_IN", "22": None,
    "23": "USB_CC1", "24": "USB_CC2", "25": "LED0_K", "26": "LED1_K",
    "27": None, "28": "+3V3", "29": "FDC_VDD", "30": None,
    "31": None, "32": "+3V3", "33": "GND",
}.items():
    wire_pin(npm_x, npm_y, NPMD, n, net)
B_PMIC.note(npm_y - min(p[4] for p in pins_of(NPMD)))

B_PMIC.cy = snap(106.0)
for ref, sym, val, nm in [
    ("C21", "C_Small", "10uF/25V X5R", {"1": "VSYS", "2": "GND"}),
    ("C22", "C_Small", "10uF/25V X5R", {"1": "VSYS", "2": "GND"}),
    ("C23", "C_Small", "2.2uF/16V X7R", {"1": "VBAT", "2": "GND"}),
    ("C24", "C_Small", "10uF/25V X5R", {"1": "+3V3", "2": "GND"}),
    ("C25", "C_Small", "100nF X5R", {"1": "+3V3", "2": "GND"}),
    ("L10", "L_Small", "2.2uH Isat>350mA DCR<400m", {"1": "SW2", "2": "+3V3"}),
    ("R20", "R_Small", "470k 1% VSET2=3.3V", {"1": "VSET2", "2": "GND"}),
    ("R21", "R_Small", "0R disables BUCK1", {"1": "VSET1", "2": "GND"}),
]:
    B_PMIC.add("Device", sym, ref, val, nm)

# ---- MCU ---------------------------------------------------------------------
nrf_x, nrf_y, NRFD = place("nordic", "NRF54L15-QFAA-R", "U1", "nRF54L15-QFAA",
                           (388.0, 60.0), "footprints:QFN48_6X6_NOR")
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
B_MCU.note(nrf_y - min(p[4] for p in pins_of(NRFD)))

# ---- MCU support -------------------------------------------------------------
# Topology is Nordic QFAA reference layout 0.8, NOT a generic decoupling
# scheme. The DC/DC output goes DCC -> L1 -> DECD, then DECD -> FB1 -> DECA,
# and DECA is the same net as DECRF. VDD is fed directly from the rail with no
# ferrite in the supply path.
for ref, sym, val, nm in [
    ("L1",  "L_Small", "LQM18PN4R7MFRL 4.7uH", {"1": "DCC", "2": "DECD"}),
    ("C1",  "C_Small", "2.2uF/2.5V X6T",    {"1": "DECD", "2": "GND"}),
    ("FB1", "L_Small", "FB 120R@100MHz",    {"1": "DECD", "2": "DECA"}),
    ("C2",  "C_Small", "2.2uF/2.5V X6T",    {"1": "DECA", "2": "GND"}),
    ("C12", "C_Small", "10nF/6.3V X7R",     {"1": "DECA", "2": "GND"}),
    ("C5",  "C_Small", "2.2nF X7R",         {"1": "DECA", "2": "GND"}),
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
           {"1": "NTC", "2": "GND"})
# LEDs sink into the PMIC drivers, fed from VSYS. Pin 1 = K, pin 2 = A.
B_BATT.add("Device", "R_Small", "R25", "1k", {"1": "VSYS", "2": "LED0_A"})
B_BATT.add("Device", "LED_Small", "D3", "GREEN", {"1": "LED0_K", "2": "LED0_A"})
B_BATT.add("Device", "R_Small", "R26", "1k", {"1": "VSYS", "2": "LED1_A"})
B_BATT.add("Device", "LED_Small", "D4", "RED", {"1": "LED1_K", "2": "LED1_A"})

# ---- sense front end ---------------------------------------------------------
# Pinout per TI SNOSCY5 Table 4-1. CIN3/CIN4 unused -> datasheet says leave open.
fd_x, fd_y, FDCD = place("fdc", "FDC1004", "U3", "FDC1004",
                         (188.0, 216.0), "Package_SO:MSOP-10_3x3mm_P0.5mm")
for n, net in {"1": "SHLD", "2": "SENSE1", "3": "SENSE2", "4": None,
               "5": None, "6": "SHLD", "7": "GND", "8": "FDC_VDD",
               "9": "SCL", "10": "SDA"}.items():
    wire_pin(fd_x, fd_y, FDCD, n, net)
B_SENSE.note(fd_y - min(p[4] for p in pins_of(FDCD)))
B_SENSE.cy = snap(258.0)
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
                           (268.0, 216.0),
                           "Sensor_Humidity:Sensirion_DFN-4_1.5x1.5mm_P0.8mm_SHT4x_NoCentralPad")
for n, net in {"1": "SDA", "2": "SCL", "3": "+3V3", "4": "GND"}.items():
    wire_pin(sht_x, sht_y, SHTD, n, net)
B_SENSE.note(sht_y - min(p[4] for p in pins_of(SHTD)))
B_SENSE.add("Device", "C_Small", "C27", "100nF X7R", {"1": "+3V3", "2": "GND"})

for ref, net in [("TP1", "SENSE1"), ("TP2", "SENSE2"), ("TP3", "SHLD")]:
    B_SENSE.add("Connector", "TestPoint", ref, net, {"1": net})

# ---- SWD ---------------------------------------------------------------------
B_SWD.add("Connector_Generic", "Conn_02x05_Odd_Even", "J4", "SWD 10p 1.27mm",
          {"1": "+3V3", "2": "SWDIO", "3": "GND", "4": "SWDCLK", "5": "GND",
           "6": "P2.07_SWO", "7": None, "8": None, "9": "GND",
           "10": "SWD_RST"}, at=(70.0, 346.0))

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
for ref, sym, val, nm in [
    ("L2",  "L_Small", "2.7nH LQP03HQ2N7B02", {"1": "ANT", "2": "RF_A"}),
    ("C6",  "C_Small", "1.5pF GJM0335C1E1R5WB01", {"1": "RF_A", "2": "GND_PA"}),
    ("L3",  "L_Small", "3.5nH LQP03HQ3N5B02", {"1": "RF_A", "2": "RF_B"}),
    ("C9",  "C_Small", "2.0pF GJM0335C1E2R0WB01", {"1": "RF_B", "2": "GND_C9"}),
    ("L4",  "L_Small", "3.5nH LQP03HQ3N5B02", {"1": "RF_B", "2": "ANT_FEED"}),
    ("C11", "C_Small", "0.3pF C0G", {"1": "ANT_FEED", "2": "GND"}),
]:
    B_RF.add("Device", sym, ref, val, nm)
B_RF.add("Connector_Generic", "Conn_01x01", "J5", "Antenna feed", {"1": "ANT_FEED"})

# NT1 joins GND_PA to GND. Place it UNDER the U1 centre pad on F.Cu, so the only
# path from pin 32 to pin 49 is the one Nordic specifies.
# NT2 joins GND_C9 to GND. Place it on B.Cu, so C9's only route to ground is a
# via down to the bottom layer.
B_RF.add("Device", "NetTie_2", "NT1", "GND_PA to GND (under U1, F.Cu)",
         {"1": "GND_PA", "2": "GND"})
B_RF.add("Device", "NetTie_2", "NT2", "GND_C9 to GND (B.Cu only)",
         {"1": "GND_C9", "2": "GND"})

# ---- net drivers -------------------------------------------------------------
# A PWR_FLAG lives in the block that owns its net, rather than in one anonymous
# pile. Each of these nets is driven only by connector or passive pins, so ERC
# needs the flag to treat it as powered.
# GND_PA needs one because U1 pin 32 (VSS_PA) is a power INPUT and splitting it
# off GND left it with nothing but passive pins to drive it. GND_C9 does not -
# it carries only C9 pin 2 and the net tie, both passive.
for blk, net in [(B_USB, "VBUS_IN"), (B_USB, "SOLAR_5V"), (B_USB, "SOLAR_PANEL"),
                 (B_BATT, "VBAT"), (B_PMIC, "GND"), (B_PMIC, "VSYS"),
                 (B_SUP, "SWD_RST"), (B_RF, "GND_PA")]:
    blk.add("power", "PWR_FLAG", f"#FLG_{net.strip('+')}", "PWR_FLAG", {"1": net})
B_PMIC.add("Connector", "TestPoint", "TP4", "SHPHLD", {"1": "SHPHLD"})
B_USB.add("Connector", "TestPoint", "TP5", "SOLAR_5V", {"1": "SOLAR_5V"})

# ---- size every block to its contents, then check the columns do not collide
_col = {}
for _b in Block.ALL:
    _y1 = _b.finalize()
    _col.setdefault(_b.x0, []).append((_b.y0, _y1, _b.title))
for _x0, _spans in _col.items():
    _spans.sort()
    for (_a0, _a1, _at), (_b0, _b1, _bt) in zip(_spans, _spans[1:]):
        if _a1 >= _b0:
            raise SystemExit(
                f"ABORT: block '{_at}' (ends {_a1}) overlaps '{_bt}' (starts {_b0})")
print("layout: blocks sized, no column overlap")

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
\t(paper "A2")
\t(title_block
\t\t(title "Indoor Capacitive Soil Moisture Sensor")
\t\t(date "2026-07-30")
\t\t(rev "B")
\t\t(comment 1 "nRF54L15-QFAA + nPM1300-QEAA + FDC1004 - BTHome v2 over BLE")
\t\t(comment 2 "Connectivity by global label. Generated by tools_gen_sch.py")
\t\t(comment 3 "See HARDWARE.md for rationale and datasheet citations")
\t)
\t(lib_symbols
{chr(10).join(emit_lib_symbol(k, used_lib[k]) for k in sorted(used_lib))}
\t)
{chr(10).join(graphics)}
{chr(10).join(wires)}
{chr(10).join(nocons)}
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
