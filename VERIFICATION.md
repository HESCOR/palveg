# Verification

Checks performed on 15 October 2026 with Chromium 154 on Ubuntu, using a local static HTTP server and a 1920 × 1400 viewport.

- The original default Shiny page and the static default page produced pixel-identical full-page screenshots (1920 × 1575; no differing pixels).
- All 208 single-date scenarios were selected through the page controls and rendered successfully, with no JavaScript errors. Slider changes had a local median of 140 ms including the 120 ms drag debounce.
- Twelve samples spanning all four reconstruction methods and all three display modes had popup arrays identical to the source app's original Leaflet output. Popups and zoom controls worked.
- Dropdown sample switches, after removing their unnecessary debounce, took about 20–86 ms locally, measured from control change to active layer state. These are local measurements; first downloads depend on network latency.
- Same-date zero anomalies use the original colour with a single zero swatch, avoiding the source app’s invalid `NaN` gradient.
- Rapid switching, delayed responses, and returning to an already displayed scenario during an in-flight request were checked to prevent stale results replacing the selected view.
- All requests in the browser checks stayed on the static site's origin. No Shiny, map API, external tile service, or CDN request was made.
- Both raw `.json.gz` responses and HTTP `Content-Encoding: gzip` responses were checked. The default screenshot remained identical.

`python scripts/check.py` validates the complete 2,912-file matrix, hashes, date labels, projection, and layer structure before deployment. `scripts/browser_check.py` contains reproducible browser checks. The GitHub Actions deployment is gated on a complete matrix; partial exports cannot be published by that workflow.
