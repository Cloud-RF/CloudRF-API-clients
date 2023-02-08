/*
Copyright 2021 Farrant Consulting Ltd

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
*/

var apiKey = undefined;
var apiServiceBaseUrl = undefined;

$(document).ready(function() {
    setApiServiceBaseUrl();
    validateApiKey();
})

$('input#apiKey').on('change', function() {
    apiKey = $('input#apiKey').val();
    validateApiKey();
})

$('input#apiServiceBaseUrl').on('change', function() {
    setApiServiceBaseUrl()
})

function setApiServiceBaseUrl() {
    apiServiceBaseUrl = $('input#apiServiceBaseUrl').val().replace(/\/$/, "");
}

// Converts from degrees to radians.
function toRadians(degrees) {
    return degrees * Math.PI / 180;
};

// Converts from radians to degrees.
function toDegrees(radians) {
    return radians * 180 / Math.PI;
}
// For directional antennas 
function bearing(startLat, startLng, destLat, destLng) {
    startLat = toRadians(startLat);
    startLng = toRadians(startLng);
    destLat = toRadians(destLat);
    destLng = toRadians(destLng);

    y = Math.sin(destLng - startLng) * Math.cos(destLat);
    x = Math.cos(startLat) * Math.sin(destLat) -
        Math.sin(startLat) * Math.cos(destLat) * Math.cos(destLng - startLng);
    brng = Math.atan2(y, x);
    brng = toDegrees(brng);
    return (brng + 360) % 360;
}
// You can edit this JSON template using any parameter from https://docs.cloudrf.com
// For extra points, create multiple templates to have many radios in your tool

var template = {
    "site": "CloudRF-API-clients-DEMO",
    "network": "CloudRF-API-clients-DEMO",
    "transmitter": {
        "lat": 38.916,
        "lon": 1.448,
        "alt": 2,
        "frq": 446,
        "txw": 5,
        "bwi": 0.1
    },
    "receiver": {
        "lat": 0,
        "lon": 0,
        "alt": 1,
        "rxg": 2.15,
        "rxs": -99
    },
    "antenna": {
        "txg": 2.15,
        "txl": 0,
        "ant": 39,
        "azi": 0,
        "tlt": 0,
        "hbw": 0,
        "vbw": 0,
        "pol": "v"
    },
    "model": {
        "pm": 1,
        "pe": 2,
        "cli": 6,
        "ked": 0,
        "rel": 95,
        "ter": 4
    },
    "output": {
        "units": "metric",
        "col": "RAINBOW.dBm",
        "out": 2,
        "ber": 0,
        "mod": 0,
        "nf": -114,
        "res": 16,
        "rad": 2
    }
};

// Contains an array of points for the points API
// https://cloudrf.com/documentation/developer/swagger-ui/#/Create/points
var multipointTemplate = {
    "site": "CloudRF-API-clients-DEMO",
    "network": "CloudRF-API-clients-DEMO",
    "transmitter": {
        "lat": 38.916,
        "lon": 1.448,
        "alt": 15,
        "frq": 3400,
        "txw": 1,
        "bwi": 0.1
    },
    "points": [],
    "receiver": {
        "lat": 0,
        "lon": 0,
        "alt": 15,
        "rxg": 12,
        "rxs": -90
    },
    "antenna": {
        "txg": 12,
        "txl": 0,
        "ant": 39,
        "azi": 0,
        "tlt": 0,
        "hbw": 0,
        "vbw": 0,
        "pol": "v"
    },
    "model": {
        "pm": 1,
        "pe": 2,
        "cli": 6,
        "ked": 0,
        "rel": 95,
        "ter": 4
    },
    "environment": {
        "clm": 0,
        "cll": 2,
        "clt": "Minimal.clt"
    },
    "output": {
        "units": "metric",
        "col": "RAINBOW.dBm",
        "out": 2,
        "ber": 0,
        "mod": 0,
        "nf": -114,
        "res": 8,
        "rad": 2
    }
};
// Simplest use. Point-to-multimpoint around a location with fixed settings
function createAreaRequest(lat, lon, map, engine = '2') {
    /*
    1. Fetch a template
    2. Apply any variables like latitude, longitude, altitude
    3. Send to api
    4. Put on map
    */
    template.engine = engine;
    template.transmitter.lat = lat;
    template.transmitter.lon = lon;

    let JSONtemplate = JSON.stringify(template, null, 4);
    CloudRFAreaAPI(JSONtemplate, map);
}

