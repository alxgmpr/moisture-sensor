#!/usr/bin/env python3
"""Validate the MCUmgr DFU archive emitted by a sysbuild."""

import json
import hashlib
import re
import struct
import sys
import zipfile


def version(value):
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)(?:\+\d+)?", value)
    if not match:
        raise AssertionError(f"invalid MCUboot version: {value!r}")
    return tuple(int(part) for part in match.groups())


def main(path):
    with zipfile.ZipFile(path) as archive:
        names = set(archive.namelist())
        assert "manifest.json" in names, "manifest.json missing"
        manifest = json.loads(archive.read("manifest.json"))
        files = manifest.get("files", [])
        assert len(files) == 1, f"expected one application, got {len(files)}"
        entry = files[0]
        assert entry["type"] == "application"
        assert entry["slot_index_primary"] == "1"
        assert entry["slot_index_secondary"] == "2"
        assert entry["file"] in names
        image = archive.read(entry["file"])
        assert len(image) == entry["size"]
        magic, _, header_size, protected_size, image_size, _ = struct.unpack_from("<IIHHII", image)
        assert magic == 0x96F3B83D
        assert header_size == 0x800, "deployed slot has a 2 KiB header"
        assert struct.unpack_from("<BBH", image, 20) == version(entry["version_MCUBOOT"])
        tlv_offset = header_size + image_size + protected_size
        magic, tlv_size = struct.unpack_from("<HH", image, tlv_offset)
        assert magic == 0x6907 and tlv_offset + tlv_size == len(image)
        tlvs = {}
        offset = tlv_offset + 4
        while offset < len(image):
            tag, _, length = struct.unpack_from("<BBH", image, offset)
            offset += 4
            assert offset + length <= len(image)
            assert tag not in tlvs, "duplicate image TLV"
            tlvs[tag] = image[offset:offset + length]
            offset += length
        # The deployed MCUboot expects SHA-256 and an RSA-2048 signature.
        # New SDK defaults on nRF54L can silently emit SHA-512 instead.
        assert tlvs.get(0x10) == hashlib.sha256(image[:tlv_offset]).digest(), "SHA-256 image hash missing/invalid"
        assert len(tlvs.get(0x01, b"")) == 32, "expected SHA-256 public-key hash"
        assert len(tlvs.get(0x20, b"")) == 256, "RSA-2048 signature missing"
    print(f"DFU OK: {path} version {entry['version_MCUBOOT']} primary=1 secondary=2")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(f"usage: {sys.argv[0]} dfu_application.zip")
    main(sys.argv[1])
