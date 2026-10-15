"""Record checksums for exported snapshots, including incomplete checkpoints."""
from pathlib import Path
import gzip
import hashlib
import json
from datetime import date

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'assets/data'

def main():
    records = []
    for path in sorted(DATA.glob('*/*.json.gz')):
        raw = path.read_bytes()
        value = json.loads(gzip.decompress(raw))
        assert value['calls'], path
        records.append({'key': str(path.relative_to(DATA))[:-8], 'bytes': len(raw),
                        'sha256': hashlib.sha256(raw).hexdigest()})
    result = {
        'source': 'https://oakern.shinyapps.io/palveg_v2/',
        'exported': str(date.today()),
        'expectedScenarios': 2912,
        'scenarios': records,
        'methods': ['REVEALS', 'Biomisation', 'JSBACH', 'PaleoVeg'],
        'modes': {'standardized': 'standardized (Z-scores)', 'absolute': 'absolute forest cover', 'anomaly': 'forest-cover anomaly'},
        'ages': list(range(20000, 70001, 2000)),
        'provenance': 'Original Leaflet calls, exact colours and popup strings; shared world geometry stored once.',
    }
    (DATA / 'manifest.json').write_text(json.dumps(result, indent=2) + '\n')
    print(f'Manifest: {len(records)}/2912 scenarios')

if __name__ == '__main__':
    main()
