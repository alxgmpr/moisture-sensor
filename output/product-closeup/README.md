Latest revision: [realistic installed CR2032](battery-realistic/README.md), with outward positive face and corrected holder clearance.

# Close-up product film — 1440p60

**Latest quality rebuild:** [10-bit Cycles video](clean/moisture-sensor-clean-2k60.mp4), [editable scene](clean/moisture-sensor-clean-2k60.blend), and [render/test details](clean/README.md). The files described below are the earlier EEVEE version.

**moisture-sensor-closeup-2k60.mp4** is an eight-second, 2560 × 1440, 60 fps H.264 product video.

The populated electronics, CR2032 cell and holder fill the opening shot. The board turns through 360 degrees while the camera tracks the populated section. At 4.5 seconds the camera begins a smooth three-second dolly back. By 7.5 seconds the whole PCB is visible, and the shot holds until the end. Rotation and pullback both ease into their stopping positions.

All moving frames are rendered natively at 60 fps. The final half-second is an intentional static hold; it reuses the identical final rendered image. There is no frame interpolation or resolution upscaling. The MP4 uses a light temporal/spatial noise filter and high-quality CRF 15 encoding. No audio is included.

## Editable project and stills

- **moisture-sensor-closeup-2k60.blend** — final editable Blender 5.2 project, saved on frame 1, including geometry, camera animation, studio lights and procedural materials.
- **opening-2k.png**, **detail-2k.png**, **ending-2k.png** — full-resolution composition stills.
- **animation-audit.json** — verifies 2560 × 1440, 60 fps, 480 frames, retained cell/holder/DNP radio module, populated-component framing and full-board final framing.
- **video-audit.json** — encoded resolution, frame rate, frame count and duration.

The final renderer is Blender EEVEE with ray-traced reflections and 32 temporal samples. Cycles and lower-resolution files in this folder are preliminary quality/composition studies, not the final deliverable.

The hardware is the existing PCB CAD assembly, including DNP U1, the existing holder model and installed CR2032 visualization envelope. The enclosure is omitted. No PCB, schematic or BOM changes were made. The original CAD model assumptions remain documented in `../product-3d/README.md`.

## Rebuild

From the repository root:

```bash
/Applications/Blender.app/Contents/MacOS/Blender -b output/product-closeup/moisture-sensor-closeup.blend --python output/product-closeup/source/build_2k60.py
/Applications/Blender.app/Contents/MacOS/Blender -b output/product-closeup/moisture-sensor-closeup-2k60.blend --python output/product-closeup/source/render_native_animation.py
bash output/product-closeup/source/encode_2k60.sh
```

The render script resumes missing frames. Use a fresh frames directory after changing the scene to avoid mixing revisions. In Blender, press Numpad 0 for the camera; scrub frames 1–480 to inspect the motion. Play the MP4 to assess the actual 60 fps result, since live viewport playback can run below the target rate.

The temporary frame sequences were removed after successful encoding and validation to reclaim disk space. The final MP4, three full-resolution stills, editable Blender file and rebuild scripts remain.
