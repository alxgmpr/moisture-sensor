# Schematic redraw and PCB layout audit — design

Date: 2026-07-31
Baseline commit: `68ed8a2`

## Problem

The schematic reads as machine-generated and the PCB carries routing at
arbitrary angles. Both are consequences of the same thing: `tools_gen_sch.py`
emits every symbol at rotation 0 and connects by net-name matching, and the
routing was drawn around a placement that was never checked against the
component datasheets.

Measured state at the baseline commit:

**Schematic** — flat A2 sheet, 60 refdes, 115 symbol instances.

| Property | Value | Why it matters |
|---|---|---|
| Symbol rotations | 115 of 115 at 0° | No passive conveys direction of current flow |
| Junctions | 0 | Connectivity is name-matching, not drawn topology |
| Net labels | 146 | `+3V3` alone appears 21× as a plain text label |
| `power:+3V3` symbols | 0 | ERC power-driving checks do nothing on the 3V3 rail |
| `power:GND` symbols | 47 | — |
| `PWR_FLAG` | 8 | Each one suppresses a real ERC check |
| `no_connect` | 57 | Unverified — may hide unrouted pins |
| Sheets | 1 (flat) | No functional block structure |
| Extent | 513 × 325 mm | Sprawl, blocks intermixed |

**PCB** — 42.0 × 155.0 mm, four layers, 61 footprints, 146 track segments,
167 vias, 0 arcs.

| Property | Value |
|---|---|
| Segments at 0/45/90/135° | 104 of 146 |
| Segments off a 45° multiple | 42 of 146 (29%) |
| Off-angle by layer | F.Cu 38, B.Cu 4 |
| Off-angle by net | `/+3V3` 10, `/DECA` 7, `/DECD` 6, `/NRESET` 4, `/PMIC_INT` 3, others 12 |
| Unconnected | 44 (per NEXT-STEPS.md §1) |

Worst off-angle offenders, by length:

| Net | Angle | Length | Layer |
|---|---|---|---|
| `/XC1` | 3.38° | 5.08 mm | F.Cu |
| `/XL1` | 155.22° | 2.86 mm | F.Cu |
| `/PMIC_INT` | 78.69° | 2.55 mm | B.Cu |
| `/XL2` | 146.98° | 2.39 mm | F.Cu |
| `/+3V3` | 158.96° | 1.67 mm | F.Cu |

Roughly a third of routing is still ahead, so discarding the bad segments is
cheap.

## Decisions

These were settled during brainstorming and are not open for re-litigation
during implementation.

| Decision | Choice |
|---|---|
| Ordering | Read-only audit first, then block-by-block schematic + placement + route |
| Placement freedom | Zone A/B/C assignment, board outline, enclosure fit, SHT45 jut-out and U.FL position all fixed. Within zone B, any component may move. |
| Evidence base | Pull the missing datasheets; audit against primary sources |
| Schematic structure | One sheet, functional blocks arranged to mirror board zones |
| Rip-up scope | All zone-B routing except the RF path |
| Angle policy | 0/45/90/135° everywhere, plus teardrops and arc fillets |
| Schematic ownership | `tools_gen_sch.py` stays authoritative, upgraded to declarative placement |

### Assumptions carried into implementation

1. **Board resemblance means relative adjacency, not literal aspect ratio.**
   The board is 42 × 155 mm with blocks stacked vertically. Reproducing that
   proportion on a schematic sheet gives an unusable tall column. The redraw
   preserves the top-to-bottom block sequence and the left/right neighbour
   relationships within each block, not the 1:3.7 aspect ratio.
2. **Phase 1 findings return for triage before Phase 3 moves any part.**
   The audit produces a ranked findings document; component moves wait on
   review of that document.

## Phase 0 — Evidence base

Download and cache in `doc/`:

| Part | Document | Sections needed |
|---|---|---|
| nPM1300 | Nordic product spec | Buck loop layout, bypass placement, thermal pad |
| FDC1004 | TI SNOSCY5 | SHLD routing, guard geometry, pinout confirmation |
| SHT45-AD1F | Sensirion datasheet | Keepout, thermal isolation, bypass |
| TPS7A1650 | TI datasheet | Input/output cap placement, thermal pad |

