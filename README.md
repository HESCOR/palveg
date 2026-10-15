# PALVEG 2.0 — static port

[![GitHub Org](https://img.shields.io/badge/GitHub-HESCOR-blue?logo=github&logoColor=white)](https://github.com/HESCOR)

A browser-only port of [PALVEG 2.0](https://oakern.shinyapps.io/palveg_v2/), retaining its interface, map appearance, zooming, grid cells, site popups, and legends.

> Work in progress: the full scenario matrix is being exported. Pages deployment stays disabled until all 2,912 files pass validation.

## Static architecture

The interface has 26 time steps (20–70 ka BP, every 2 ka), four reconstruction methods, and three display modes. Absolute and standardized views each require 104 scenarios; anomalies require 2,704 ordered date comparisons. The complete matrix contains **2,912 distinct scenarios**. Changing the reference date in a single-time-step mode does not require another file.

Each scenario is an independently loaded, gzip-compressed JSON file containing the original Leaflet layer instructions. Shared country geometry is stored once. The page downloads only the selected scenario, keeps the 12 most recently visited scenarios in memory, and aborts obsolete requests during fast control changes. All JavaScript, CSS, raster images, and geographic layers are local static assets.

**There is no R or Shiny server, map API, API key, runtime model calculation, or external CDN request.** GitHub Pages serves the files directly. Browsers decompress the scenario files locally using `DecompressionStream`.

The scientific outputs are exported directly from the public app. Anomalies are not recomputed from rounded popup values, and colours are not inferred from screenshots. The original EPSG:3857 projection, layer ordering, raster sampling, opacity, popup strings, legend gradients, and fit bounds are preserved. The original page reserves an empty 400 px plot area; the running source app returned no plot there, so that space is retained.

The existing Leaflet 1.3.1 canvas teardown is guarded against a pending animation callback during fast map changes. No vendored library code is modified.

## Local preview

```sh
python3 -m http.server 4174
```

Open http://localhost:4174/. A modern browser with `DecompressionStream` support is required.

## Export and validation

To export or resume the public layer snapshots:

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install playwright
playwright install chromium
python scripts/export_layers.py
```

Alternatively pass `--browser /usr/bin/chromium`. The exporter skips existing files and waits for each Shiny output to finish. The source service must be available during export only. It may take time to start and has intermittently returned “The application failed to start — signal: killed”; rerunning the exporter resumes without discarding completed work.

`assets/data/manifest.json` records each scenario's size and SHA-256 hash. Validate the complete matrix with:

```sh
python3 scripts/check.py
```

The GitHub Pages workflow runs that check before publishing. It refuses to deploy an incomplete matrix.

## Attribution

The original author credits, manuscript title, method citations, and contact details remain in the interface. See [THIRD_PARTY.md](THIRD_PARTY.md) for dependency licences and scientific provenance. The underlying reconstruction data and Shiny source were not supplied for this port.
