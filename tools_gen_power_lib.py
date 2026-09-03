#!/usr/bin/env python3
"""Generate lib/power_local.kicad_sym -- project power symbols for the rails
KiCad's stock power library does not carry.

A rail drawn as a power symbol is checked by ERC as a rail. A rail spelled as a
plain text label is not: it is just a name, and a typo in one of 21 copies
silently makes a second net. Every rail on this board gets a symbol.

Two graphic styles, matching the usual convention:
  bar   - a supply rail (arrow-and-bar, like the stock +3V3)
  arrow - a derived or gated rail, drawn as an open arrow so it reads
          differently from a primary supply at a glance

Run:  python3 tools_gen_power_lib.py
"""
import os

PROJ = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(PROJ, "lib", "power_local.kicad_sym")

# name, style, description
RAILS = [
    ("VSYS",        "bar",   "nPM1300 system rail -- battery or VBUS, whichever is higher"),
    ("VBAT",        "bar",   "Primary-cell VBAT rail"),
    ("VBUS_IN",     "bar",   "USB-C VBUS, OR-ed with the solar pre-regulator through D5"),
    ("SOLAR_PANEL", "arrow", "Raw panel input at J3, ahead of U5"),
    ("SOLAR_5V",    "arrow", "U5 TPS7A1650 output, 5 V, feeds VBUS_IN through D5"),
    ("FDC_VDD",     "arrow", "Gated FDC1004 supply, off nPM1300 LOADSW1"),
]

BAR = """\t\t\t(polyline
\t\t\t\t(pts
\t\t\t\t\t(xy -0.762 1.27) (xy 0 2.54)
\t\t\t\t)
\t\t\t\t(stroke (width 0) (type default))
\t\t\t\t(fill (type none))
\t\t\t)
\t\t\t(polyline
\t\t\t\t(pts
\t\t\t\t\t(xy 0 2.54) (xy 0.762 1.27)
\t\t\t\t)
\t\t\t\t(stroke (width 0) (type default))
\t\t\t\t(fill (type none))
\t\t\t)
\t\t\t(polyline
\t\t\t\t(pts
\t\t\t\t\t(xy 0 0) (xy 0 2.54)
\t\t\t\t)
\t\t\t\t(stroke (width 0) (type default))
\t\t\t\t(fill (type none))
\t\t\t)"""

ARROW = """\t\t\t(polyline
\t\t\t\t(pts
\t\t\t\t\t(xy 0 0) (xy 0 1.27)
\t\t\t\t)
\t\t\t\t(stroke (width 0) (type default))
\t\t\t\t(fill (type none))
\t\t\t)
\t\t\t(polyline
\t\t\t\t(pts
\t\t\t\t\t(xy -1.016 1.27) (xy 0 2.794) (xy 1.016 1.27) (xy -1.016 1.27)
\t\t\t\t)
\t\t\t\t(stroke (width 0) (type default))
\t\t\t\t(fill (type none))
\t\t\t)"""


def prop(name, value, y, hide):
    return (f'\t\t(property "{name}" "{value}"\n'
            f'\t\t\t(at 0 {y} 0)\n'
            f'\t\t\t(show_name no)\n'
            f'\t\t\t(do_not_autoplace no)\n'
            + ('\t\t\t(hide yes)\n' if hide else '')
            + '\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t)\n'
            '\t\t)')


def symbol(name, style, descr):
    art = BAR if style == "bar" else ARROW
    esc = descr.replace('"', '\\"')
    return f'''\t(symbol "{name}"
\t\t(power global)
\t\t(pin_numbers
\t\t\t(hide yes)
\t\t)
\t\t(pin_names
\t\t\t(offset 0)
\t\t\t(hide yes)
\t\t)
\t\t(exclude_from_sim no)
\t\t(in_bom yes)
\t\t(on_board yes)
\t\t(in_pos_files yes)
\t\t(duplicate_pin_numbers_are_jumpers no)
{prop("Reference", "#PWR", -3.81, True)}
{prop("Value", name, 3.556, False)}
{prop("Footprint", "", 0, True)}
{prop("Datasheet", "", 0, True)}
{prop("Description", esc, 0, True)}
{prop("ki_keywords", "global power " + name, 0, True)}
\t\t(symbol "{name}_0_1"
{art}
\t\t)
\t\t(symbol "{name}_1_1"
\t\t\t(pin power_in line
\t\t\t\t(at 0 0 90)
\t\t\t\t(length 0)
\t\t\t\t(name ""
\t\t\t\t\t(effects
\t\t\t\t\t\t(font
\t\t\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t\t\t)
\t\t\t\t\t)
\t\t\t\t)
\t\t\t\t(number "1"
\t\t\t\t\t(effects
\t\t\t\t\t\t(font
\t\t\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t\t\t)
\t\t\t\t\t)
\t\t\t\t)
\t\t\t)
\t\t)
\t\t(embedded_fonts no)
\t)'''


def main():
    body = "\n".join(symbol(n, s, d) for n, s, d in RAILS)
    doc = ('(kicad_symbol_lib\n'
           '\t(version 20241209)\n'
           '\t(generator "tools_gen_power_lib.py")\n'
           '\t(generator_version "10.0")\n'
           f'{body}\n'
           ')\n')
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w").write(doc)
    print("wrote %s  (%d symbols: %s)" % (OUT, len(RAILS), ", ".join(n for n, _, _ in RAILS)))


if __name__ == '__main__':
    main()
