# Realistic installed CR2032 revision

The 20 × 3.2 mm cell has a formed positive nickel can, rolled edge, recessed face, negative underside, insulating gasket, satin metal finish, and surface markings. Its marked positive face points away from the PCB. The holder insertion well and spring leaves depict the installed state rather than unloaded springs penetrating the cell.

Dimensions/reference: [Panasonic CR2032](https://industry.panasonic.eu/model/33053). The existing holder mesh is the Q&J/QIJEY CR2032-BS-6-1 visualization substitute documented in `lib/footprint-sources/CR2032-BS-6.md`. These edits change only the Blender visualization, not the selected hardware, footprint, BOM, or manufacturing files.

Independent watertight-solid intersection tests measured 9.52956 mm³ overlap in the old visualization, and 0 mm³ between the new cell envelope and each of the five holder/contact solids. The revised envelope measures 20 × 20 × 3.2000003 mm. See `qa/installed-fit-meshes-fit-report.json`. These tests validate the rendered model, not a physical fit guarantee for the substitute CAD.

Full animation checks pass: retained components, camera framing, continuous camera/board motion, native 2560 × 1440 at 60 fps, and static ending. Render profile retains Cycles 256 samples, 64 minimum adaptive samples, 0.01 threshold, guided OIDN with GPU acceleration, fixed seed and a half-frame motion blur shutter. The final master uses 10-bit HEVC to preserve smooth shading.

Builder: `../source/build_realistic_battery.py`. Collision verification: `../source/verify_battery_fit.py`. GPU renderer: `../source/render_realistic_battery.py`. Encoding and video verification: `../source/encode_realistic_battery.sh` and `../source/verify_realistic_battery_video.py`.

Full-resolution opening and close-up previews were rendered with RTX 3090 OptiX and visually inspected (`qa/opening.png`, `qa/hero.png`, `qa/side.png`). Ollama was restored afterward, VM 140 stopped and detached, and the GPU lease lock verified free.

Cloud rendering uses an RTX 5090 with OptiX and GPU-accelerated OIDN. Enabling GPU denoising reduced warm frame times from approximately 13 seconds to 3.8 seconds; the sequence was restarted to keep this setting consistent throughout. A short 10-bit HEVC preview was decoded and visually inspected before final encoding.

Final output: [1440p60 10-bit HEVC video](moisture-sensor-realistic-battery-2k60.mp4) and [editable Blender scene](moisture-sensor-realistic-battery-2k60.blend). All 480 source PNGs are retained locally. Cloud and local video audits passed; the downloaded MP4 SHA256 matches the cloud copy.

The encoded frames 215–244 measured 44.27% less temporal variation than the original in a shared low-gradient PCB region (100,799 pixels). This is a local noise proxy, not a guarantee that every surface is flicker-free; see `qa/board-flicker-encoded.json`.

Vast instance 50103694 was destroyed after download and validation. The instance list confirmed removal. The rental lasted about 38 minutes, with $0.26 reported at cleanup (approximately $0.28 including a conservative allowance for final metering), below the $2 limit. See `qa/cloud-cost-report.json`. The temporary Vast public-key registration was removed. Ollama VM 130 and its API were verified running; VM 140 is stopped, detached, and the GPU lease lock is free.
