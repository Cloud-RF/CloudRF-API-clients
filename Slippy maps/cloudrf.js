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
var key = "101-IBIZA.DEMO.KEY"; // Look after your API key. You can hide it by putting a proxy script


// You can edit this JSON template using any parameter from https://docs.cloudrf.com
// For extra points, create multiple templates to have many radios in your tool

var template = {
  "site": "DEMO",
  "network": "DEMO",
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
  "environment": {
      "clm": 1,
      "cll": 2,
      "mat": 0.5
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

// Simplest use. Point-to-multimpoint around a location with fixed settings
function createRFLayer(lat,lon,map){
  /*
  1. Fetch a template
  2. Apply any variables like latitude, longitude, altitude
  3. Send to api
  4. Put on map
  */
  template.transmitter.lat = lat;
  template.transmitter.lon = lon;

  var JSONtemplate = JSON.stringify(template);
  CloudRFAreaAPI(JSONtemplate,map);
}

// Advanced use. Point-to-multipoint with antenna azimuth and customised parameters
function createRFSector(lat,lon,azi,txh,col,map){
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

  var JSONtemplate = JSON.stringify(template);
  CloudRFAreaAPI(JSONtemplate,map);
}

function CloudRFAreaAPI(request,slippyMap){
  var xhr = new XMLHttpRequest();
  xhr.withCredentials = false;
  xhr.addEventListener("readystatechange", function() {
    if(this.readyState === 4) {
      AreaCallback(this.responseText,slippyMap);
    }
  });
  xhr.open("POST", "https://api.cloudrf.com/area");
  xhr.setRequestHeader("key", key);
  xhr.send(request);
}

// Leaflet and openlayers methods
function AreaCallback(text,slippyMap){
  var json =  JSON.parse(text);
  console.log(text);
  if(slippyMap === "leaflet"){ // Leaflet bounds are SOUTH,WEST, NORTH, EAST
    var boundsNESW = json.bounds; // CloudRF uses NORTH,EAST,SOUTH,WEST
    var  imageBounds = [[boundsNESW[2], boundsNESW[3]], [boundsNESW[0], boundsNESW[1]]];
    L.imageOverlay(json.PNG_Mercator, imageBounds).setOpacity(0.5).addTo(map);
  }
  if(slippyMap === "mapbox"){ // Leaflet bounds are SOUTH,WEST, NORTH, EAST
    var boundsNESW = json.bounds; // CloudRF uses NORTH,EAST,SOUTH,WEST
    var  imageBounds = [[boundsNESW[2], boundsNESW[3]], [boundsNESW[0], boundsNESW[1]]];
    //L.imageOverlay(json.PNG_Mercator, imageBounds).setOpacity(0.5).addTo(map);
    if(map.isSourceLoaded('cloudrf')){
      map.removeLayer('cloudrf-layer');
      map.removeSource('cloudrf');
    }
    map.addSource('cloudrf', {
    'type': 'image',
    'url': json.PNG_Mercator,
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
    'raster-opacity': 0.5
    }
    });
  }
  if(slippyMap === "openlayers"){
    var boundsNESW = json.bounds; // CloudRF uses NORTH,EAST,SOUTH,WEST
    var boundsWSEN = [boundsNESW[3],boundsNESW[2],boundsNESW[1],boundsNESW[0]];

    // Create an image layer
    var imageLayer = new ol.layer.Image({
        opacity: 0.5,
        source: new ol.source.ImageStatic({
            url: json.PNG_Mercator,
            projection: map.getView().getProjection(),
            imageExtent: ol.proj.transformExtent(boundsWSEN, 'EPSG:4326', 'EPSG:3857')
        })
    });
    console.log(imageLayer);
    map.addLayer(imageLayer);
  }
}
