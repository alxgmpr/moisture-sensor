# PCB product render

`pcb-three-quarter.png` is a 2400 × 1800 Blender Cycles render of the maintained KiCad board, with the MCU module nearest the camera. It uses procedural solder-mask texture, metallic component finishes, three area lights, up to 96 samples, and denoising. The holder body uses white molded plastic with metallic electrical contacts. The empty battery holder is shown as exported; no battery or enclosure is synthesized.

The export includes the MCU module even though its footprint is marked DNP in the design. Including it is intentional for this assembled-board illustration. Existing component-model substitutions remain visualization approximations; see the model-source notes under `lib/footprint-sources/`. Materials and lighting are presentation choices, not measured surface properties.

PCB SHA-256: `15fb16698dda97d8ae5c5b4ddb6095a8edb0759da1a4a20add4bf374184158e5`.

## Rebuild

From the repository root, with KiCad 10 and Blender installed:

```sh
mkdir -p output/pcb-render
kicad-cli pcb export glb --force --subst-models \
  --include-pads --include-silkscreen --include-soldermask \
  --output "$PWD/output/pcb-render/board.glb" nrf-moisture-sensor.kicad_pcb
blender --background --threads 4 --python scripts/render_pcb.py
```

The script also saves an editable scene to `output/pcb-render/moisture-sensor.blend`. Use `-- --preview` for a 1200 × 900, 24-sample composition preview. Rendering is serial and limited to four CPU threads, with a 240-second sampling limit. The GLB and Blender scene remain local generated artifacts; the final PNG and rendering script are committed.
