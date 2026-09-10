"""Add the approved sprout as grouped F.SilkS rectangles through KiCad IPC.

Run from the project root with kicad-python and Pillow installed.
"""
from pathlib import Path
import json
from PIL import Image
from kipy import KiCad
from kipy.board_types import BoardRectangle, Group
from kipy.common_types import Vector2

OUT = Path('output/sprout-silkscreen')
NAME = 'Leafy sprout radio artwork'
board = KiCad('ipc:///tmp/kicad/api.sock').get_board()
assert board.name == 'nrf-moisture-sensor.kicad_pcb'
assert not any(g.name == NAME for g in board.get_groups()), 'Artwork already present'
mask = Image.open(OUT / 'ink-mask.png').convert('L')
assert mask.size == (56, 72)

# Merge identical horizontal runs on consecutive rows into solid rectangles.
rectangles = []
active = {}
for y in range(mask.height + 1):
    runs = []
    x = 0
    while y < mask.height and x < mask.width:
        if mask.getpixel((x, y)) < 128:
            x += 1
            continue
        start = x
        while x < mask.width and mask.getpixel((x, y)) >= 128:
            x += 1
        runs.append((start, x))
    for run in list(active):
        if run not in runs:
            rectangles.append((run[0], active.pop(run), run[1], y))
    for run in runs:
        active.setdefault(run, y)

layer = board.get_layer_by_name('F.SilkS')
shapes = []
for x1, y1, x2, y2 in rectangles:
    shape = BoardRectangle()
    shape.layer = layer
    shape.top_left = Vector2.from_xy_mm(70 + x1 * .25, 119 + y1 * .25)
    shape.bottom_right = Vector2.from_xy_mm(70 + x2 * .25, 119 + y2 * .25)
    shape.attributes.fill.filled = True
    shape.attributes.stroke.width = 0
    shapes.append(shape)

commit = board.begin_commit()
try:
    created = board.create_items(shapes)
    assert len(created) == len(shapes)
    group = Group()
    group.proto.name = NAME
    group.items = created
    result = board.create_items(group)
    assert len(result) == 1
    board.push_commit(commit, 'Add leafy sprout radio artwork to F.SilkS')
except Exception:
    board.drop_commit(commit)
    raise
board.save()
(OUT / 'artwork-items.json').write_text(json.dumps({
    'group': result[0].id.value,
    'rectangles': [s.id.value for s in created],
    'layer': 'F.SilkS', 'bounds_mm': [70, 119, 84, 137],
    'pixel_pitch_mm': .25,
}, indent=2) + '\n')
board.set_active_layer(layer)
print(f'Added {len(created)} rectangles in one group; saved {board.name}')
