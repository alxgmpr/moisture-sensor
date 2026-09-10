# Moisture sensor product film

- **moisture-sensor-turntable.mp4** — eight-second seamless turntable, H.264, 1280 × 720, 24 fps, no audio.
- **moisture-sensor-turntable.blend** — editable, self-contained Blender 5.2 project with animated turntable, camera, lights and procedural materials.
- **poster.png** — 1920 × 1080 Cycles still from the same composition.
- **enclosure-review.md** — recommendation, dimensional budget and manufacturer links.
- **section-comparison.svg** — section schematic explaining board capture at the case joint.

The existing CR2032 holder, installed coin cell and DNP-marked U1 radio module are all retained. The video omits the enclosure. PCB and schematic source files were not changed.

The original source model and its visualization approximations are documented in `../product-3d/README.md`. In particular, the holder is the existing C70377 CAD substitute and the installed cell is a nominal 20 × 3.2 mm envelope. Materials are artistic approximations. This film is a design visualization, not footage of manufactured hardware.

## Reproduce

From the repository root:

```bash
/Applications/Blender.app/Contents/MacOS/Blender -b output/product-3d/moisture-sensor-studio.blend --python output/product-video/source/build_video.py
/Applications/Blender.app/Contents/MacOS/Blender -b output/product-video/moisture-sensor-turntable.blend --python output/product-video/source/render_movie.py
bash output/product-video/source/encode.sh
```

Rendering uses Cycles on the installed Apple Metal GPU. `render_movie.py` resumes missing PNG frames in `frames-hd`. Clear or choose a new frames directory if changing the scene, so frames from different revisions are not mixed. The rebuild renders its poster at the configured 720p movie size; set 1920 × 1080 manually for a higher-resolution still.

`animation-audit.json` verifies camera framing for every frame, clearance above the studio surface, a matching loop boundary, and retention of both the battery holder and cell plus the DNP module. `video-audit.json` records the encoded duration, resolution, frame rate and frame count. The encoded film is also decoded fully to check for stream errors.

In Blender, use Numpad 0 for the camera, Space to play the timeline, and F12 for a still. Adjust the Turntable object's Z rotation to change the spin; its two keyframes produce one full turn over 192 displayed frames, with frame 193 matching frame 1.
