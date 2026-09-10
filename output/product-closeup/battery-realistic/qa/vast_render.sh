#!/bin/bash
set -uo pipefail
cd /root/render
blender -b moisture-sensor-realistic-battery-2k60.blend --python-exit-code 1 --python render_realistic_battery.py -- 1 452 > render.log 2>&1
result=$?
printf '%s\n' "$result" > render.exit
exit "$result"
