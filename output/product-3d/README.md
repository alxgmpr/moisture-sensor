# Moisture sensor — Blender product studio

Open `moisture-sensor-studio.blend` in Blender 5.2 or later. The scene selector at the top right contains:

1. **Bare PCB** — full assembled PCB and installed cell.
2. **Enclosed product** — black Hammond 1551WK with the probe and sensor tab exposed.
3. **Exploded assembly** — bottom, populated PCB, gasket and lid separated vertically.
4. **Electronics detail** — closer camera over the populated board.

Use Numpad 0 for the active camera and F12 to render. All geometry and procedural materials are contained in the Blender file; no external image textures or add-ons are required. Materials, cameras, area lights and objects remain editable. The scenes use metres internally with millimetre display, Cycles, AgX, depth of field and denoising. The board has satin forest-green solder mask, exposed laminate edges, white silkscreen and metallic pads; the case has fine molded-plastic texture. These finishes are artistic approximations, not measured samples.

## CAD exports and inclusion

- `pcb-full.step`: mechanical PCB assembly with pads and all attached component models.
- `pcb-full.glb`: Blender-ready PCB with copper, pads, vias, solder mask and silkscreen.
- `case-bottom-concept.step`: original manufacturer's bottom with proposed probe and sensor slots.
- `case-meshes.json`: tessellated manufacturer case geometry used by Blender.

The source is `nrf-moisture-sensor.kicad_pcb`. DNP parts are **included**, including U1 / BL54L15, whose DNP flag is for the assembly stage. Export commands deliberately omit `--no-dnp`; the board's manufacturing flags are unchanged. U1's imported geometry is verified in `import-audit.json`. KiCad's saved viewer settings were updated to show DNP and excluded-position-file footprints; an already-running viewer may need reopening. Bare test points, fiducials and footprint pads do not require separate component models.

## Assembly assumptions

The case uses the original `lib/enclosure/1551WK_{Bottom,Lid,Gasket}.stp` assets. Alignment follows `tools_encl_draw.py`: board-local (17,37) mm is at the case centre; PCB underside is 6.20 mm above the outer bottom and the PCB is 1.60 mm thick.

The manufacturer's unmodified case cannot pass the probe and SHT45 tab. The visualization adds a 20.8 × 2.3 mm probe slot and 5.8 × 2.3 mm sensor slot, centred at 7.0 mm above the outer bottom. These are concept clearances for visualization, not released machining drawings or a sealing/assembly qualification. Original STEP files are preserved. Closed-case RF performance and sensor/probe sealing remain design validation items documented in the hardware project.

The battery holder uses the project's existing C70377 visualization substitute for the selected CR2032-BS-6. A nominal 20 × 3.2 mm CR2032 cell and simplified nylon case fastener heads were added for product appearance; their exact seating and fastening details require actual part confirmation. No human hand is included; the scene is true-scale for further hand/photography composition.

`drc.rpt` and `erc.rpt` contain zero error-level violations; DRC also reports zero unconnected pads. The CAD check in `case-fit-check.json` found 0.0 mm³ intersection between the PCB substrate and modified case bottom at the documented mounting height. The STEP substrate is 1.4942 mm thick, with exported copper/mask layers completing the nominal 1.6 mm stack. Components, cell and fasteners are outside this limited fit check; this is not a full mechanical interference qualification.

## Rebuild

Run `bash output/product-3d/source/export.sh` from this repository. It uses the installed KiCad CLI, existing `.venv-cq` CadQuery environment and installed Blender. The script repeats the error-level checks before exporting. Final photographs are the numbered PNG files in this folder.

Blender glTF material import reference: https://docs.blender.org/manual/en/dev/addons/scene_gltf2.html
