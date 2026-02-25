(function () {
  const mapContainer = document.getElementById('national-map');
  if (!mapContainer) {
    return;
  }

  const apiUrl = mapContainer.dataset.apiUrl;
  const defaultLayer = mapContainer.dataset.defaultLayer;
  const detail = document.getElementById('feature-details');

  if (typeof L === 'undefined') {
    mapContainer.innerHTML = '<p style="padding:1rem">Impossible de charger la librairie cartographique.</p>';
    return;
  }

  const colorByLayer = {
    electricite: '#f97316',
    'eau-assainissement': '#3b82f6',
    'fibre-telecom': '#0ea5a4',
    voirie: '#64748b',
    'caniveaux-drainage': '#16a34a',
  };

  const map = L.map('national-map', {
    zoomControl: true,
    minZoom: 5,
  }).setView([-4.325, 15.313], 6);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 18,
    attribution: '&copy; OpenStreetMap contributors',
  }).addTo(map);

  const geoLayer = L.geoJSON([], {
    pointToLayer: (feature, latlng) => {
      const layerKey = feature?.properties?.layer_key;
      const color = colorByLayer[layerKey] || '#1464f4';
      return L.circleMarker(latlng, {
        radius: 7,
        fillColor: color,
        color,
        weight: 1,
        fillOpacity: 0.8,
      });
    },
    style: (feature) => ({
      color: colorByLayer[feature?.properties?.layer_key] || '#1464f4',
      weight: 3,
      opacity: 0.9,
    }),
    onEachFeature: (feature, layer) => {
      layer.on('click', () => {
        renderDetails(feature.properties || {});
      });
    },
  }).addTo(map);

  function renderDetails(properties) {
    const rows = Object.entries(properties)
      .filter(([key]) => key !== 'layer_key')
      .map(([key, value]) => `<dt>${key}</dt><dd>${String(value)}</dd>`)
      .join('');
    detail.innerHTML = `<h3>Fiche technique</h3><dl>${rows || '<dd>Aucun attribut</dd>'}</dl>`;
  }

  function getFilters() {
    const params = new URLSearchParams();
    const search = document.getElementById('map-search')?.value?.trim();
    const province = document.getElementById('map-province')?.value?.trim();
    const city = document.getElementById('map-city')?.value?.trim();
    const axis = document.getElementById('map-axis')?.value?.trim();
    const layer = document.getElementById('map-layer')?.value?.trim();

    if (search) params.set('q', search);
    if (province) params.set('province', province);
    if (city) params.set('city', city);
    if (axis) params.set('axis', axis);
    if (layer) params.set('layer', layer);

    return params;
  }

  async function loadFeatures() {
    const params = getFilters();
    mapContainer.classList.add('is-loading');
    try {
      const response = await fetch(`${apiUrl}?${params.toString()}`);
      const payload = await response.json();
      geoLayer.clearLayers();
      geoLayer.addData(payload);
      if (geoLayer.getLayers().length > 0) {
        map.fitBounds(geoLayer.getBounds(), { padding: [20, 20] });
      }
    } catch (error) {
      detail.innerHTML = '<h3>Fiche technique</h3><p>Echec du chargement des donnees cartographiques.</p>';
    } finally {
      mapContainer.classList.remove('is-loading');
    }
  }

  document.getElementById('apply-map-filters')?.addEventListener('click', loadFeatures);
  document.getElementById('reset-map-filters')?.addEventListener('click', () => {
    ['map-search', 'map-province', 'map-city', 'map-axis'].forEach((id) => {
      const element = document.getElementById(id);
      if (element) element.value = '';
    });
    const layerSelect = document.getElementById('map-layer');
    if (layerSelect) {
      layerSelect.value = defaultLayer || '';
    }
    loadFeatures();
  });

  if (defaultLayer) {
    const layerSelect = document.getElementById('map-layer');
    if (layerSelect) {
      layerSelect.value = defaultLayer;
    }
  }

  loadFeatures();
})();
