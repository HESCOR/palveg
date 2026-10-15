"""Check the full static PALVEG scenario matrix and layer integrity."""
from pathlib import Path
import gzip
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'assets/data'
AGES = range(20000, 70001, 2000)
METHODS = ['REVEALS', 'Biomisation', 'JSBACH', 'PaleoVeg']
ALLOWED = {'createMapPane', 'addRasterImage', 'addPolygons', 'addCircleMarkers', 'addRectangles', 'addLegend', 'addControl'}

def main():
    manifest = json.loads((DATA / 'manifest.json').read_text())
    records = {r['key']: r for r in manifest['scenarios']}
    assert len(records) == 2912, f'Export incomplete: {len(records)}/2912 maps saved; {2912-len(records)} remaining. Resume the export workflow; completed files are retained.'
    world = json.loads((DATA / 'world.json').read_text())
    assert world, 'Empty basemap'
    count = 0
    for method in METHODS:
        for mode in ['standardized', 'absolute', 'anomaly']:
            for reference in (AGES if mode == 'anomaly' else [None]):
                for age in AGES:
                    key = f'{method}/{mode}-{age}' + (f'-{reference}' if reference else '')
                    path = DATA / f'{key}.json.gz'
                    data = path.read_bytes()
                    assert hashlib.sha256(data).hexdigest() == records[key]['sha256'], key
                    value = json.loads(gzip.decompress(data))
                    assert value['fitBounds'][:4] == [30.5, -5.5, 60.5, 40.5], key
                    assert value['options']['crs']['crsClass'] == 'L.CRS.EPSG3857', key
                    legend = next(c['args'][0] for c in value['calls'] if c['method'] == 'addLegend')
                    dates = [int(n) for n in re.findall(r'(\d+) ka BP', legend['title'])]
                    assert dates == ([age // 1000, reference // 1000] if reference else [age // 1000]), (key, dates)
                    methods = {call['method'] for call in value['calls']}
                    assert methods <= ALLOWED, (key, methods)
                    assert {'addPolygons', 'addLegend', 'addControl'} <= methods, key
                    assert methods & {'addCircleMarkers', 'addRectangles'}, key
                    for call in value['calls']:
                        if call['method'] == 'addPolygons':
                            assert call['args'][0] == {'$ref': 'world'}, key
                        if call['method'] == 'addRasterImage':
                            assert call['args'][0].startswith('data:image/png;base64,'), key
                    count += 1
    print(f'Checked {count} static scenarios: complete matrix, checksums, projection and layer structure.')

if __name__ == '__main__':
    main()
