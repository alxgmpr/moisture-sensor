#!/usr/bin/env python3
"""Keep configuration outside the deployed MCUboot slots, including PM output."""
import re
import sys
from pathlib import Path

EXPECTED = {
    'mcuboot': (0, 0xd800),
    'mcuboot_pad': (0xe000, 0x800),
    'app': (0xe800, 0xaa800),
    'mcuboot_primary': (0xe000, 0xab000),
    'mcuboot_primary_app': (0xe800, 0xaa800),
    'mcuboot_secondary': (0xb9000, 0xab000),
    'zms_storage': (0x164000, 0x1000),
}

def validate(path):
    partitions = {}
    current = None
    for line in Path(path).read_text().splitlines():
        name = re.fullmatch(r'(\w+):', line)
        value = re.fullmatch(r'  (address|size): (0x[0-9a-fA-F]+|\d+)', line)
        if name:
            current = name[1]
            partitions[current] = {}
        elif value and current:
            partitions[current][value[1]] = int(value[2], 0)
    for name, (address, size) in EXPECTED.items():
        assert partitions[name]['address'] == address, (name, partitions[name])
        assert partitions[name]['size'] == size, (name, partitions[name])
    assert not ({'sensor_config', 'EMPTY_1'} & partitions.keys()), 'duplicate tail reservation'
    print(f'partitions OK: {path}; deployed slots and app budget unchanged, ZMS=4 KiB')

if __name__ == '__main__':
    validate(Path(__file__).parents[1] / 'pm_static.yml')
    for path in sys.argv[1:]:
        validate(path)
