#!/bin/bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y curl xz-utils ffmpeg libxi6 libxrender1 libxkbcommon0 libsm6 libgl1 libegl1 libxxf86vm1 libxfixes3 libxcursor1 libdbus-1-3 libgomp1
cd /opt
curl -fL --retry 3 https://download.blender.org/release/Blender5.2/blender-5.2.1-linux-x64.tar.xz -o blender.tar.xz
curl -fsSL https://download.blender.org/release/Blender5.2/blender-5.2.1.sha256 -o blender.sha256
mv blender.tar.xz blender-5.2.1-linux-x64.tar.xz
sha256sum --check --ignore-missing blender.sha256
tar -xJf blender-5.2.1-linux-x64.tar.xz
ln -sfn /opt/blender-5.2.1-linux-x64/blender /usr/local/bin/blender
mkdir -p /root/render/frames
nvidia-smi --query-gpu=name,driver_version --format=csv,noheader
blender --version
