// =====================================================
// === Map initialization
// =====================================================
var map = L.map('map', { center: [51.79407, -2.09633], zoom: 13 });
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: '<a href="https://cloudrf.com">CloudRF</a> | &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map);


// =====================================================
// === Fixed Nodes (draggable)
// =====================================================
let fixedNodes = [
  { name: "Sensor A",  lat: 51.805, lon: -2.1, alt: 5,  frq: 2400, txw: 1 },
  { name: "Sensor B",  lat: 51.794, lon: -2.15, alt: 5,  frq: 2400, txw: 1 },
  { name: "Sensor C",  lat: 51.793, lon: -2.05, alt: 5,  frq: 2400, txw: 1 }
];


var UASIcon = L.icon({
    iconUrl: 'images/drone.png',

    iconSize:     [40, 40], // size of the icon
    iconAnchor:   [20, 20], // point of the icon which will correspond to marker's location
});

var drone = {
  lat: 51.8,
  lon: -2.09633,
  alt: 50,
  marker: L.marker([51.8, -2.09633], { icon: UASIcon, draggable: true }).addTo(map)
};
drone.marker.bindTooltip("Drone");

let nodes = fixedNodes.map(n => {
  const marker = L.circleMarker([n.lat, n.lon], { radius: 15, color: 'black' })
    .addTo(map)
    .bindTooltip(`${n.name}, F ${n.frq}MHz, ${n.txw}W`);

  const draggableMarker = L.marker([n.lat, n.lon], { draggable: true, opacity: 0.0 }).addTo(map);
  const node = { ...n, marker, dragHandle: draggableMarker };

  draggableMarker.on('drag', evt => {
    const pos = evt.target.getLatLng();
    marker.setLatLng(pos);
    node.lat = pos.lat;
    node.lon = pos.lng;
  });

  draggableMarker.on('dragend', evt => {
    const pos = evt.target.getLatLng();
    node.lat = pos.lat;
    node.lon = pos.lng;
    calculate();
  });

  return node;
});


// =====================================================
// === RSSI helpers
// =====================================================
function rssi_color(v) {
  if (v < -90) return 'red';
  if (v < -80) return 'orange';
  return 'green';
}

// Track link polylines so they can be cleared each update
let linkLines = [];

function update_node_colors(data) {
  if (!data.values) return;

  linkLines.forEach(l => map.removeLayer(l));
  linkLines = [];

  const vals = Object.values(data.values);
  nodes.forEach((node, i) => {
    const val = vals[i] || -90;
    const color = rssi_color(val);

    node.marker.setStyle({ color });
    node.marker.setTooltipContent(`${node.name}: ${val.toFixed(1)} dBm`);

    // Draw coloured link line from drone to node
    const line = L.polyline(
      [[drone.lat, drone.lon], [node.lat, node.lon]],
      { color, weight: 3, opacity: 0.8 }
    ).addTo(map);
    line.bindTooltip(`${node.name}: ${val.toFixed(1)} dBm`);
    linkLines.push(line);
  });
}


// =====================================================
// === FIGURE-EIGHT AUTOPILOT
// =====================================================
let figureEightActive = false;
let figureEightTimer  = null;
let figureEightOriginLat = drone.lat;
let figureEightOriginLon = drone.lon;
let figureEightT = 0;

// ── Size & speed ──────────────────────────────────────
const FIGURE_EIGHT_RADIUS   = 0.05;  // degrees (~800 m wide loop)
const FIGURE_EIGHT_STEP     = 0.05;  // radians per tick
const FIGURE_EIGHT_INTERVAL = 500;    // ms between ticks
// ─────────────────────────────────────────────────────

let figureEightPathLayer = null;

function drawFigureEightPath(originLat, originLon) {
  if (figureEightPathLayer) map.removeLayer(figureEightPathLayer);
  const pts = [];
  for (let t = 0; t <= 2 * Math.PI + 0.05; t += 0.04) {
    const pos = figureEightPosition(t, originLat, originLon);
    pts.push([pos.lat, pos.lon]);
  }
  figureEightPathLayer = L.polyline(pts, {
    color: '#3388ff', weight: 2, dashArray: '6,5', opacity: 0.65
  }).addTo(map);
}

