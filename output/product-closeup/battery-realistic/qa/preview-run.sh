#!/bin/bash
set -euo pipefail
cd /srv/blender/jobs/battery-preview
blender -b scene.blend --python-exit-code 1 --python render_previews.py > render.log 2>&1
printf 'PREVIEW_RENDERS_COMPLETE\n'
