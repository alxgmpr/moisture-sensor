# Clean 1440p60 product video

Rebuilt from `../moisture-sensor-closeup-2k60.blend`, with the original geometry, materials, studio lights, 360-degree turn, camera pullback and eight-second duration.

**Finished:** `moisture-sensor-clean-2k60.mp4` is the preferred 10-bit HEVC master. `moisture-sensor-clean-2k60-h264.mp4` is an 8-bit compatibility copy. Both retain the original eight-second animation.

## Quality changes

- Cycles path-traced shadows and reflections replace the EEVEE approximation.
- 256 maximum samples, 64 minimum adaptive samples, 0.01 noise threshold.
- OpenImageDenoise with albedo/normal guides and accurate prefiltering.
- Native 60 fps at 2560 × 1440; half-frame (180-degree) motion-blur shutter.
- Fixed Cycles seed. Sampling quality is the primary noise treatment; the seed alone does not guarantee temporal stability.
- 10-bit HEVC (H.265), CRF 16, with the Apple-compatible hvc1 tag, without temporal/spatial noise filtering. The 10-bit RGB-to-YUV conversion preserves smooth shading better than the tested 8-bit H.264 encodes.
- Frames 1–452 are rendered. Frame 452 is the first frame whose entire shutter interval is inside the static hold; frames 453–480 reuse it.

## Build and render

From the repository root:

```bash
/Applications/Blender.app/Contents/MacOS/Blender -b output/product-closeup/moisture-sensor-closeup-2k60.blend --python-exit-code 1 --python output/product-closeup/source/build_clean.py
/Applications/Blender.app/Contents/MacOS/Blender -b output/product-closeup/clean/moisture-sensor-clean-2k60.blend --python-exit-code 1 --python output/product-closeup/source/render_clean.py -- 1 452
bash output/product-closeup/source/encode_clean.sh
```

The renderer explicitly selects Metal each time because device preferences are not stored in the blend file. Frame ranges can be rendered separately. Use a fresh output directory if the scene settings change.

## Verification

`../source/verify_clean_scene.py` checks the render profile and camera/rotation continuity. The existing full framing audit also passes for all 480 frames, including retained components and the whole-board ending; see `animation-audit.json`.

`../source/measure_temporal.py` compares 30 consecutive moving frames against the previous video using optical-flow-compensated luma differences. This is a flicker proxy affected by motion blur, lighting and encoding, so it supplements visual review rather than proving perceptual smoothness.

`../source/verify_clean_video.py` verifies every PNG, 480 encoded frames, exact 60 fps timing, absence of duplicate moving frames, static final hold and full MP4 decoding. Its report is written only after the encoded file passes.

The `qa/.venv` environment contains Pillow, NumPy and OpenCV for these checks.

## Final results

The HEVC master passed the 480-frame, 60 fps, constant-timestamp, unique-rendered-frame, static-hold, PNG-integrity and complete MP4-decode checks. See `video-audit.json` and `encode-10bit.log`.

A board-plane-aligned comparison of encoded frames 215–244 measured temporal-noise RMS of 0.236 versus 0.426 in the old video (44.6% lower) across a shared 100,682-pixel PCB-surface mask. This is a local flicker proxy, not a whole-video perceptual score. See `qa/board-flicker-final.json`. The earlier generic optical-flow metric was inconclusive; 8-bit H.264 variants also scored worse on the board-aligned metric than the 10-bit master. All reports remain for inspection. Representative opening, rotation, pullback and final frames were visually inspected.
