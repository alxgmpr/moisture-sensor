# KiCad routing handoff — 2026-09-04

The board is saved with an incomplete local routing pass. Design edits in this
pass were made through KiCad's GUI, including schematic footprint assignments
and Update PCB from Schematic. No external PCB file rewrite was used in this
pass. GUI canvas interaction became unreliable; routing has stopped so the user
can take over without concurrent edits.

## Hand-route these three connections first

Coordinates below are millimetres in the saved board. Use Find to locate the
references/nets, or double-click the corresponding DRC unconnected item.

| Order | Net | Endpoints | Routing intent |
| --- | --- | --- | --- |
| 1 | `/XC2` | X2 pad 3 `(72.575, 56.875)` → U1 pad 35 `(75.200001, 60.079)` | Route this more constrained crystal connection first, on F.Cu with no signal vias. Adjust X2/C5/C4 placement if necessary to leave space for both clock traces. |
| 2 | `/XC1` | X2 pad 1 `(73.725, 58.325)` → U1 pad 34 `(75.600, 60.079)` | Short F.Cu connection with no signal vias. Both crystal nets currently have no tracks. Check grounded case pads and surrounding ground after any crystal move. |
| 3 | `/DECA` | Local branch at U1 pad 43 `(74.079, 63.200)` / FB1 pad 2 `(72.470, 63.400)` → RF branch at U1 pad 33 `(75.999999, 60.079)` / C5 pad 1 `(75.670, 58.850)` | Join the two existing copper islands. C2/C12/FB1/U1-43 already connect; C5 already connects to U1-33. Keep the decoupling connections short. |

C5's saved centre is `(75.35, 58.85)`, rotation 180 degrees. Attempts to move
it farther upward did not persist; do not assume that space has been created.
The crystal corridor is tight, so placement remains provisional.

## Repair these routing issues from this pass

1. **C10 / +3V3:** widen the two 0.15 mm F.Cu segments starting at
   `(72.920, 65.800)` and `(73.700, 65.800)` to at least **0.20 mm**, then check
   clearances. These are two DRC errors.
2. **U1 pad 39 / SCL:** the new front-layer escape toward the via at
   `(70.000, 61.373)` is 0.127 mm. Reroute/widen the local escape to at least
   **0.15 mm** under the existing fine-pitch rule. This produces four DRC width
   errors. Reposition nearby capacitors if needed; do not relax the rule merely
   to suppress the errors.
3. **U1 pad 45 / DECD:** the new connection from `(74.079, 64.000001)` toward
   `(72.047501, 64.000001)` and FB1 is 0.127 mm. Make the escape at least
   **0.15 mm** and verify clearance to L1/DCC. This produces one DRC width error.
4. **Dangling +3V3 stub:** DRC identifies the F.Cu track at `(69.4325, 67.400)`,
   length 0.8325 mm, UUID `2d6fc38c-e752-4086-96a5-df59513973a5`. Remove the
   obsolete loose end while retaining the connected power network.
5. **Redundant DECD branch:** inspect the old branch from FB1 pad 1 through
   `(71.830, 63.490)` → `(71.450, 63.870)` → `(71.450, 64.4625)` →
   `(71.4125, 64.500)`. It remains alongside the new connection and can be
   simplified. Clean up off-centre L1 pad entries after its placement shift.

The width setting was left at **0.127 mm** during the crystal attempts. Select
the appropriate width before continuing; the fine-pitch rule requires 0.15 mm
and ordinary power routing requires 0.20 mm. Router mode was Walk Around,
H/V/45 routing, with DRC violations disabled.

## What changed and what to preserve

- Support parts were changed to standard footprints through the schematic:
  C1/C2/C4/C5/C7/C8/C10/C12/C13, FB1 and R1 to 0201; C3 to 0402; L1 to 0603.
  Exact purchased MPN/package compatibility still needs confirmation.
- The local nRF power parts, crystal and I2C pull-ups were repositioned. The
  current DRC reports no courtyard overlaps. Assembly access still needs review.
- DCC and local DECA/DECD routing were shortened; I2C pull-up routing and its
  +3V3 connection were reworked. The missing connections and width errors above
  must be finished before accepting this placement.
- Preserve C6's dedicated front-layer VSS_PA return and C9's separate bottom
  return. Preserve the prior C11 ground correction, SHT45 bypass C27, FDC1004
  bypass C28 and sensing shields. Do not blanket-reroute the RF/sensor sections.

## Verified handoff state

After saving and refilling in KiCad, CLI DRC with zone refill and schematic
parity reports:

- **7 track-width errors and 3 missing connections.**
- **47 warnings:** 18 silkscreen-over-copper, 15 overlapping silkscreen,
  13 library footprint differences and 1 dangling track.
- **0 courtyard-overlap, short or clearance violations reported.**
- **0 schematic/PCB parity issues.**
- Electrical netlist fingerprint unchanged: **62 nets**.
- Repository checks: **35 passed**. These do not substitute for PCB DRC.

Machine-readable report:
[`handoff-drc.json`](../tmp/board-finish/handoff-drc.json).
Pre-layout-pass backup: `tmp/board-finish/baseline/`. That baseline had zero DRC
errors and zero unrouted connections; it predates this placement/routing pass.
Keep the schematic, PCB and project together if reviewing or restoring that
backup, and avoid loading an older disk copy over the current GUI session.

After routing, refill zones and require zero missing connections, zero DRC
errors and zero parity issues. Resolve the silkscreen warnings, then continue
the RF, manufacturing, BOM and prototype work in
[`TODO.md`](../TODO.md). The current board is not ready
for fabrication.
