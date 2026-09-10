#!/usr/bin/env python3
"""Package PCB reference Gerbers with only U1's custom top-paste apertures."""
from pathlib import Path
import argparse
import re
import zipfile


def package_module_stencil(directory):
    directory = Path(directory)
    paste = (directory / 'manual-module-stencil/manual-module-F_Paste.gtp').read_bytes()
    text = paste.decode()
    assert len(re.findall(r'D03\*', text)) == 39, 'Expected 39 module apertures'
    assert set(re.findall(r'%TO.C,([^*]+)\*%', text)) == {'U1'}
    assert '%TF.FileFunction,Paste,Top*%' in text
    with zipfile.ZipFile(directory / 'JLC-Gerbers.zip') as source:
        files = {name: source.read(name) for name in source.namelist()}
    top = [name for name in files if name.endswith('.gtp')]
    bottom = [name for name in files if name.endswith('.gbp')]
    outline = [name for name in files if name.endswith(('.gm1', '.gko'))]
    assert len(top) == len(bottom) == len(outline) == 1
    assert 'D03*' not in files[bottom[0]].decode(), 'Unexpected bottom paste'
    files[top[0]] = paste
    # JLC recommends one clearly named outline file; GKO is its documented suffix.
    files[str(Path(outline[0]).with_suffix('.gko'))] = files.pop(outline[0])
    note = (
        'CUSTOM TOP-SIDE STENCIL ONLY - BL54L15 MODULE U1\n'
        'Cut only the 39 apertures in the supplied .gtp top solder-paste layer.\n'
        'The .gbp bottom paste layer is intentionally empty. Select Top only.\n'
        'Copper, mask, silkscreen, outline and drill files are PCB references.\n'
        'Do not generate extra apertures from copper, mask or other components.\n'
        'PCB outline is an alignment reference, not a stencil aperture or foil cutout.\n'
        'Order as a separate SMT stencil, not as PCB fabrication or PCBA.\n'
        'Stencil outline/dimensions and thickness follow the stencil order settings.\n'
    )
    files['STENCIL-README.txt'] = note.encode()
    target = directory / 'BL54L15-Custom-Stencil-JLC.zip'
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(files.items()):
            assert Path(name).name == name
            archive.writestr(name, data)
    with zipfile.ZipFile(target) as archive:
        assert archive.testzip() is None
        assert archive.read(top[0]) == paste
        assert len(archive.namelist()) == 14
    return target


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    args = parser.parse_args()
    print(package_module_stencil(args.directory).resolve())
