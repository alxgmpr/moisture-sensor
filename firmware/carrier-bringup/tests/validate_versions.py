#!/usr/bin/env python3
"""Keep the production and maintenance image versions monotonic."""

import re
from pathlib import Path


def read_version(path):
    values = {}
    for line in Path(path).read_text().splitlines():
        match = re.match(r"(?:VERSION_(MAJOR|MINOR)|PATCHLEVEL)\s*=\s*(\d+)", line)
        if match:
            values[match.group(1) or "PATCHLEVEL"] = int(match.group(2))
    return tuple(values[key] for key in ("MAJOR", "MINOR", "PATCHLEVEL"))


def main():
    production = read_version(Path(__file__).parents[1] / "VERSION")
    text = (Path(__file__).parents[1] / "ota.conf").read_text()
    match = re.search(r'CONFIG_MCUBOOT_IMGTOOL_SIGN_VERSION="([^"]+)"', text)
    assert match, "maintenance image version missing"
    maintenance = tuple(int(x) for x in match.group(1).split(".")[:3])
    assert maintenance > production, (production, maintenance)
    print(f"versions OK: sensor={production} maintenance={maintenance}")


if __name__ == "__main__":
    main()