// Lemniscate of Bernoulli parametric form
function figureEightPosition(t, originLat, originLon) {
  const scale = 1 / (1 + Math.sin(t) * Math.sin(t));
  const x = FIGURE_EIGHT_RADIUS * Math.cos(t) * scale;
  const y = FIGURE_EIGHT_RADIUS * Math.sin(t) * Math.cos(t) * scale;
  return { lat: originLat + y, lon: originLon + x };
}

function startFigureEight() {
  figureEightOriginLat = drone.lat;
  figureEightOriginLon = drone.lon;
  figureEightT = 0;
  drawFigureEightPath(figureEightOriginLat, figureEightOriginLon);

  figureEightTimer = setInterval(() => {
    figureEightT += FIGURE_EIGHT_STEP;
    const pos = figureEightPosition(figureEightT, figureEightOriginLat, figureEightOriginLon);
    drone.lat = pos.lat;
    drone.lon = pos.lon;
    drone.marker.setLatLng([drone.lat, drone.lon]);

    // Auto-vary altitude if enabled
    if (autoHeightActive) {
      const minH  = parseFloat(document.getElementById('autoHeightMin').value)  || 20;
      const maxH  = parseFloat(document.getElementById('autoHeightMax').value)  || 200;
      const freq  = parseFloat(document.getElementById('autoHeightFreq').value) || 0.5;
      const newAlt = minH + ((maxH - minH) / 2) * (1 + Math.sin(figureEightT * freq));
      drone.alt = Math.round(newAlt);
      const slider   = document.getElementById('Altitude-Slider');
      const altLabel = document.getElementById('Altitude-Value');
      if (slider)   slider.value = drone.alt;
      if (altLabel) altLabel.textContent = `${drone.alt} m`;
    }

    calculate();
  }, FIGURE_EIGHT_INTERVAL);
}

function stopFigureEight() {
  if (figureEightTimer) { clearInterval(figureEightTimer); figureEightTimer = null; }
  if (figureEightPathLayer) { map.removeLayer(figureEightPathLayer); figureEightPathLayer = null; }
}

function toggleFigureEight() {
  figureEightActive = !figureEightActive;
  const btn = document.getElementById('btnFigureEight');
  if (figureEightActive) {
    startFigureEight();
    btn.textContent = 'Stop Figure-Eight';
    btn.className = 'btn btn-sm btn-warning';
    drone.marker.dragging.disable();
  } else {
    stopFigureEight();
    btn.textContent = 'Start Figure-Eight';
    btn.className = 'btn btn-sm btn-primary';
    drone.marker.dragging.enable();
  }
}


// =====================================================
// === AUTO HEIGHT VARIATION
// =====================================================
let autoHeightActive = false;

function toggleAutoHeight() {
  autoHeightActive = !autoHeightActive;
  const btn   = document.getElementById('btnAutoHeight');
  const panel = document.getElementById('autoHeightPanel');
  if (autoHeightActive) {
    btn.textContent = '↕ Auto Height: ON';
    btn.className   = 'btn btn-sm btn-success';
    panel.style.display = 'flex';
  } else {
    btn.textContent = '↕ Auto Height: OFF';
    btn.className   = 'btn btn-sm btn-outline-success';
    panel.style.display = 'none';
  }
}


// =====================================================
// === RECORDING & KMZ EXPORT
// =====================================================
let recordedResults = [];
let isRecording     = false;

function toggleRecording() {
  if (!isRecording) {
    recordedResults = [];
    isRecording = true;
    document.getElementById('btnRecord').textContent = '⏹ Stop Recording';
    document.getElementById('btnRecord').className   = 'btn btn-sm btn-danger';
    document.getElementById('recordingDot').style.display = 'inline-block';
  } else {
    isRecording = false;
    document.getElementById('btnRecord').textContent = '⏺ Start Recording';
    document.getElementById('btnRecord').className   = 'btn btn-sm btn-outline-danger';
    document.getElementById('recordingDot').style.display = 'none';
  }
  document.getElementById('recordCount').textContent = `${recordedResults.length} snapshots`;
}