The nRF54L15 needs no download — `doc/nRF54L15_qfaa_4L_config1_schematic.pdf`,
`_pcb.pdf` and `_draftsman_pcb.pdf` are Nordic's own reference for this exact
part and stackup, which is stronger than prose guidance.

Use the `kicad-happy:datasheets` and `kicad-happy:digikey` skills.

**Contradiction handling.** HARDWARE.md and LAYOUT.md carry prior verification
claims ("verified against SNOSCY5", "Confirmed against Nordic's nPM1300 EK
(PCA10152)", "Confirmed against TI's FDC1004EVM"). Where a fresh read of the
primary document contradicts one of those claims, that contradiction is itself
a Phase 1 finding and gets reported, not silently resolved.

## Phase 1 — Read-only audit

No file changes in this phase. Output is a single ranked findings document at
`docs/audit-2026-07-31.md`. Every finding cites its evidence source and carries
a confidence label.

### 1.1 Netlist correctness

Trace every net pin-to-pin against datasheet pinouts. Specific targets:

- **57 `no_connect` markers** — each verified as genuinely NC per its
  datasheet, or reported as a suppressed connection.
- **8 `PWR_FLAG`s** — each justified or marked for removal. A `PWR_FLAG`
  exists to tell ERC a net is driven; on a net that has a real driver it only
  hides errors.
- **Single-pin nets** — any net with one pin is either an error or a
  deliberate test point.
- **3 `NetTie`s** (NT1 `NetTie_VSSPA`, NT2, NT3) — confirm each joins the two
  domains it is supposed to join, at the point it is supposed to join them.
- Nets connecting pins that should not be connected.

### 1.2 Power topology and loop area

Measure enclosed loop area from footprint pad geometry, not from schematic
adjacency. Coordinates below are `.kicad_pcb` file coordinates — subtract
(60, 40) for board-relative.

| Loop | Components | Baseline geometry |
|---|---|---|
| nPM1300 buck | L10 (64.0, 93.5) → U2 (69.5, 96.0) → C20–C23 (x=75) | Output caps sit on the opposite side of the IC from the inductor — measure first |
| nRF54L15 DCDC | FB1 (70.0, 62.6) / L1 (70.0, 64.4) → U1 (77.0, 63.0) → C1 (70.0, 66.3) / C10 (70.0, 67.4) | — |
| TPS7A1650 | C30 (89.5, 89.0) / C31 (85.5, 89.0) → U5 (87.5, 92.5) | — |

Then per-bypass-cap distance to the pin it actually serves. C2 (66.5, 62.6),
C12 (66.5, 64.0) and C5 (66.5, 65.4) sit ~10.5 mm from U1 at (77.0, 63.0);
determine which pins they serve and whether that separation is defensible for
a QFN48.

### 1.3 Datasheet conformance

- U1 cluster compared directly against Nordic's reference PCB layout.
- X1 (32.768 kHz, CM8V-T1A) and X2 (32 MHz, FA-128) load caps and guard.
- QFN thermal-pad via count and placement, both QFNs.
- FDC1004 SHLD routing and guard geometry against LAYOUT.md §5.
- SHT45 jut-out keepout and thermal isolation.

### 1.4 Geometry

- The 42 enumerated off-angle segments.
- Off-grid pads and footprint origins.
- Acute-angle trace junctions.
- **Zone-boundary straddles.** J5's centre sits at board y = 12.00, which is
  0.50 mm past the zone A/B boundary at 11.5, and the U.FL body spans roughly
  y = 10.5–13.5. NEXT-STEPS.md assigns J5 to zone A. Confirm whether the
  straddle is intended or whether the zone table and the placement disagree.
  Check every component against its stated zone the same way.

## Phase 2 — Schematic redraw

`tools_gen_sch.py` is rewritten so placement is declarative data rather than an
auto-place pass: per-block origin, per-symbol offset and rotation, explicit
wire paths, explicit junction coordinates.

Rules the regenerated schematic must satisfy:

1. `power:+3V3`, `power:VSYS`, `power:VBAT`, `power:VBUS_IN` symbols replace
   the corresponding plain text labels. Net labels survive only for genuine
   cross-block nets.
2. Every bypass capacitor is drawn adjacent to the pin it serves, with the
   rail entering from above and a GND symbol below, so orientation reads as
   the current path.
3. Series elements (FB1, L1, L10) drawn horizontally, oriented in the
   direction of power flow.
4. Intra-block connectivity uses real wires and junctions.
5. Each functional block carries an outline and a title matching its PCB zone
   name.
6. ERC clean **with the unjustified `PWR_FLAG`s removed**, not with them left
   in place suppressing the check.

Block sequence, top to bottom, mirroring board y-order. All 60 schematic
components are assigned to exactly one block; MP1 (the enclosure) has no
symbol and does not appear.

| Block | Board y | n | Members |
|---|---|---|---|
| RF / antenna | 12–17 | 9 | J5, NT2, C11, L2, L3, L4, C9, C6, NT1 |
| MCU | 17–30 | 16 | U1, X1, X2, FB1, L1, C1–C5, C7, C8, C10, C12, C13, R1 |
| Ambient | 20.6 (jut-out) | 2 | U4, C27 |
| Debug | 33–36 | 3 | J4, R22, R23 |
| Power / PMIC | 41–64 | 24 | U2, U5, J1, J3, L10, D5, D3, D4, TH1, NT3, C20–C25, C30, C31, R20, R21, R25, R26, TP4, TP5 |
| Sense front end | 63–73 | 6 | U3, C26, J2, TP1–TP3 |

### Coordinate systems — do not mix these

Two different origins are in play and they differ by (60, 40):

- **`.kicad_pcb` file coordinates.** What the footprint `(at …)` values and the
  Phase 1.2 tables below use. Edge.Cuts bounding box is
  x 60.00–102.00, y 40.00–195.00.
- **Board-relative coordinates.** What NEXT-STEPS.md's zone table and the
  `Board y` column above use. `board_y = file_y − 40.00`,
  `board_x = file_x − 60.00`.

Board size confirms at 42.00 × 155.00 mm.

## Phase 3 — Block-by-block placement and routing

Order: power/PMIC → MCU+RF → sense → debug/test. Each block completes
schematic-fix → placement-fix → route → DRC before the next begins.

**Preserved, not touched:**
- The tuned 0.36 mm RF microstrip (`ANT_FEED`, `RF_A`, `RF_B`) and its guard —
  impedance work from LAYOUT.md §2.
- QFN centre-pad via arrays, both QFNs.
- Ground stitching vias.

**Ripped up:** all other zone-B routing.

**Angle policy:** every segment on every layer at 0/45/90/135°. Teardrops at
pad junctions, arc fillets at corners.

## Phase 4 — Verification

| Check | Pass condition |
|---|---|
| ERC | Clean, with unjustified `PWR_FLAG`s removed rather than retained |
| DRC | Clean against `moisture-sensor-carrier.kicad_dru` |
| Connectivity | 0 unconnected |
| Angles | `tools_lint_angles.py` reports 0 segments off a 45° multiple |
| Net equivalence | Schematic-vs-PCB net comparison shows drawing-only changes, except where Phase 1 found a genuine error — each such change called out individually |

`tools_lint_angles.py` is the analyzer written during brainstorming, promoted
into the repo as a permanent check.

## Toolchain constraints

Carried from NEXT-STEPS.md; violating these silently destroys work.

- **Do not run `tools_gen_pcb.py`.** The `.kicad_pcb` carries manual fillets at
  the jut-out corners that the generator does not emit, and `main()` strips
  every drawing before redrawing. The script stays as reference for its
  constants and self-checks.
- **Do not hand-edit `.kicad_sch`.** Edit `tools_gen_sch.py` and re-run.
- **DRU rules are last-match-wins.** Fabrication floors sit above specific
  rules. Any new rule needs an injection test in `tools_dru_test.py`, not a
  read-through.
- **`insideArea()` is true for a zone that merely overlaps the area**, not for
  the intersecting part. Zone-conditioned rules need
  `&& A.Type != 'Zone' && B.Type != 'Zone'`.
- **Both Nordic QFN footprints carry their pin-1 marker twice.**
  `tools_gen_pcb.py` strips duplicates at load time; since the generator is
  frozen, silkscreen-overlap warnings may reappear.

## Out of scope

- Part selection. The BOM is settled; L1, X2, U5, the cell and the panel are
  closed decisions.
- Board outline, enclosure fit, zone assignment.
- Solar architecture. Settled — populated on every board, panel external.
- Firmware.
