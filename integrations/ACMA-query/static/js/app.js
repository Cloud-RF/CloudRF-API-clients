(function () {
  "use strict";

  // ---------------------------------------------------------------------
  // Geo helpers (no external geo library needed)
  // ---------------------------------------------------------------------
  const EARTH_RADIUS_M = 6371000;

  /** Destination point given a start lat/lng, bearing (deg) and distance (m). */
  function destinationPoint(lat, lng, bearingDeg, distanceM) {
    const delta = distanceM / EARTH_RADIUS_M;
    const theta = (bearingDeg * Math.PI) / 180;
    const phi1 = (lat * Math.PI) / 180;
    const lambda1 = (lng * Math.PI) / 180;

    const phi2 = Math.asin(
      Math.sin(phi1) * Math.cos(delta) +
        Math.cos(phi1) * Math.sin(delta) * Math.cos(theta)
    );
    const lambda2 =
      lambda1 +
      Math.atan2(
        Math.sin(theta) * Math.sin(delta) * Math.cos(phi1),
        Math.cos(delta) - Math.sin(phi1) * Math.sin(phi2)
      );

    return {
      lat: (phi2 * 180) / Math.PI,
      lng: ((((lambda2 * 180) / Math.PI) + 540) % 360) - 180,
    };
  }

  /** Approximate a circle as a closed GeoJSON polygon ring. */
  function circleToPolygonCoords(centerLat, centerLng, radiusM, numPoints) {
    const ring = [];
    for (let i = 0; i <= numPoints; i++) {
      const bearing = (360 * i) / numPoints;
      const pt = destinationPoint(centerLat, centerLng, bearing, radiusM);
      ring.push([pt.lng, pt.lat]);
    }
    return ring;
  }

  // ---------------------------------------------------------------------
  // State
  // ---------------------------------------------------------------------
  const HANDLE_BEARING = 90; // handle sits due east of the center
  const RADIUS_MIN_M = 10_000; // 10 km
  const RADIUS_MAX_M = 500_000; // 500 km
  const RADIUS_DEFAULT_M = 50_000; // 50 km

  function clampRadiusM(metres) {
    return Math.min(RADIUS_MAX_M, Math.max(RADIUS_MIN_M, metres));
  }

  const state = {
    center: null, // {lat, lng}
    radius: RADIUS_DEFAULT_M, // metres (UI displays this in km)
  };

  // ---------------------------------------------------------------------
  // Map setup
  // ---------------------------------------------------------------------
  const map = L.map("map", { zoomControl: true }).setView([-25.2744, 133.7751], 4); // Australia

  const BASEMAPS = {
    osm: L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: "&copy; OpenStreetMap contributors",
    }),
    esriTopo: L.tileLayer(
      "https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
      { maxZoom: 19, attribution: "Tiles &copy; Esri" }
    ),
    esriSatellite: L.tileLayer(
      "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
      { maxZoom: 19, attribution: "Tiles &copy; Esri" }
    ),
  };

  let currentBasemapKey = null;

  function switchBasemap(key) {
    if (!BASEMAPS[key]) key = "osm";
    if (key === currentBasemapKey) return;
    if (currentBasemapKey && map.hasLayer(BASEMAPS[currentBasemapKey])) {
      map.removeLayer(BASEMAPS[currentBasemapKey]);
    }
    BASEMAPS[key].addTo(map);
    currentBasemapKey = key;
    try {
      localStorage.setItem("basemap", key);
    } catch (err) {
      // localStorage unavailable (private browsing, etc.) — not critical
    }
  }

  let savedBasemap = "osm";
  try {
    savedBasemap = localStorage.getItem("basemap") || "osm";
  } catch (err) {
    // ignore — default to osm
  }
  switchBasemap(savedBasemap);

  const circleLayer = L.circle([0, 0], {
    radius: state.radius,
    color: "#2563eb",
    weight: 2,
    fillColor: "#2563eb",
    fillOpacity: 0.15,
  });

  const centerMarker = L.marker([0, 0], { draggable: true });

  const handleIcon = L.divIcon({
    className: "",
    html: '<div class="radius-handle-icon"></div>',
    iconSize: [12, 12],
    iconAnchor: [6, 6],
  });
  const radiusHandle = L.marker([0, 0], { draggable: true, icon: handleIcon });

  const resultIcon = L.divIcon({
    className: "",
    html: '<div class="result-marker-icon"></div>',
    iconSize: [14, 14],
    iconAnchor: [7, 12],
    popupAnchor: [0, -10],
  });
  const resultsLayer = L.markerClusterGroup({ maxClusterRadius: 50 });
  resultsLayer.addTo(map);

  // ---------------------------------------------------------------------
  // DOM references
  // ---------------------------------------------------------------------
  const el = {
    app: document.getElementById("app"),
    sidebarToggle: document.getElementById("sidebarToggle"),
    lat: document.getElementById("latField"),
    lng: document.getElementById("lngField"),
    radiusNumber: document.getElementById("radiusNumber"),
    radiusSlider: document.getElementById("radiusSlider"),
    freqMinValue: document.getElementById("freqMinValue"),
    freqMinUnit: document.getElementById("freqMinUnit"),
    freqMaxValue: document.getElementById("freqMaxValue"),
    freqMaxUnit: document.getElementById("freqMaxUnit"),
    name: document.getElementById("nameField"),
    polygonMode: document.getElementById("polygonMode"),
    form: document.getElementById("shapeForm"),
    searchBtn: document.getElementById("searchBtn"),
    searchStatus: document.getElementById("searchStatus"),
    clearBtn: document.getElementById("clearBtn"),
    copyBtn: document.getElementById("copyBtn"),
    downloadBtn: document.getElementById("downloadBtn"),
    saveBtn: document.getElementById("saveBtn"),
    savedList: document.getElementById("savedList"),
    bandwidthChart: document.getElementById("bandwidthChart"),
    bandwidthChartTitle: document.getElementById("bandwidthChartTitle"),
    bandwidthChartClose: document.getElementById("bandwidthChartClose"),
    bandwidthChartBody: document.getElementById("bandwidthChartBody"),
    bwAxisMin: document.getElementById("bwAxisMin"),
    bwAxisMid: document.getElementById("bwAxisMid"),
    bwAxisMax: document.getElementById("bwAxisMax"),
    modelBtn: document.getElementById("modelBtn"),
    modelStatus: document.getElementById("modelStatus"),
    modelStatusText: document.getElementById("modelStatusText"),
    rfLayersSection: document.getElementById("rfLayersSection"),
    rfLayersClose: document.getElementById("rfLayersClose"),
    rfLayerList: document.getElementById("rfLayerList"),
    settingsBtn: document.getElementById("settingsBtn"),
    settingsBackdrop: document.getElementById("settingsBackdrop"),
    settingsClose: document.getElementById("settingsClose"),
    basemapRadios: document.querySelectorAll('input[name="basemap"]'),
    cloudrfKeyInput: document.getElementById("cloudrfKeyInput"),
    cloudrfKeyToggle: document.getElementById("cloudrfKeyToggle"),
    cloudrfKeyHint: document.getElementById("cloudrfKeyHint"),
    cloudrfKeySave: document.getElementById("cloudrfKeySave"),
    cloudrfKeyStatus: document.getElementById("cloudrfKeyStatus"),
  };

  // Search results currently on the map, in the same order used by the
  // bandwidth chart (chart bar data-index -> this array index).
  let currentResultItems = []; // [{feature, marker}]
  let selectedBarEl = null;

  // CloudRF coverage overlays currently on the map: [{id, overlay, li}]
  let rfLayers = [];

  // ---------------------------------------------------------------------
  // Core drawing / sync logic
  // ---------------------------------------------------------------------
  function hasShape() {
    return state.center !== null;
  }

  function placeShape(lat, lng, radius) {
    state.center = { lat, lng };
    state.radius = radius;

    centerMarker.setLatLng([lat, lng]);
    circleLayer.setLatLng([lat, lng]);
    circleLayer.setRadius(radius);

    if (!map.hasLayer(centerMarker)) centerMarker.addTo(map);
    if (!map.hasLayer(circleLayer)) circleLayer.addTo(map);
    if (!map.hasLayer(radiusHandle)) radiusHandle.addTo(map);

    snapHandleToEdge();
    syncFormFromState();
  }

  function snapHandleToEdge() {
    if (!state.center) return;
    const pt = destinationPoint(
      state.center.lat,
      state.center.lng,
      HANDLE_BEARING,
      state.radius
    );
    radiusHandle.setLatLng([pt.lat, pt.lng]);
  }

  function syncFormFromState() {
    if (!state.center) return;
    el.lat.value = state.center.lat.toFixed(6);
    el.lng.value = state.center.lng.toFixed(6);
    const km = state.radius / 1000;
    el.radiusNumber.value = Math.round(km * 100) / 100; // 2 decimal places
    el.radiusSlider.value = Math.round(clampRadiusM(state.radius) / 1000);
  }

  function buildGeoJSON() {
    if (!state.center) return null;
    const { lat, lng } = state.center;
    const radius = Math.round(state.radius);

    const properties = {
      name: el.name.value || undefined,
      radius,
    };

    if (el.polygonMode.checked) {
      properties.shape = "circle-polygon";
      return {
        type: "Feature",
        properties,
        geometry: {
          type: "Polygon",
          coordinates: [circleToPolygonCoords(lat, lng, radius, 64)],
        },
      };
    }

    properties.shape = "circle";
    return {
      type: "Feature",
      properties,
      geometry: {
        type: "Point",
        coordinates: [lng, lat],
      },
    };
  }

  function clearShape() {
    state.center = null;
    state.radius = clampRadiusM((Number(el.radiusNumber.value) || 50) * 1000);
    [centerMarker, circleLayer, radiusHandle].forEach((layer) => {
      if (map.hasLayer(layer)) map.removeLayer(layer);
    });
    el.lat.value = "";
    el.lng.value = "";
    resultsLayer.clearLayers();
    currentResultItems = [];
    selectedBarEl = null;
    el.bandwidthChart.hidden = true;
    el.bandwidthChartBody.innerHTML = "";
    setSearchStatus("");
    clearRfLayers();
  }

  // ---------------------------------------------------------------------
  // Map interactions
  // ---------------------------------------------------------------------
  map.on("click", (e) => {
    const km = Number(el.radiusNumber.value);
    const radius = clampRadiusM((Number.isFinite(km) && km > 0 ? km : state.radius / 1000) * 1000);
    placeShape(e.latlng.lat, e.latlng.lng, radius);
  });

  centerMarker.on("drag", (e) => {
    const { lat, lng } = e.target.getLatLng();
    state.center = { lat, lng };
    circleLayer.setLatLng([lat, lng]);
    snapHandleToEdge();
    syncFormFromState();
  });

  radiusHandle.on("drag", (e) => {
    if (!state.center) return;
    const handleLatLng = e.target.getLatLng();
    const centerLatLng = L.latLng(state.center.lat, state.center.lng);
    const newRadius = clampRadiusM(centerLatLng.distanceTo(handleLatLng));
    state.radius = newRadius;
    circleLayer.setRadius(newRadius);
    syncFormFromState();
  });

  radiusHandle.on("dragend", () => {
    // Snap the handle back onto the exact east point of the circle so it
    // stays a clean "grab here to resize" affordance.
    snapHandleToEdge();
  });

  // ---------------------------------------------------------------------
  // Form interactions
  // ---------------------------------------------------------------------
  /** value is metres; updates circle + form once a shape already exists. */
  function onRadiusInputChanged(value) {
    if (!hasShape()) {
      state.radius = value;
      return;
    }
    state.radius = value;
    circleLayer.setRadius(value);
    snapHandleToEdge();
  }

  // While the user is actively typing a km value, don't clamp/rewrite the
  // field on every keystroke (that would fight e.g. typing "5" on the way
  // to "50"). Clamp + snap it back into range once they're done (blur/Enter).
  el.radiusNumber.addEventListener("input", () => {
    const km = Number(el.radiusNumber.value);
    if (!Number.isFinite(km) || km <= 0) return;
    const metres = km * 1000;
    el.radiusSlider.value = Math.round(clampRadiusM(metres) / 1000);
    onRadiusInputChanged(metres);
  });

  el.radiusNumber.addEventListener("change", () => {
    const km = Number(el.radiusNumber.value) || RADIUS_DEFAULT_M / 1000;
    const metres = clampRadiusM(km * 1000);
    el.radiusNumber.value = Math.round((metres / 1000) * 100) / 100;
    el.radiusSlider.value = Math.round(metres / 1000);
    onRadiusInputChanged(metres);
  });

  el.radiusSlider.addEventListener("input", () => {
    const metres = Number(el.radiusSlider.value) * 1000; // range input is already clamped by min/max
    el.radiusNumber.value = Math.round((metres / 1000) * 100) / 100;
    onRadiusInputChanged(metres);
  });

  el.clearBtn.addEventListener("click", clearShape);

  async function copyTextToClipboard(text) {
    try {
      await navigator.clipboard.writeText(text);
    } catch (err) {
      const temp = document.createElement("textarea");
      temp.value = text;
      temp.style.position = "fixed";
      temp.style.opacity = "0";
      document.body.appendChild(temp);
      temp.select();
      document.execCommand("copy");
      temp.remove();
    }
  }

  el.copyBtn.addEventListener("click", async () => {
    const geojson = buildGeoJSON();
    if (!geojson) {
      alert("Click the map to place a circle first.");
      return;
    }
    await copyTextToClipboard(JSON.stringify(geojson, null, 2));
    flashButton(el.copyBtn, "Copied!");
  });

  el.downloadBtn.addEventListener("click", () => {
    const geojson = buildGeoJSON();
    if (!geojson) {
      alert("Click the map to place a circle first.");
      return;
    }
    const blob = new Blob([JSON.stringify(geojson, null, 2)], { type: "application/geo+json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    const name = (el.name.value || "shape").trim().replace(/\s+/g, "_");
    a.href = url;
    a.download = `${name}.geojson`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  });

  function flashButton(button, text) {
    const original = button.textContent;
    button.textContent = text;
    setTimeout(() => (button.textContent = original), 1200);
  }

  // ---------------------------------------------------------------------
  // Licence search (GeoJSON circle + frequency band -> /api/search)
  // ---------------------------------------------------------------------
  const FREQ_UNIT_MULTIPLIERS = { Hz: 1, kHz: 1e3, MHz: 1e6, GHz: 1e9 };

  /** Read a value+unit pair into Hz, or null if the value field is empty/invalid. */
  function getFrequencyHz(valueEl, unitEl) {
    if (valueEl.value.trim() === "") return null;
    const raw = Number(valueEl.value);
    if (!Number.isFinite(raw)) return null;
    return raw * FREQ_UNIT_MULTIPLIERS[unitEl.value];
  }

  function setSearchStatus(text, kind) {
    el.searchStatus.textContent = text;
    el.searchStatus.hidden = !text;
    el.searchStatus.className = "search-status" + (kind ? ` is-${kind}` : "");
  }

  function escapeHtml(str) {
    return String(str).replace(/[&<>"']/g, (c) => (
      { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]
    ));
  }

  function formatHz(hz) {
    if (hz === null || hz === undefined) return null;
    const abs = Math.abs(hz);
    if (abs >= 1e9) return `${(hz / 1e9).toFixed(4).replace(/\.?0+$/, "")} GHz`;
    if (abs >= 1e6) return `${(hz / 1e6).toFixed(3).replace(/\.?0+$/, "")} MHz`;
    if (abs >= 1e3) return `${(hz / 1e3).toFixed(3).replace(/\.?0+$/, "")} kHz`;
    return `${hz} Hz`;
  }

  // property key -> display label; keys not listed are shown title-cased.
  const RESULT_PROPERTY_LABELS = {
    licence_no: "Licence No",
    licence_type: "Licence Type",
    licence_category: "Licence Category",
    status_text: "Status",
    date_issued: "Date Issued",
    date_of_effect: "Date of Effect",
    date_of_expiry: "Date of Expiry",
    client_no: "Client No",
    licencee: "Licencee",
    trading_name: "Trading Name",
    service: "Service",
    subservice: "Subservice",
    site_id: "Site ID",
    distance_m: "Distance",
    frequency_hz: "Frequency",
    bandwidth_hz: "Bandwidth",
    freq_range_hz: "Frequency Range",
    emission: "Emission",
    device_type: "Device Type",
    station_type: "Station Type",
    station_name: "Station Name",
    call_sign: "Call Sign",
    class_of_station_desc: "Class of Station",
    antenna_id: "Antenna ID",
    antenna_gain_dbi: "Antenna Gain",
    azimuth: "Azimuth",
    height_m: "Height",
    tilt: "Tilt",
    polarisation: "Polarisation",
    transmitter_power: "Tx Power",
    eirp: "EIRP",
    sdd_id: "Device Record ID",
  };

  // Keys merged into a single formatted line elsewhere, or too internal to show raw.
  const RESULT_PROPERTY_SKIP = new Set([
    "status", "class_of_station", "transmitter_power_unit", "eirp_unit",
  ]);

  function formatPropertyValue(key, value, props) {
    if (key === "frequency_hz") return formatHz(value);
    if (key === "bandwidth_hz") return formatHz(value);
    if (key === "freq_range_hz") return `${formatHz(value[0])} – ${formatHz(value[1])}`;
    if (key === "distance_m") return value < 1000 ? `${value} m` : `${(value / 1000).toFixed(2)} km`;
    if (key === "transmitter_power") return `${value} ${props.transmitter_power_unit || ""}`.trim();
    if (key === "eirp") return `${value} ${props.eirp_unit || ""}`.trim();
    if (key === "azimuth" || key === "tilt") return `${value}°`;
    if (key === "height_m") return `${value} m`;
    if (key === "antenna_gain_dbi") return `${value} dBi`;
    return String(value);
  }

  function buildPopupHtml(props) {
    const title = props.licencee || props.trading_name || props.licence_no || "Licence";
    const rows = Object.keys(RESULT_PROPERTY_LABELS)
      .filter((key) => key !== "licencee" || props.trading_name) // avoid repeating the title
      .map((key) => {
        const value = props[key];
        if (value === null || value === undefined || value === "" || RESULT_PROPERTY_SKIP.has(key)) {
          return "";
        }
        const label = RESULT_PROPERTY_LABELS[key];
        const formatted = escapeHtml(formatPropertyValue(key, value, props));
        return `<tr><td class="k">${label}</td><td class="v">${formatted}</td></tr>`;
      })
      .join("");

    return `
      <div class="result-popup">
        <h3>${escapeHtml(title)}</h3>
        <table>${rows}</table>
      </div>
    `;
  }

  function renderResults(features) {
    resultsLayer.clearLayers();
    currentResultItems = features.map((feature, index) => {
      const [lng, lat] = feature.geometry.coordinates;
      const marker = L.marker([lat, lng], { icon: resultIcon });
      marker.bindPopup(buildPopupHtml(feature.properties), { maxWidth: 320 });
      // Keep the chart bar highlighted in sync with whichever popup is open,
      // however it was opened (chart click, direct marker click, ...).
      marker.on("popupopen", () => highlightBar(index));
      return { feature, marker };
    });
    resultsLayer.addLayers(currentResultItems.map((item) => item.marker));
    return currentResultItems;
  }

  // ---------------------------------------------------------------------
  // Occupied-bandwidth chart (bottom of the map)
  // ---------------------------------------------------------------------

  /**
   * Greedily pack [start,end] bars into the fewest horizontal rows such
   * that no two bars in the same row overlap (classic interval-partitioning
   * / "minimum platforms" algorithm — sort by start, reuse the first row
   * already free at that point, else open a new row).
   */
  function packBandwidthRows(bars) {
    const sorted = [...bars].sort((a, b) => a.start - b.start);
    const rows = [];
    for (const bar of sorted) {
      let row = rows.find((r) => bar.start >= r.lastEnd);
      if (!row) {
        row = { lastEnd: -Infinity, items: [] };
        rows.push(row);
      }
      row.items.push(bar);
      row.lastEnd = bar.end;
    }
    return rows.map((r) => r.items);
  }

  function highlightBar(index) {
    if (selectedBarEl) selectedBarEl.classList.remove("selected");
    selectedBarEl = el.bandwidthChartBody.querySelector(`.bw-bar[data-index="${index}"]`);
    if (selectedBarEl) {
      selectedBarEl.classList.add("selected");
      selectedBarEl.scrollIntoView({ block: "nearest" });
    }
  }

  function renderBandwidthChart(items, freqMinHz, freqMaxHz) {
    el.bandwidthChartBody.innerHTML = "";
    selectedBarEl = null;

    if (!items.length) {
      el.bandwidthChart.hidden = true;
      return;
    }

    el.bandwidthChartTitle.textContent =
      `Occupied bandwidth — ${items.length} result${items.length === 1 ? "" : "s"}`;
    el.bwAxisMin.textContent = formatHz(freqMinHz);
    el.bwAxisMid.textContent = formatHz((freqMinHz + freqMaxHz) / 2);
    el.bwAxisMax.textContent = formatHz(freqMaxHz);

    const span = Math.max(freqMaxHz - freqMinHz, 1);
    const bars = items
      .map((item, index) => {
        const range = item.feature.properties.freq_range_hz;
        if (!range) return null;
        const start = Math.max(freqMinHz, Math.min(range[0], range[1]));
        const end = Math.min(freqMaxHz, Math.max(range[0], range[1], start));
        return { index, start, end };
      })
      .filter(Boolean);

    const rows = packBandwidthRows(bars);
    const fragment = document.createDocumentFragment();
    rows.forEach((rowBars) => {
      const rowEl = document.createElement("div");
      rowEl.className = "bw-row";
      rowBars.forEach((bar) => {
        const props = items[bar.index].feature.properties;
        const leftPct = ((bar.start - freqMinHz) / span) * 100;
        const widthPct = Math.max(((bar.end - bar.start) / span) * 100, 0.3);

        const barEl = document.createElement("div");
        barEl.className = "bw-bar";
        barEl.style.left = `${leftPct}%`;
        barEl.style.width = `${widthPct}%`;
        barEl.dataset.index = bar.index;
        const label = props.licencee || props.trading_name || props.licence_no || "Licence";
        barEl.title = `${label} — ${formatHz(bar.start)} to ${formatHz(bar.end)}`;
        rowEl.appendChild(barEl);
      });
      fragment.appendChild(rowEl);
    });
    el.bandwidthChartBody.appendChild(fragment);

    el.bandwidthChart.hidden = false;
  }

  el.bandwidthChartBody.addEventListener("click", (e) => {
    const barEl = e.target.closest(".bw-bar");
    if (!barEl) return;
    const index = Number(barEl.dataset.index);
    const item = currentResultItems[index];
    if (!item) return;
    highlightBar(index);
    resultsLayer.zoomToShowLayer(item.marker, () => item.marker.openPopup());
  });

  el.bandwidthChartClose.addEventListener("click", () => {
    el.bandwidthChart.hidden = true;
  });

  // ---------------------------------------------------------------------
  // "Model sites" — CloudRF Area coverage for the nearest results
  // ---------------------------------------------------------------------
  const RF_MODEL_COUNT = 10;

  function setModelStatus(text, kind, spinning) {
    el.modelStatusText.textContent = text;
    el.modelStatus.hidden = !text;
    el.modelStatus.className = "search-status" + (kind ? ` is-${kind}` : "");
    el.modelStatus.querySelector(".spinner").hidden = !spinning;
  }

  /** Dedupe search results by site (a site can have several device records,
   * e.g. a transmitter + receiver pair) and take the N nearest, preferring
   * a transmitter ('T') record per site as the more physically meaningful
   * source of RF parameters when one exists. */
  function getNearestUniqueSites(items, limit) {
    const bySite = new Map();
    for (const item of items) {
      const siteId = item.feature.properties.site_id;
      if (!siteId) continue; // can't model a site with no location key
      const existing = bySite.get(siteId);
      if (!existing) {
        bySite.set(siteId, item);
      } else if (
        item.feature.properties.device_type === "T" &&
        existing.feature.properties.device_type !== "T"
      ) {
        bySite.set(siteId, item);
      }
    }
    return [...bySite.values()]
      .sort((a, b) => (a.feature.properties.distance_m ?? Infinity) - (b.feature.properties.distance_m ?? Infinity))
      .slice(0, limit);
  }

  function siteRequestPayload(item) {
    const props = item.feature.properties;
    const [lng, lat] = item.feature.geometry.coordinates;
    return {
      lat,
      lng,
      name: props.station_name || props.licencee || props.licence_no || `Site ${props.site_id}`,
      frequency_hz: props.frequency_hz,
      bandwidth_hz: props.bandwidth_hz,
      // Power + gain are the only ACMA antenna figures CloudRF uses — see
      // cloudrf.py: it models a plain dipole (no ACMA pattern/azimuth/tilt
      // data), so those aren't sent here.
      eirp: props.eirp,
      eirp_unit: props.eirp_unit,
      transmitter_power: props.transmitter_power,
      transmitter_power_unit: props.transmitter_power_unit,
      antenna_gain_dbi: props.antenna_gain_dbi,
      height_m: props.height_m,
      polarisation: props.polarisation,
    };
  }

  function clearRfLayers() {
    rfLayers.forEach(({ overlay }) => {
      if (map.hasLayer(overlay)) map.removeLayer(overlay);
    });
    rfLayers = [];
    el.rfLayerList.innerHTML = "";
    el.rfLayersSection.hidden = true;
  }

  function addRfLayerRow(id, label, overlay) {
    overlay.addTo(map);
    rfLayers.push({ id, overlay });

    const li = document.createElement("li");

    const checkboxLabel = document.createElement("label");
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.checked = true;
    checkbox.addEventListener("change", () => {
      if (checkbox.checked) {
        overlay.addTo(map);
      } else if (map.hasLayer(overlay)) {
        map.removeLayer(overlay);
      }
    });
    const nameSpan = document.createElement("span");
    nameSpan.className = "rf-layer-name";
    nameSpan.textContent = label;
    nameSpan.title = label;
    checkboxLabel.appendChild(checkbox);
    checkboxLabel.appendChild(nameSpan);

    const removeBtn = document.createElement("button");
    removeBtn.type = "button";
    removeBtn.className = "rf-layer-remove";
    removeBtn.textContent = "✕";
    removeBtn.title = "Remove layer";
    removeBtn.addEventListener("click", () => {
      if (map.hasLayer(overlay)) map.removeLayer(overlay);
      rfLayers = rfLayers.filter((l) => l.id !== id);
      li.remove();
      if (!rfLayers.length) el.rfLayersSection.hidden = true;
    });

    li.appendChild(checkboxLabel);
    li.appendChild(removeBtn);
    el.rfLayerList.appendChild(li);
    el.rfLayersSection.hidden = false;
  }

  el.rfLayersClose.addEventListener("click", () => {
    el.rfLayersSection.hidden = true;
  });

  function addRfLayerError(label, message) {
    const li = document.createElement("li");
    const span = document.createElement("span");
    span.className = "rf-layer-error";
    span.textContent = `${label}: ${message}`;
    li.appendChild(span);
    el.rfLayerList.appendChild(li);
    el.rfLayersSection.hidden = false;
  }

  async function runModelSites() {
    if (!currentResultItems.length) {
      alert("Run a search with results first.");
      return;
    }

    const sites = getNearestUniqueSites(currentResultItems, RF_MODEL_COUNT);
    if (!sites.length) {
      alert("No sites with location data in the current results.");
      return;
    }

    clearRfLayers();
    el.modelBtn.disabled = true;
    let succeeded = 0;
    let failed = 0;

    for (let i = 0; i < sites.length; i++) {
      const item = sites[i];
      const label = siteRequestPayload(item).name;
      setModelStatus(`Modelling site ${i + 1}/${sites.length}: ${label}…`, "loading", true);

      try {
        const res = await fetch("/api/cloudrf/area", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            site: siteRequestPayload(item),
            radius_m: state.radius,
          }),
        });
        const body = await res.json();
        if (!res.ok) throw new Error(body.error || `Request failed (${res.status})`);

        const bounds = body.bounds; // [[lat,lon],[lat,lon]]
        const overlay = L.imageOverlay(body.image_url, bounds, { opacity: 0.7 });
        addRfLayerRow(body.job_id, label, overlay);
        succeeded++;
      } catch (err) {
        console.error(`CloudRF modelling failed for ${label}`, err);
        addRfLayerError(label, err.message);
        failed++;
      }
    }

    const summary = failed
      ? `Modelled ${succeeded}/${sites.length} sites (${failed} failed — see layer list below)`
      : `Modelled ${succeeded} site${succeeded === 1 ? "" : "s"}`;
    setModelStatus(summary, failed ? "error" : "success", false);
    el.modelBtn.disabled = false;
  }

  el.modelBtn.addEventListener("click", runModelSites);

  async function runSearch() {
    if (!hasShape()) {
      alert("Click the map to place a circle first.");
      return;
    }
    if (!el.freqMinValue.reportValidity() || !el.freqMaxValue.reportValidity()) {
      return;
    }
    const freqMinHz = getFrequencyHz(el.freqMinValue, el.freqMinUnit);
    const freqMaxHz = getFrequencyHz(el.freqMaxValue, el.freqMaxUnit);
    if (freqMinHz === null || freqMaxHz === null) {
      alert("Enter both a lower and upper frequency.");
      return;
    }
    if (freqMinHz > freqMaxHz) {
      alert("Lower frequency must not be greater than the upper frequency.");
      return;
    }

    const circle = buildGeoJSON();
    const originalLabel = el.searchBtn.textContent;
    el.searchBtn.disabled = true;
    el.searchBtn.textContent = "Searching…";
    setSearchStatus("Searching…", "loading");

    try {
      const res = await fetch("/api/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          circle,
          freq_min: freqMinHz,
          freq_max: freqMaxHz,
          limit: 500,
        }),
      });
      const body = await res.json();
      if (!res.ok) {
        throw new Error(body.error || `Search failed (${res.status})`);
      }

      const items = renderResults(body.features);
      renderBandwidthChart(items, freqMinHz, freqMaxHz);

      if (body.meta.count === 0) {
        setSearchStatus("No licences found in that area and frequency range.", "empty");
      } else {
        const suffix = body.meta.truncated
          ? ` (showing first ${body.meta.count}, more exist — narrow the search)`
          : "";
        setSearchStatus(`${body.meta.count} result${body.meta.count === 1 ? "" : "s"}${suffix}`, "success");
      }
    } catch (err) {
      console.error("Search failed", err);
      resultsLayer.clearLayers();
      currentResultItems = [];
      el.bandwidthChart.hidden = true;
      setSearchStatus(`Error: ${err.message}`, "error");
    } finally {
      el.searchBtn.disabled = false;
      el.searchBtn.textContent = originalLabel;
    }
  }

  el.searchBtn.addEventListener("click", runSearch);

  // ---------------------------------------------------------------------
  // Sidebar toggle
  // ---------------------------------------------------------------------
  el.sidebarToggle.addEventListener("click", () => {
    el.app.classList.toggle("collapsed");
    setTimeout(() => map.invalidateSize(), 210);
  });

  // ---------------------------------------------------------------------
  // Settings modal (base map + CloudRF API key)
  // ---------------------------------------------------------------------
  function cloudRfHintText(body) {
    if (body.cloudrf_api_key) return "Overrides the CLOUDRF_API_KEY environment variable.";
    if (body.cloudrf_api_key_from_env) {
      return "Using the CLOUDRF_API_KEY environment variable. Enter a key here to override it.";
    }
    return "No key configured yet — Model sites won't work until one is set.";
  }

  async function loadCloudRfKeyIntoModal() {
    el.cloudrfKeyStatus.hidden = true;
    el.cloudrfKeyHint.textContent = "Loading…";
    try {
      const res = await fetch("/api/settings");
      const body = await res.json();
      el.cloudrfKeyInput.value = body.cloudrf_api_key || "";
      el.cloudrfKeyHint.textContent = cloudRfHintText(body);
    } catch (err) {
      el.cloudrfKeyHint.textContent = "Could not load current settings.";
    }
  }

  function openSettings() {
    const checkedRadio = [...el.basemapRadios].find((r) => r.value === currentBasemapKey);
    if (checkedRadio) checkedRadio.checked = true;
    loadCloudRfKeyIntoModal();
    el.settingsBackdrop.hidden = false;
  }

  function closeSettings() {
    el.settingsBackdrop.hidden = true;
  }

  el.settingsBtn.addEventListener("click", openSettings);
  el.settingsClose.addEventListener("click", closeSettings);
  el.settingsBackdrop.addEventListener("click", (e) => {
    if (e.target === el.settingsBackdrop) closeSettings();
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !el.settingsBackdrop.hidden) closeSettings();
  });

  el.basemapRadios.forEach((radio) => {
    radio.addEventListener("change", () => {
      if (radio.checked) switchBasemap(radio.value);
    });
  });

  el.cloudrfKeyToggle.addEventListener("click", () => {
    el.cloudrfKeyInput.type = el.cloudrfKeyInput.type === "password" ? "text" : "password";
  });

  el.cloudrfKeySave.addEventListener("click", async () => {
    try {
      const res = await fetch("/api/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ cloudrf_api_key: el.cloudrfKeyInput.value }),
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body.error || "Save failed");
      el.cloudrfKeyHint.textContent = cloudRfHintText(body);
      el.cloudrfKeyStatus.textContent = "Saved!";
      el.cloudrfKeyStatus.className = "search-status is-success";
      el.cloudrfKeyStatus.hidden = false;
      setTimeout(() => {
        el.cloudrfKeyStatus.hidden = true;
      }, 2000);
    } catch (err) {
      el.cloudrfKeyStatus.textContent = `Error: ${err.message}`;
      el.cloudrfKeyStatus.className = "search-status is-error";
      el.cloudrfKeyStatus.hidden = false;
    }
  });

  // ---------------------------------------------------------------------
  // Saving / loading shapes via the backend
  // ---------------------------------------------------------------------
  async function refreshSavedList() {
    let shapes = [];
    try {
      const res = await fetch("/api/shapes");
      shapes = await res.json();
    } catch (err) {
      console.error("Failed to load saved shapes", err);
    }

    el.savedList.innerHTML = "";
    if (!shapes.length) {
      const li = document.createElement("li");
      li.className = "empty";
      li.textContent = "None yet";
      el.savedList.appendChild(li);
      return;
    }

    shapes.forEach((shape) => {
      const li = document.createElement("li");

      const nameSpan = document.createElement("span");
      nameSpan.className = "saved-name";
      nameSpan.textContent = shape.name;
      nameSpan.title = shape.name;

      const actions = document.createElement("div");
      actions.className = "saved-actions";

      const loadBtn = document.createElement("button");
      loadBtn.type = "button";
      loadBtn.textContent = "Load";
      loadBtn.addEventListener("click", () => loadSavedShape(shape));

      const delBtn = document.createElement("button");
      delBtn.type = "button";
      delBtn.textContent = "✕";
      delBtn.title = "Delete";
      delBtn.addEventListener("click", () => deleteSavedShape(shape.id));

      actions.appendChild(loadBtn);
      actions.appendChild(delBtn);
      li.appendChild(nameSpan);
      li.appendChild(actions);
      el.savedList.appendChild(li);
    });
  }

  function loadSavedShape(shape) {
    const geom = shape.geojson && shape.geojson.geometry;
    if (!geom) return;

    el.name.value = shape.name || "";

    if (geom.type === "Point") {
      const [lng, lat] = geom.coordinates;
      const radius = clampRadiusM((shape.geojson.properties && shape.geojson.properties.radius) || RADIUS_DEFAULT_M);
      el.polygonMode.checked = false;
      placeShape(lat, lng, radius);
    } else if (geom.type === "Polygon") {
      const ring = geom.coordinates[0];
      const lats = ring.map((c) => c[1]);
      const lngs = ring.map((c) => c[0]);
      const lat = (Math.min(...lats) + Math.max(...lats)) / 2;
      const lng = (Math.min(...lngs) + Math.max(...lngs)) / 2;
      const radius = clampRadiusM((shape.geojson.properties && shape.geojson.properties.radius) || RADIUS_DEFAULT_M);
      el.polygonMode.checked = true;
      placeShape(lat, lng, radius);
    }
    map.setView([state.center.lat, state.center.lng], Math.max(map.getZoom(), 10));
  }

  async function deleteSavedShape(id) {
    try {
      await fetch(`/api/shapes/${id}`, { method: "DELETE" });
      refreshSavedList();
    } catch (err) {
      console.error("Failed to delete shape", err);
    }
  }

  el.saveBtn.addEventListener("click", async () => {
    if (!hasShape()) {
      alert("Click the map to place a point first.");
      return;
    }
    const geojson = buildGeoJSON();
    try {
      const res = await fetch("/api/shapes", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: el.name.value || "Untitled shape",
          geojson,
        }),
      });
      if (!res.ok) throw new Error(await res.text());
      flashButton(el.saveBtn, "Saved!");
      refreshSavedList();
    } catch (err) {
      console.error("Failed to save shape", err);
      alert("Could not save shape — see console for details.");
    }
  });

  // ---------------------------------------------------------------------
  // Init
  // ---------------------------------------------------------------------
  refreshSavedList();
})();
