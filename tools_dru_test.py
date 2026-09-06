#!/usr/bin/env python3
"""
DRU injection tests.

The .kicad_dru cannot be verified by reading it. Rules are last-match-wins, an
unconditioned rule silently overrides every stricter rule below it, a bad
property name parses but evaluates false forever, and a condition split over two
lines makes KiCad discard the WHOLE file and fall back to netclass clearances.
All four of those had happened on this board.

So: every rule gets a piece of geometry that must trip it. Run this after any
edit to the .kicad_dru.

    python3 tools_dru_test.py

Writes scratch boards next to itself; does not touch the real board.
"""

import re, subprocess, sys, uuid, shutil, os
BASE=os.path.join(os.path.dirname(os.path.abspath(__file__)), "nrf-moisture-sensor")
SCR=os.environ.get("DRUTEST_SCRATCH", os.path.dirname(os.path.abspath(__file__))+"/.drutest")
os.makedirs(SCR, exist_ok=True)
KC="/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"

def seg(x1,y1,x2,y2,w,layer,net):
    return (f'\n\t(segment\n\t\t(start {x1} {y1})\n\t\t(end {x2} {y2})\n\t\t(width {w})\n'
            f'\t\t(layer "{layer}")\n\t\t(net "{net}")\n\t\t(uuid "{uuid.uuid4()}")\n\t)')
def via(x,y,net,l1="F.Cu",l2="B.Cu",size=0.4,drill=0.2):
    return (f'\n\t(via\n\t\t(at {x} {y})\n\t\t(size {size})\n\t\t(drill {drill})\n'
            f'\t\t(layers "{l1}" "{l2}")\n\t\t(net "{net}")\n\t\t(uuid "{uuid.uuid4()}")\n\t)')

SRC=open(BASE+".kicad_pcb").read()
def run(name, items):
    s=SRC; i=s.rstrip().rfind(')'); s=s[:i]+"".join(items)+s[i:]
    p=f"{SCR}/t_{name}"
    open(p+".kicad_pcb","w").write(s)
    shutil.copy(BASE+".kicad_pro", p+".kicad_pro")
    shutil.copy(BASE+".kicad_dru", p+".kicad_dru")
    subprocess.run([KC,"pcb","drc","--output",p+".rpt","--severity-error",p+".kicad_pcb"],
                   capture_output=True)
    return open(p+".rpt").read()

