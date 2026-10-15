"""Export PALVEG's public Leaflet output without approximating its calculations.

Requires playwright (pip install playwright; playwright install chromium).
Use --browser /usr/bin/chromium to use an installed browser.
Exports are resumable. Each request waits for Shiny's output and idle state.
"""
import argparse
import copy
import gzip
import hashlib
import json
from pathlib import Path
import time
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'https://oakern.shinyapps.io/palveg_v2/'
METHODS = ['REVEALS', 'Biomisation', 'JSBACH', 'PaleoVeg']
MODES = {'standardized': 'standardized (Z-scores)', 'absolute': 'absolute forest cover', 'anomaly': 'forest-cover anomaly'}
AGES = list(range(20000, 70001, 2000))

def encode(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode()

def store_map(value, destination):
    value = copy.deepcopy(value)
    # JSON transport replaces CRS methods with null after browser rendering;
    # keep the same EPSG:3857 projection via Leaflet's supported CRS descriptor.
    value['options']['crs'] = {'crsClass': 'L.CRS.EPSG3857'}
    for call in value['calls']:
        if call['method'] == 'addPolygons':
            geometry = encode(call['args'][0])
            common = ROOT / 'assets/data/world.json'
            if common.exists():
                assert common.read_bytes() == geometry, 'Unexpected basemap geometry change'
            else:
                common.write_bytes(geometry)
            call['args'][0] = {'$ref': 'world'}
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix('.tmp')
    temporary.write_bytes(gzip.compress(encode(value), mtime=0))
    temporary.replace(destination)

def key(method, mode, age, age2=20000):
    suffix = f'-{age2}' if mode == 'anomaly' else ''
    return f'{method}/{mode}-{age}{suffix}'

def jobs():
    # Export all single-time-step views before the larger comparison matrix.
    for mode in ['standardized', 'absolute', 'anomaly']:
        for method in METHODS:
            for age2 in (AGES if mode == 'anomaly' else [20000]):
                for age in AGES:
                    yield method, mode, age, age2

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--browser')
    parser.add_argument('--url', default=SOURCE)
    parser.add_argument('--method', action='append', choices=METHODS)
    parser.add_argument('--mode', action='append', choices=list(MODES))
    args = parser.parse_args()
    folder = ROOT / 'assets/data'
    folder.mkdir(parents=True, exist_ok=True)
    done = sum((folder / (key(*job) + '.json.gz')).exists() for job in jobs())
    print(f'Starting at {done}/2912 exported scenarios', flush=True)
    if done == 2912:
        from write_manifest import main as write_manifest
        write_manifest()
        print('The complete matrix is already present; no source connection needed.', flush=True)
        return
    started = time.monotonic()
    with sync_playwright() as playwright:
        options = {'headless': True}
        if args.browser:
            options['executable_path'] = args.browser
        browser = playwright.chromium.launch(**options)
        page = browser.new_page(viewport={'width': 1920, 'height': 1400}, device_scale_factor=1)
        print('Loading source app...', flush=True)
        page.goto(args.url, wait_until='domcontentloaded', timeout=120000)
        print('Source HTML loaded; waiting for initial map...', flush=True)
        page.wait_for_function('window.Shiny?.shinyapp?.$values?.map || document.body.innerText.includes("failed to start")', timeout=120000)
        if not page.evaluate('Boolean(window.Shiny?.shinyapp?.$values?.map)'):
            message = page.locator('body').inner_text()
            raise RuntimeError(f'Source app unavailable: {message}')
        page.wait_for_function('!document.documentElement.classList.contains("shiny-busy")', timeout=120000)
        print('Initial map received.', flush=True)
        page.evaluate('''() => {
            window.__outputs = []; window.__errors = [];
            $(document).on('shiny:value', event => window.__outputs.push(event.name));
            $(document).on('shiny:error', event => window.__errors.push({name:event.name,error:event.error}));
            // Rendering thousands of invisible popup targets is unnecessary
            // during export. Shiny still receives every output normally.
            HTMLWidgets.find('#map').renderValue = () => {};
        }''')
        for method, mode, age, age2 in jobs():
            if args.method and method not in args.method:
                continue
            if args.mode and mode not in args.mode:
                continue
            destination = folder / (key(method, mode, age, age2) + '.json.gz')
            if destination.exists():
                continue
            selected = {'data': method, 'scale': MODES[mode], 'age': age, 'age2': age2}
            current = page.evaluate('Shiny.shinyapp.$inputValues')
            if any(current.get(k) != v for k, v in selected.items()):
                page.evaluate('''selected => {
                    window.__outputs = []; window.__errors = [];
                    for (const [name,value] of Object.entries(selected)) Shiny.setInputValue(name,value);
                }''', selected)
                page.wait_for_function('''() => (window.__outputs.includes('map') || window.__errors.some(e=>e.name==='map'))
                    && !document.documentElement.classList.contains('shiny-busy')''', timeout=180000)
                errors = page.evaluate('window.__errors')
                if errors:
                    raise RuntimeError(f'{selected}: {errors}')
            # A single-time-step output is independent of reference time.
            actual = page.evaluate('Shiny.shinyapp.$inputValues')
            assert all(actual.get(k) == v for k, v in selected.items()), actual
            value = page.evaluate('Shiny.shinyapp.$values.map.x')
            assert any(c['method'] == 'addLegend' for c in value['calls']), selected
            store_map(value, destination)
            done += 1
            if done % 20 == 0 or done == 2912:
                print(f'{done}/2912 | {key(method, mode, age, age2)} | {time.monotonic()-started:.1f}s elapsed', flush=True)
        browser.close()
    manifest = []
    for job in jobs():
        path = folder / (key(*job) + '.json.gz')
        if not path.exists():
            continue
        manifest.append({'key': key(*job), 'bytes': path.stat().st_size,
                         'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    (folder / 'manifest.json').write_text(json.dumps({
        'source': SOURCE, 'exported': time.strftime('%Y-%m-%d'), 'scenarios': manifest,
        'methods': METHODS, 'modes': MODES, 'ages': AGES,
        'provenance': 'Original Leaflet calls, exact colours and popup strings; shared world geometry stored once.',
    }, indent=2) + '\n')
    print(f'Export pass complete: {len(manifest)}/2912 scenarios stored.', flush=True)

if __name__ == '__main__':
    main()
