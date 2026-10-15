'use strict';
(() => {
  // Leaflet 1.3.1 can leave a canvas redraw scheduled when a map is removed.
  // Cancel it before disposing the renderer during fast scenario changes.
  const destroyCanvas = L.Canvas.prototype._destroyContainer;
  L.Canvas.include({
    _destroyContainer() {
      L.Util.cancelAnimFrame(this._redrawRequest);
      this._redrawRequest = null;
      return destroyCanvas.call(this);
    },
  });
  const status = document.querySelector('#status');
  const mapElement = document.querySelector('#map');
  const scales = {
    'standardized (Z-scores)': 'standardized',
    'absolute forest cover': 'absolute',
    'forest-cover anomaly': 'anomaly',
  };
  const cache = new Map();
  let generation = 0;
  let timer;
  let activeKey;
  let activeRequest;
  let widget;
  const world = fetch('assets/data/world.json').then(response => {
    if (!response.ok) throw new Error('The basemap could not be loaded.');
    return response.json();
  });

  async function loadScenario(key, signal) {
    if (cache.has(key)) {
      const value = cache.get(key);
      cache.delete(key);
      cache.set(key, value);
      return value;
    }
    const response = await fetch(`assets/data/${key}.json.gz`, {signal});
    if (!response.ok) throw new Error('The selected reconstruction could not be loaded. Please try again.');
    // GitHub Pages serves .gz as a file. Decode the compact layer data locally.
    const stream = response.body.pipeThrough(new DecompressionStream('gzip'));
    const value = await new Response(stream).json();
    cache.set(key, value);
    if (cache.size > 12) cache.delete(cache.keys().next().value);
    return value;
  }

  function selectedKey() {
    const method = document.querySelector('#data').value;
    const mode = scales[document.querySelector('#scale').value];
    const age = $('#age').data('ionRangeSlider').result.from;
    const age2 = $('#age2').data('ionRangeSlider').result.from;
    return `${method}/${mode}-${age}${mode === 'anomaly' ? `-${age2}` : ''}`;
  }

  async function update() {
    const key = selectedKey();
    if (key === activeKey) return;
    const current = ++generation;
    activeRequest?.abort();
    activeRequest = new AbortController();
    mapElement.setAttribute('aria-busy', 'true');
    status.hidden = true;
    try {
      const [stored, geometry] = await Promise.all([loadScenario(key, activeRequest.signal), world]);
      if (current !== generation) return;
      const data = structuredClone(stored);
      for (const call of data.calls) {
        if (call.method === 'addPolygons' && call.args[0].$ref === 'world') call.args[0] = geometry;
      }
      // The original Leaflet renderer preserves map geometry, colours, legends,
      // popup text, projection, panes and fit bounds from the Shiny output.
      widget.renderValue(data);
      activeKey = key;
      mapElement.dataset.scenario = key;
      mapElement.removeAttribute('aria-busy');
      mapElement.dispatchEvent(new CustomEvent('scenariochange', {detail: {key}}));
    } catch (error) {
      if (current !== generation || error.name === 'AbortError') return;
      mapElement.removeAttribute('aria-busy');
      status.textContent = `${error.message} Check your connection and change a control to retry.`;
      status.hidden = false;
      console.error(error);
    }
  }

  function schedule() {
    clearTimeout(timer);
    timer = setTimeout(update, 120);
  }

  $(() => {
    HTMLWidgets.staticRender();
    widget = HTMLWidgets.find('#map');
    $('.js-range-slider').ionRangeSlider({onChange: schedule});
    $('#data, #scale').selectize({plugins: ['selectize-plugin-a11y'], onChange: schedule});
    update();
  });
})();