function recordSnapshot(request, data) {
  if (!isRecording) return;
  recordedResults.push({
    timestamp: new Date().toISOString(),
    lat: drone.lat,
    lon: drone.lon,
    alt: drone.alt,
    request: JSON.parse(JSON.stringify(request)),
    response: JSON.parse(JSON.stringify(data))
  });
  document.getElementById('recordCount').textContent = `${recordedResults.length} snapshots`;
}

async function exportKMZ() {
  if (recordedResults.length === 0) {
    alert('No recorded results to export. Start recording and run some calculations first.');
    return;
  }

  const placemarks = recordedResults.map((snap, i) => {
    const rssiValues = snap.response && snap.response.values
      ? Object.values(snap.response.values) : [];
    const avg = rssiValues.length > 0
      ? rssiValues.reduce((a, b) => a + b, 0) / rssiValues.length : null;

    let iconHref = 'http://maps.google.com/mapfiles/kml/paddle/red-circle.png';
    if (avg !== null && avg >= -80) iconHref = 'http://maps.google.com/mapfiles/kml/paddle/grn-circle.png';
    else if (avg !== null && avg >= -90) iconHref = 'http://maps.google.com/mapfiles/kml/paddle/ylw-circle.png';

    const nodeRows = nodes.map((node, ni) => {
      const rssi = rssiValues[ni] !== undefined ? rssiValues[ni].toFixed(1) + ' dBm' : 'N/A';
      return `<tr><td>${node.name}</td><td>${rssi}</td></tr>`;
    }).join('');

    // KML color format: AABBGGRR
    function rssiToKmlColor(v) {
      if (v < -90) return 'ff0000ff'; // red
      if (v < -80) return 'ff00aaff'; // orange
      return 'ff00bb00';              // green
    }

    // One link line per node, coloured by RSSI — mirrors the live map display
    const linkLinePlacemarks = nodes.map((node, ni) => {
      const val      = rssiValues[ni] !== undefined ? rssiValues[ni] : -90;
      const kmlColor = rssiToKmlColor(val);
      return `
    <Placemark>
      <description><![CDATA[<b>${node.name}</b><br/>RSSI: ${val.toFixed(1)} dBm<br/>Drone alt: ${snap.alt} m]]></description>
      <Style><LineStyle><color>${kmlColor}</color><width>3</width></LineStyle></Style>
      <LineString>
        <altitudeMode>relativeToGround</altitudeMode>
        <tessellate>1</tessellate>
        <coordinates>${snap.lon},${snap.lat},${snap.alt} ${node.lon},${node.lat},${node.alt}</coordinates>
      </LineString>
    </Placemark>`;
    }).join('\n');

    return `
    <Placemark>
      <description><![CDATA[
        <b>Time:</b> ${snap.timestamp}<br/>
        <b>Lat/Lon:</b> ${snap.lat.toFixed(6)}, ${snap.lon.toFixed(6)}<br/>
        <b>Altitude:</b> ${snap.alt} m<br/>
        <b>Avg RSSI:</b> ${avg !== null ? avg.toFixed(1) + ' dBm' : 'N/A'}<br/><br/>
        <table border="1" cellpadding="3"><tr><th>Node</th><th>RSSI</th></tr>${nodeRows}</table>
      ]]></description>
      <Style><IconStyle><scale>0.7</scale><Icon><href>${iconHref}</href></Icon></IconStyle></Style>
      <Point>
        <altitudeMode>relativeToGround</altitudeMode>
        <coordinates>${snap.lon},${snap.lat},${snap.alt}</coordinates>
      </Point>
    </Placemark>
    ${linkLinePlacemarks}`;
  }).join('\n');

  const nodePlacemarks = nodes.map(n => `
    <Placemark>
      <name>${n.name}</name>
      <description>Freq: ${n.frq} MHz | Power: ${n.txw} W | Alt: ${n.alt}m</description>
      <Style><IconStyle><color>ff0088ff</color><scale>1.0</scale>
        <Icon><href>http://maps.google.com/mapfiles/kml/shapes/placemark_square.png</href></Icon>
      </IconStyle></Style>
      <Point>
        <altitudeMode>relativeToGround</altitudeMode>
        <coordinates>${n.lon},${n.lat},${n.alt}</coordinates>
      </Point>
    </Placemark>`).join('\n');

  const pathCoords = recordedResults.map(s => `${s.lon},${s.lat},${s.alt}`).join('\n');
  const pathLine = recordedResults.length > 1 ? `
    <Placemark>
      <name>Flight Path</name>
      <Style><LineStyle><color>ff3388ff</color><width>2</width></LineStyle></Style>
      <LineString>
        <altitudeMode>relativeToGround</altitudeMode>
        <tessellate>1</tessellate>
        <coordinates>${pathCoords}</coordinates>
      </LineString>
    </Placemark>` : '';

  const kml = `<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>CloudRF Drone Survey — ${new Date().toISOString().slice(0, 16).replace('T', ' ')}</name>
    <description>${recordedResults.length} snapshots. Green &gt;= -80dBm | Yellow -90 to -80 | Red &lt; -90.</description>
    <Folder><name>Drone Snapshots</name>${placemarks}</Folder>
    <Folder><name>Sensor Nodes</name>${nodePlacemarks}</Folder>
    ${pathLine}
  </Document>
</kml>`;

  if (typeof JSZip !== 'undefined') {
    const zip = new JSZip();
    zip.file('doc.kml', kml);
    const blob = await zip.generateAsync({ type: 'blob', compression: 'DEFLATE' });
    triggerDownload(blob, `CloudRF_Survey_${Date.now()}.kmz`);
  } else {
    const blob = new Blob([kml], { type: 'application/vnd.google-earth.kml+xml' });
    triggerDownload(blob, `CloudRF_Survey_${Date.now()}.kml`);
  }
}

