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
BASE="/Users/alex/moisture-sensor-carrier/moisture-sensor-carrier"
SCR=os.environ.get("DRUTEST_SCRATCH", os.path.dirname(os.path.abspath(__file__))+"/.drutest")
os.makedirs(SCR, exist_ok=True)
KC="/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"

def seg(x1,y1,x2,y2,w,layer,net):
    return (f'\n\t(segment\n\t\t(start {x1} {y1})\n\t\t(end {x2} {y2})\n\t\t(width {w})\n'
            f'\t\t(layer "{layer}")\n\t\t(net {net})\n\t\t(uuid "{uuid.uuid4()}")\n\t)')
def via(x,y,net,l1="F.Cu",l2="B.Cu",size=0.4,drill=0.2):
    return (f'\n\t(via\n\t\t(at {x} {y})\n\t\t(size {size})\n\t\t(drill {drill})\n'
            f'\t\t(layers "{l1}" "{l2}")\n\t\t(net {net})\n\t\t(uuid "{uuid.uuid4()}")\n\t)')

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

# net codes
ANT,RFA,GNDPA,GND,NRESET,SENSE1,SHLD,SW2,VBAT,PVSS2,GNDC9,XC1,XC2 = 12,6,7,9,8,23,22,45,59,13,89,10,11
Y=90.0   # empty In2.Cu band in Zone B
CASES=[
 # name, items, rule that MUST appear
 ("rf_clear",   [seg(84,Y,90,Y,0.38,"In2.Cu",ANT),     seg(84,Y+0.64,90,Y+0.64,0.2,"In2.Cu",NRESET)], "RF clearance to other nets"),
 ("rf_width",   [seg(84,Y,90,Y,0.20,"In2.Cu",ANT)],                                                    "RF 50R trace width"),
 ("rf_via",     [via(96.0,60.6,ANT,size=0.6,drill=0.3), seg(95.2,60.6,96.0,60.6,0.38,"F.Cu",ANT)],      "No vias in the RF path"),
 ("sense_sw",   [seg(84,Y,90,Y,0.25,"In2.Cu",SENSE1),  seg(84,Y+1.5,90,Y+1.5,0.5,"In2.Cu",SW2)],       "Sense away from switching nodes"),
 ("shield_sw",  [seg(84,Y,90,Y,0.30,"In2.Cu",SHLD),    seg(84,Y+1.0,90,Y+1.0,0.5,"In2.Cu",SW2)],       "Shield away from switching nodes"),
 ("sense_rf",   [seg(84,Y,90,Y,0.25,"In2.Cu",SENSE1),  seg(84,Y+1.0,90,Y+1.0,0.38,"In2.Cu",ANT)],      "Sense away from RF"),
 ("sense_gnd",  [seg(84,Y,90,Y,0.25,"In2.Cu",SENSE1),  seg(84,Y+0.6,90,Y+0.6,0.4,"In2.Cu",GND)],       "Sense away from ground"),
 ("sense_shld", [seg(84,Y,90,Y,0.25,"In2.Cu",SENSE1),  seg(84,Y+0.3,90,Y+0.3,0.3,"In2.Cu",SHLD)],      "Sense to shield spacing"),
 ("pwr_width",  [seg(84,Y,90,Y,0.30,"In2.Cu",GND)],                                                    "Power track width"),
 ("chg_width",  [seg(84,Y,90,Y,0.50,"In2.Cu",VBAT)],                                                   "Charge path width"),
 ("sw_width",   [seg(84,Y,90,Y,0.30,"In2.Cu",SW2)],                                                    "Switch node width"),
 ("pvss2_width",[seg(84,Y,90,Y,0.30,"In2.Cu",PVSS2)],                                                  "BUCK2 power ground is short and fat"),
 ("gndpa_via",  [via(96.0,62.0,GNDPA,size=0.6,drill=0.3), seg(95.2,62.0,96.0,62.0,0.4,"F.Cu",GNDPA)],   "C6 ground takes no vias"),
 ("gndpa_layer",[seg(84,Y,90,Y,0.4,"B.Cu",GNDPA)],                                                     "C6 ground stays on the top layer"),
 ("gndc9_inner",[seg(84,Y,90,Y,0.4,"In1.Cu",GNDC9)],                                                   "C9 ground never touches an inner plane"),
 ("ant_keepout",[seg(84,45,90,45,0.2,"In2.Cu",XC1)],                                                   "Antenna keepout is copper free"),
 ("fab_floor",  [seg(84,Y,90,Y,0.2,"In2.Cu",XC1),      seg(84,Y+0.30,90,Y+0.30,0.2,"In2.Cu",XC2)],     "Fab minimum clearance"),
]
fails=0
for name, items, want in CASES:
    rpt=run(name, items)
    hit = want in rpt
    print(f"  {'PASS' if hit else 'FAIL'}  {name:14s} expect fire: {want!r}")
    if not hit:
        fails+=1
        got=sorted(set(re.findall(r"Rule: ([^;]+);", rpt)))
        print(f"        rules that fired instead: {got}")
print(f"\n{len(CASES)-fails}/{len(CASES)} fire-tests passed")
sys.exit(1 if fails else 0)