# Net NAMES, not codes. KiCad 10 stores nets by name in the .kicad_pcb and has no
# net-code table, and codes shift whenever a part is added or removed - which
# silently re-pointed half these tests at the wrong nets once already.
ANT,RFA,GNDPA,GND,NRESET   = "/ANT","/RF_FILTER_N1","/RF_PA_RETURN_LOCAL","GND","/NRESET"
# VBAT carries no leading slash: it is a global power symbol, not a local label.
# The slashed nets below still are local labels. Getting this wrong does not
# error - the rule simply never matches and the fire-test fails, which is what
# this harness exists to catch.
SENSE1,SHLD,SW2,VBAT       = "/SENSE1","/SHLD","/SW","VBAT"
SENSE2                     = "/SENSE2"
GNDC9,XC1,XC2              = "/RF_C9_RETURN_BOTTOM","/XC1","/XC2"
Y=90.0   # In2.Cu band in Zone B - now inside ZoneB_3V3, still empty of tracks
ZA=45.0  # Zone A: no pour on In2.Cu or B.Cu, no rule areas
# name, items, rule that MUST fire, [rule that must NOT fire]
#
# The fourth field is not decoration. A relaxing rule that matches more than it
# should does not announce itself - it silently lowers a limit somewhere else
# on the board. That is exactly how the fine-pitch fanout clearance rule
# behaved before the Type guards went in: insideArea() is true for a ZONE that
# merely OVERLAPS the area, so the rule caught ZoneB_GND_F and through it every
# track and via on the board.
CASES=[
 # name, items, rule that MUST appear
 ("rf_clear",   [seg(84,Y,90,Y,0.1565,"In2.Cu",ANT),  seg(84,Y+0.64,90,Y+0.64,0.2,"In2.Cu",NRESET)], "RF clearance to other nets"),
 ("rf_width",   [seg(84,Y,90,Y,0.20,"In2.Cu",ANT)],                                                    "RF 50R trace width"),
 ("rf_via",     [via(96.0,60.6,ANT,size=0.6,drill=0.3), seg(95.2,60.6,96.0,60.6,0.1565,"F.Cu",ANT)],  "No vias in the RF path"),
 ("sense_sw",   [seg(84,Y,90,Y,0.25,"In2.Cu",SENSE1),  seg(84,Y+1.5,90,Y+1.5,0.5,"In2.Cu",SW2)],       "Sense away from switching nodes"),
 ("shield_sw",  [seg(84,Y,90,Y,0.30,"In2.Cu",SHLD),    seg(84,Y+1.0,90,Y+1.0,0.5,"In2.Cu",SW2)],       "Shield away from switching nodes"),
 ("sense_rf",   [seg(84,Y,90,Y,0.25,"In2.Cu",SENSE1),  seg(84,Y+1.0,90,Y+1.0,0.1565,"In2.Cu",ANT)],   "Sense away from RF"),
 ("sense_gnd",  [seg(84,Y,90,Y,0.25,"In2.Cu",SENSE1),  seg(84,Y+0.6,90,Y+0.6,0.4,"In2.Cu",GND)],       "Sense away from ground"),
 ("sense_shld", [seg(84,Y,90,Y,0.25,"In2.Cu",SENSE1),  seg(84,Y+0.3,90,Y+0.3,0.3,"In2.Cu",SHLD)],      "Sense to shield spacing"),
 ("sense_sense",[seg(84,Y,90,Y,0.25,"In2.Cu",SENSE1),  seg(84,Y+0.4,90,Y+0.4,0.25,"In2.Cu",SENSE2)],  "Sense channel to sense channel"),
 ("pwr_width",  [seg(84,Y,90,Y,0.30,"In2.Cu",GND)],                                                    "Power track width"),
 ("sw_width",   [seg(84,Y,90,Y,0.30,"In2.Cu",SW2)],                                                    "Switch node width"),
 # Both of these moved. They used to sit at (96, 62) and on B.Cu at y = 90.
 # The first is inside the SHT45_Jut keepout: KiCad reports one
 # items_not_allowed per item, so the keepout won and masked the rule under
 # test - the case passed for years and then silently stopped meaning
 # anything. The second is now under the B.Cu debug bus. ZA is Zone A, which
 # has no copper on In2.Cu or B.Cu and no rule areas.
 ("gndpa_via",  [via(88.0,ZA,GNDPA,size=0.6,drill=0.3), seg(87.2,ZA,88.0,ZA,0.4,"F.Cu",GNDPA)],        "C6 ground takes no vias"),
 ("gndpa_layer",[seg(84,ZA,90,ZA,0.4,"In2.Cu",GNDPA)],                                                 "C6 ground stays on the top layer"),
 ("gndc9_inner",[seg(84,Y,90,Y,0.4,"In1.Cu",GNDC9)],                                                   "C9 ground never touches an inner plane"),
 ("fab_floor",  [seg(84,Y,90,Y,0.2,"In2.Cu",XC1),      seg(84,Y+0.30,90,Y+0.30,0.2,"In2.Cu",XC2)],     "Fab minimum clearance"),

 # The fine-pitch fanout pair, injected inside the U1-top FinePitchFanout area
 # (74.50..79.50, 65.30..67.00 on F.Cu). The width case is also a negative test
 # for "Power track width": GND is Power class, so a 0.13 mm GND track would
 # trip the 0.4 mm rule if the fanout rule were not the last width rule to
 # match. It must come back as the fanout rule, not as "Power track width".
 ("fanout_width", [seg(74.6,66.80,75.4,66.80,0.13,"F.Cu",GND)],
                  "Fine-pitch fanout: track width is set by the pad pitch"),
 ("fanout_clear", [seg(74.6,66.55,75.4,66.55,0.13,"F.Cu",XC1),
                   seg(74.6,66.69,75.4,66.69,0.13,"F.Cu",XC2)],
                  "Fine-pitch fanout: clearance is set by the pad pitch"),

 # ...and the containment test. Same 0.14 mm gap, in Zone A on B.Cu, which is
 # nowhere near a FinePitchFanout window. It must come back as the 0.127 mm fab
 # floor. If it comes back as the fanout rule, the exemption has escaped its
 # windows again.
 ("fanout_scope", [seg(84.0,45.0,90.0,45.0,0.13,"B.Cu",XC1),
                   seg(84.0,45.14,90.0,45.14,0.13,"B.Cu",XC2)],
                  "Fab minimum clearance",
                  "Fine-pitch fanout: clearance is set by the pad pitch"),
]
fails=0
for case in CASES:
    name, items, want = case[0], case[1], case[2]
    forbid = case[3] if len(case) > 3 else None
    rpt=run(name, items)
    hit = want in rpt
    leaked = forbid is not None and forbid in rpt
    ok = hit and not leaked
    note = f"expect fire: {want!r}" + (f", never {forbid!r}" if forbid else "")
    print(f"  {'PASS' if ok else 'FAIL'}  {name:14s} {note}")
    if not ok:
        fails+=1
        got=sorted(set(re.findall(r"Rule: ([^;]+);", rpt)))
        if leaked:
            print(f"        {forbid!r} fired but must not")
        print(f"        rules that fired: {got}")
print(f"\n{len(CASES)-fails}/{len(CASES)} fire-tests passed")
sys.exit(1 if fails else 0)
