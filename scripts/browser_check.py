"""Browser acceptance checks for the static port (requires playwright).

Run a local HTTP server first, then:
python scripts/browser_check.py --url http://localhost:4174/ --browser /usr/bin/chromium
"""
import argparse
import gzip
import json
from pathlib import Path
from time import perf_counter
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', default='http://localhost:4174/')
    parser.add_argument('--browser')
    args = parser.parse_args()
    origin = urlsplit(args.url).netloc
    with sync_playwright() as playwright:
        options = {'headless': True}
        if args.browser:
            options['executable_path'] = args.browser
        browser = playwright.chromium.launch(**options)
        page = browser.new_page(viewport={'width': 1920, 'height': 1400}, device_scale_factor=1)
        errors = []
        requests = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.on('request', lambda request: requests.append(request.url))
        page.goto(args.url, wait_until='networkidle')
        page.wait_for_function('document.querySelector("#map").dataset.scenario')
        page.evaluate("$('#age2').data('ionRangeSlider').update({from:70000})")
        timings = []
        for method in ['REVEALS', 'Biomisation', 'JSBACH', 'PaleoVeg']:
            for mode, label in [('standardized', 'standardized (Z-scores)'), ('absolute', 'absolute forest cover'), ('anomaly', 'forest-cover anomaly')]:
                key = f'{method}/{mode}-20000' + ('-70000' if mode == 'anomaly' else '')
                start = perf_counter()
                page.evaluate('''([method, mode]) => {
                    $('#data')[0].selectize.setValue(method);
                    $('#scale')[0].selectize.setValue(mode);
                }''', [method, label])
                page.wait_for_function('key => document.querySelector("#map").dataset.scenario === key', arg=key)
                timings.append({'key': key, 'ms': round(1000 * (perf_counter() - start))})
                stored = json.loads(gzip.decompress((ROOT / f'assets/data/{key}.json.gz').read_bytes()))
                call = next(c for c in stored['calls'] if c['method'] in ['addCircleMarkers', 'addRectangles'])
                expected = call['args'][8 if call['method'] == 'addCircleMarkers' else 7]
                actual = page.evaluate('''() => Object.values(HTMLWidgets.find('#map').getMap()._layers)
                    .filter(layer => layer._popup).map(layer => layer._popup._content)''')
                assert actual == expected, f'{key}: popup mismatch'
                page.evaluate('''() => {
                    const map = HTMLWidgets.find('#map').getMap();
                    Object.values(map._layers).find(layer => layer._popup).openPopup();
                }''')
                assert page.locator('.leaflet-popup-content').count() == 1, key
                page.evaluate("HTMLWidgets.find('#map').getMap().closePopup()")
        # The source's constant-zero numeric gradient contains NaN. Display
        # its original colour and zero label without an invalid SVG gradient.
        page.evaluate("$('#data')[0].selectize.setValue('REVEALS'); const slider=$('#age2').data('ionRangeSlider'); slider.update({from:20000}); slider.options.onChange(slider.result)")
        page.wait_for_function('document.querySelector("#map").dataset.scenario === "REVEALS/anomaly-20000-20000"')
        assert page.locator('.leaflet-bottom.leaflet-right .legend i').count() == 1
        assert page.locator('.leaflet-bottom.leaflet-right .legend svg').count() == 0
        page.evaluate("const slider=$('#age2').data('ionRangeSlider'); slider.update({from:70000}); slider.options.onChange(slider.result)")
        page.wait_for_function('document.querySelector("#map").dataset.scenario === "REVEALS/anomaly-20000-70000"')
        zoom = page.evaluate("HTMLWidgets.find('#map').getMap().getZoom()")
        page.locator('.leaflet-control-zoom-in').click()
        page.wait_for_function('zoom => HTMLWidgets.find("#map").getMap().getZoom() === zoom + 1', arg=zoom)
        # Change through several methods before the debounce fires; the last wins.
        page.evaluate('''() => {
            for (const method of ['JSBACH', 'REVEALS', 'Biomisation']) $('#data')[0].selectize.setValue(method);
        }''')
        page.wait_for_function('document.querySelector("#map").dataset.scenario === "Biomisation/anomaly-20000-70000"')
        # A slow old response must not overwrite a newer selected scenario.
        race = browser.new_page(viewport={'width': 1920, 'height': 1400})
        race.on('pageerror', lambda error: errors.append(str(error)))
        race.add_init_script("""(() => {
            const original = window.fetch.bind(window);
            window.fetch = async (...args) => {
                const response = await original(...args);
                if (String(args[0]).includes('PaleoVeg/absolute-20000')) {
                    window.slowRequestStarted = true;
                    await new Promise(resolve => setTimeout(resolve, 600));
                }
                return response;
            };
        })()""")
        race.goto(args.url, wait_until='networkidle')
        race.wait_for_function('document.querySelector("#map").dataset.scenario')
        race.evaluate("$('#data')[0].selectize.setValue('PaleoVeg'); $('#scale')[0].selectize.setValue('absolute forest cover')")
        race.wait_for_function('window.slowRequestStarted === true')
        race.evaluate("$('#data')[0].selectize.setValue('JSBACH')")
        race.wait_for_function('document.querySelector("#map").dataset.scenario === "JSBACH/absolute-20000"')
        race.wait_for_timeout(700)
        assert race.locator('#map').get_attribute('data-scenario') == 'JSBACH/absolute-20000'
        # Returning to the already displayed view must cancel an in-flight load.
        race.evaluate("$('#data')[0].selectize.setValue('PaleoVeg')")
        race.wait_for_function('document.querySelector("#map").getAttribute("aria-busy") === "true"')
        race.evaluate("$('#data')[0].selectize.setValue('JSBACH')")
        race.wait_for_function('document.querySelector("#map").getAttribute("aria-busy") !== "true"')
        race.wait_for_timeout(700)
        assert race.locator('#map').get_attribute('data-scenario') == 'JSBACH/absolute-20000'
        race.close()
        external = [url for url in requests if urlsplit(url).netloc != origin]
        assert not errors, errors
        assert not external, external
        print(json.dumps({'scenarioTimings': timings, 'popupFidelity': 'passed', 'zeroAnomalyLegend': 'passed', 'zoom': 'passed',
                          'rapidSwitching': 'passed', 'staleResponseProtection': 'passed', 'javascriptErrors': errors, 'externalRequests': external}, indent=2))
        browser.close()


if __name__ == '__main__':
    main()