// Points API. One AP to many CPE
function createPointsRequest(rxLat, rxLon, points, map) {
    /*
    1. Fetch a template
    2. Apply any variables like latitude, longitude, altitude
    3. Send to api
    4. Put on map
    */
    multipointTemplate.receiver.lat = rxLat;
    multipointTemplate.receiver.lon = rxLon;

    // Add the CPE array :)
    multipointTemplate.points = points;

    let JSONtemplate = JSON.stringify(multipointTemplate, null, 4);
    console.log(JSONtemplate);
    CloudRFPointsAPI(JSONtemplate, map);
}


// Advanced use. Point-to-multipoint with antenna azimuth and customised parameters
function createRFSectorRequest(lat, lon, azi, txh, col, map) {
    /*
    1. Fetch a template
    2. Apply any variables like latitude, longitude, altitude
    3. Send to api
    4. Put on map
    */
    template.transmitter.lat = lat;
    template.transmitter.lon = lon;
    template.transmitter.alt = txh;
    template.transmitter.frq = 1800;

    // Antenna settings for 120 deg panel
    template.antenna.txg = 12;
    template.antenna.azi = azi;
    template.antenna.tlt = 0;
    template.antenna.ant = 16322; // COMMSCOPE_HBX-6516DS-VTM_2110_00NELH04NQT804JQWB.ADF
    template.antenna.hbw = 120;
    template.antenna.vbw = 60;

    // Colour key is GREEN #2
    template.output.col = col;
    template.output.rad = 3;
    template.output.res = 10;

    // Mobile UE
    template.receiver.rxs = -105;
    template.receiver.rxg = 1;

    let JSONtemplate = JSON.stringify(template, null, 4);
    CloudRFAreaAPI(JSONtemplate, map);
}

function displayAlertMessage(message) {
    $('#dangerAlert').removeClass('d-none').html(message);
}

function hideAlertMessage() {
    $('#dangerAlert').addClass('d-none')
}

function validateApiKey() {
    hideAlertMessage()

    if(!apiKey) displayAlertMessage('You do not have an API key set!');
}

function CloudRFAreaAPI(request, slippyMap) {
    validateApiKey();

    $('#requestRawOutput').html(request)

    let xhr = new XMLHttpRequest();
    xhr.withCredentials = false;
    xhr.addEventListener("readystatechange", function () {
        if (this.readyState === 4) {
            responseJson = JSON.parse(this.responseText)
            $('#responseRawOutput').html(JSON.stringify(responseJson, null, 4))
            AreaCallback(this.responseText, slippyMap);
        }
    });
    xhr.open("POST", `${apiServiceBaseUrl}/area`);
    xhr.setRequestHeader("key", apiKey);
    xhr.send(request);
}

function CloudRFPathAPI(request, slippyMap) {
    validateApiKey();

    $('#requestRawOutput').html(request)

    let xhr = new XMLHttpRequest();
    xhr.withCredentials = false;
    xhr.addEventListener("readystatechange", function () {
        if (this.readyState === 4) {
            responseJson = JSON.parse(this.responseText)
            $('#responseRawOutput').html(JSON.stringify(responseJson, null, 4))
            PathCallback(this.responseText, slippyMap);
        }
    });
    xhr.open("POST", `${apiServiceBaseUrl}/path`);
    xhr.setRequestHeader("key", apiKey);
    xhr.send(request);
}

function CloudRFPointsAPI(request, slippyMap) {
    validateApiKey();

    $('#requestRawOutput').html(request)

    let xhr = new XMLHttpRequest();
    xhr.withCredentials = false;
    xhr.addEventListener("readystatechange", function () {
        if (this.readyState === 4) {
            responseJson = JSON.parse(this.responseText)
            $('#responseRawOutput').html(JSON.stringify(responseJson, null, 4))
            PointsCallback(this.responseText, slippyMap);
        }
    });
    xhr.open("POST", `${apiServiceBaseUrl}/points`);
    xhr.setRequestHeader("key", apiKey);
    xhr.send(request);
}

// Leaflet only :p
function PathCallback(text) {

    // Clear the map first
    map.eachLayer((layer) => {
        if (layer.options.title === "link") {
            map.removeLayer(layer);
        }
    })

    var json = JSON.parse(text);
    var rxlat = json.Receiver[0].Latitude;
    var rxlon = json.Receiver[0].Longitude;
    var txlat = json.Transmitters[0].Latitude;
    var txlon = json.Transmitters[0].Longitude;

    var latlngs = [
        [rxlat, rxlon],
        [txlat, txlon]
    ];
    console.log(json);

    // Signal strength test
    style = 'red';
    threshold1 = -90;
    threshold2 = -70;
    if (json.Transmitters[0]["Signal power at receiver dBm"] > threshold1) {
        style = 'orange';
    }
    if (json.Transmitters[0]["Signal power at receiver dBm"] > threshold2) {
        style = 'green';
    }
    // Draw a line
    var polyline = L.polyline(latlngs, { color: style, title: "link" }).addTo(map);

    // Pull the PNG image
    $('#chartImage').remove();
    $(`<img id="chartImage" class="w-100" src="${json["Chart image"]}" />`).insertBefore('#responseRawOutput');
}