function triggerDownload(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a   = document.createElement('a');
  a.href = url; a.download = filename;
  document.body.appendChild(a); a.click();
  setTimeout(() => { URL.revokeObjectURL(url); a.remove(); }, 1500);
}


// =====================================================
// === CloudRF API Request
// =====================================================
async function calculate() {
  const api_key = document.getElementById("apiKey").value;
  const api_url = document.getElementById("apiServiceBaseUrl").value;

  const radios = [
    {
      lat: drone.lat, lon: drone.lon, alt: drone.alt,
      frq: 2450, txw: 1, bwi: 20, nf: "-100",
      antenna: { txg: 2, txl: 0, ant: 1, pol: "v", azi: 0, tlt: 0 }
    },
    ...nodes.map(n => ({
      lat: n.lat, lon: n.lon, alt: n.alt,
      frq: n.frq, txw: n.txw, bwi: 1.2, nf: "-100",
      antenna: { txg: 2, txl: 0, ant: 1, pol: "v", azi: 0, tlt: 0 }
    }))
  ];

  const request = {
    site: "Site", ui: 3, network: "CUASLeafletDemo", radios,
    model: { pm: 4, pe: 2, ked: 0, rel: 50 },
    environment: { elevation: 2, landcover: 0, buildings: 0 },
    output: { units: "m", out: 2, res: "20" }
  };

  document.getElementById('requestRawOutput').textContent = JSON.stringify(request, null, 2);

  try {
    const response = await fetch(api_url + '/multilink', {
      method: "POST",
      headers: { key: api_key },
      body: JSON.stringify(request)
    });
    const data = await response.json();
    document.getElementById('responseRawOutput').textContent = JSON.stringify(data, null, 2);
    update_node_colors(data);
    recordSnapshot(request, data);
  } catch (err) {
    console.error(err);
  }
}


// =====================================================
// === Drone drag (disabled during autopilot)
// =====================================================
drone.marker.on('dragend', function (e) {
  if (figureEightActive) return;
  const pos = e.target.getLatLng();
  drone.lat = pos.lat;
  drone.lon = pos.lng;
  calculate();
});

// === Initial calculation ===
calculate();
