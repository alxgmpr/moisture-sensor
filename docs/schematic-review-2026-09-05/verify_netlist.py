"""Compare exported connectivity and symbol pin identities, ignoring page placement."""
from pathlib import Path
import json
import xml.etree.ElementTree as ET
here = Path(__file__).resolve().parent
before, after = [ET.parse(here / stage / 'netlist.xml') for stage in ('before', 'after')]
def nets(tree):
    return {net.attrib['name']: sorted((node.attrib['ref'], node.attrib['pin'])
            for node in net.findall('node')) for net in tree.findall('./nets/net')}
def pins(tree):
    return {(part.attrib['lib'], part.attrib['part']): sorted(tuple(sorted(pin.attrib.items()))
            for pin in part.findall('./pins/pin')) for part in tree.findall('./libparts/libpart')}
def components(tree):
    return {part.attrib['ref']: (part.findtext('value'), part.findtext('footprint'))
            for part in tree.findall('./components/comp')}
result = {'net_connectivity_equal': nets(before) == nets(after),
          'symbol_pin_definitions_equal': pins(before) == pins(after),
          'component_values_and_footprints_equal': components(before) == components(after),
          'nets': len(nets(after)), 'components': len(components(after))}
assert all(result[key] for key in result if key.endswith('_equal')), result
(here / 'verification.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
