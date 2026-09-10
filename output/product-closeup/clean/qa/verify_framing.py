import runpy
from pathlib import Path
source = Path('/Users/alex/moisture-sensor-carrier/output/product-closeup/source/verify_2k60.py')
# Redirect the existing geometry/framing report into this new render revision.
exec(compile(source.read_text(), str(source), 'exec'), {'__file__': str(Path(__file__).resolve().parent / 'verify_2k60.py')})