// Leaflet only :p
function PointsCallback(text) {

    // Clear the map first
    map.eachLayer((layer) => {
        if (layer.options.title === "link") {
            map.removeLayer(layer);
        }
    })

    var json = JSON.parse(text);
    var rxlat = json.Receiver[0].Latitude;
    var rxlon = json.Receiver[0].Longitude;

    for (i = 0; i < json.Transmitters.length; i++) {
        cpelat = json.Transmitters[i].Latitude;
        cpelon = json.Transmitters[i].Longitude;

        var latlngs = [
            [rxlat, rxlon],
            [cpelat, cpelon]
        ];

        // Signal strength test
        style = 'red';
        threshold1 = -90;
        threshold2 = -70;
        if (json.Transmitters[i]["Signal power at receiver dBm"] > threshold1) {
            style = 'orange';
        }
        if (json.Transmitters[i]["Signal power at receiver dBm"] > threshold2) {
            style = 'green';
        }
        // Draw a line
        var polyline = L.polyline(latlngs, { color: style, title: "link" }).addTo(map);
    }
}

// Leaflet and openlayers methods
function AreaCallback(text, slippyMap) {
    var json = JSON.parse(text);
    console.log(text);
    if (slippyMap === "leaflet") { // Leaflet bounds are SOUTH,WEST, NORTH, EAST
        var boundsNESW = json.bounds; // CloudRF uses NORTH,EAST,SOUTH,WEST
        var imageBounds = [[boundsNESW[2], boundsNESW[3]], [boundsNESW[0], boundsNESW[1]]];
        L.imageOverlay(
            $('input[name="calculationEngine"]:checked').val() == 1 ? json.PNG_WGS84 : json.PNG_Mercator, 
            imageBounds
        )
        .setOpacity($('input[name="calculationEngine"]:checked').val() == 1 ? 0.9 : 0.5)
        .addTo(map);
    }
    if (slippyMap === "mapbox") { // Leaflet bounds are SOUTH,WEST, NORTH, EAST
        var boundsNESW = json.bounds; // CloudRF uses NORTH,EAST,SOUTH,WEST
        var imageBounds = [[boundsNESW[2], boundsNESW[3]], [boundsNESW[0], boundsNESW[1]]];
        //L.imageOverlay(json.PNG_Mercator, imageBounds).setOpacity(0.5).addTo(map);
        if (map.isSourceLoaded('cloudrf')) {
            map.removeLayer('cloudrf-layer');
            map.removeSource('cloudrf');
        }
        map.addSource('cloudrf', {
            'type': 'image',
            'url': $('input[name="calculationEngine"]:checked').val() == 1 ? json.PNG_WGS84 : json.PNG_Mercator,
            'coordinates': [
                [boundsNESW[3], boundsNESW[0]],
                [boundsNESW[1], boundsNESW[0]],
                [boundsNESW[1], boundsNESW[2]],
                [boundsNESW[3], boundsNESW[2]]
            ]
        });
        map.addLayer({
            id: 'cloudrf-layer',
            'type': 'raster',
            'source': 'cloudrf',
            'paint': {
                'raster-fade-duration': 0,
                'raster-opacity': $('input[name="calculationEngine"]:checked').val() == 1 ? 0.9 : 0.5
            }
        });
    }
    if (slippyMap === "openlayers") {
        var boundsNESW = json.bounds; // CloudRF uses NORTH,EAST,SOUTH,WEST
        var boundsWSEN = [boundsNESW[3], boundsNESW[2], boundsNESW[1], boundsNESW[0]];

        // Create an image layer
        var imageLayer = new ol.layer.Image({
            opacity: $('input[name="calculationEngine"]:checked').val() == 1 ? 0.9 : 0.5,
            source: new ol.source.ImageStatic({
                url: $('input[name="calculationEngine"]:checked').val() == 1 ? json.PNG_WGS84 : json.PNG_Mercator,
                projection: map.getView().getProjection(),
                imageExtent: ol.proj.transformExtent(boundsWSEN, 'EPSG:4326', 'EPSG:3857')
            })
        });
        console.log(imageLayer);
        map.addLayer(imageLayer);
    }
}
