(function () {
  const buttons = document.querySelectorAll('[data-toggle-map]');
  if (!buttons.length) {
    return;
  }

  const defaultCenter = [-4.325, 15.313];
  const defaultZoom = 6;
  const mapInstances = new Map();

  function parseGeometry(data) {
    if (!data) {
      return null;
    }
    try {
      let parsed = data;
      for (let i = 0; i < 2; i += 1) {
        if (typeof parsed === 'string') {
          parsed = JSON.parse(parsed);
        }
      }
      if (!parsed || (typeof parsed === 'object' && Object.keys(parsed).length === 0)) {
        return null;
      }
      if (parsed.type === 'FeatureCollection') {
        return parsed;
      }
      if (parsed.type === 'Feature') {
        return parsed.geometry || null;
      }
      if (parsed.geometry && parsed.geometry.type) {
        return parsed.geometry;
      }
      if (parsed.type && parsed.coordinates) {
        return parsed;
      }
      return parsed;
    } catch (error) {
      return null;
    }
  }

  function readJsonScript(id) {
    const el = document.getElementById(id);
    if (!el) {
      return null;
    }
    try {
      return JSON.parse(el.textContent);
    } catch (error) {
      return null;
    }
  }

  function normalizeGeoJson(payload, label) {
    if (!payload) {
      return null;
    }
    if (payload.type === 'FeatureCollection' || payload.type === 'Feature') {
      return payload;
    }
    return {
      type: 'Feature',
      properties: { label: label || '' },
      geometry: payload,
    };
  }

  function initMap(container) {
    if (!container || mapInstances.has(container.id)) {
      return;
    }

    if (typeof L === 'undefined') {
      container.innerHTML = '<p style="padding:0.8rem">Carte indisponible.</p>';
      return;
    }

    const requestId = container.dataset.requestId;
    const proposedRaw = readJsonScript(`proposed-geometry-${requestId}`) || container.dataset.proposed;
    const currentRaw = readJsonScript(`current-geometry-${requestId}`) || container.dataset.current;
    const proposed = parseGeometry(proposedRaw);
    const current = parseGeometry(currentRaw);
    if (!proposed && !current) {
      container.innerHTML = '<p style="padding:0.8rem">Aucune geometrie disponible.</p>';
      return;
    }

    const map = L.map(container, { zoomControl: true, minZoom: 4 }).setView(defaultCenter, defaultZoom);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 18,
      attribution: '&copy; OpenStreetMap contributors',
    }).addTo(map);

    const group = L.featureGroup().addTo(map);

    if (current) {
      L.geoJSON(normalizeGeoJson(current, 'Actuel'), {
        style: { color: '#94a3b8', weight: 3, opacity: 0.85 },
        pointToLayer: (_, latlng) =>
          L.circleMarker(latlng, {
            radius: 7,
            fillColor: '#94a3b8',
            color: '#94a3b8',
            weight: 1,
            fillOpacity: 0.7,
          }),
      }).addTo(group);
    }

    if (proposed) {
      L.geoJSON(normalizeGeoJson(proposed, 'Propose'), {
        style: { color: '#2563eb', weight: 3, opacity: 0.95 },
        pointToLayer: (_, latlng) =>
          L.circleMarker(latlng, {
            radius: 8,
            fillColor: '#2563eb',
            color: '#2563eb',
            weight: 1,
            fillOpacity: 0.85,
          }),
      }).addTo(group);
    }

    if (group.getLayers().length === 0) {
      container.innerHTML = '<p style="padding:0.8rem">Aucune geometrie disponible.</p>';
      return;
    }

    map.fitBounds(group.getBounds(), { padding: [20, 20] });
    setTimeout(() => map.invalidateSize(), 120);
    mapInstances.set(container.id, map);
  }

  buttons.forEach((button) => {
    button.addEventListener('click', () => {
      const targetId = button.dataset.target;
      const container = document.getElementById(targetId);
      if (!container) {
        return;
      }
      const isHidden = container.classList.contains('is-hidden');
      container.classList.toggle('is-hidden');
      if (isHidden) {
        initMap(container);
      } else if (mapInstances.has(container.id)) {
        const map = mapInstances.get(container.id);
        setTimeout(() => map.invalidateSize(), 120);
      }
    });
  });
})();
