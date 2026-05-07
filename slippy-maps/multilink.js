// https://cloudrf.com/documentation/developer

var c_lat = 51.79407;
var c_lon = -2.09633;
var c_alt = 20;

var drone_count = 30;

const number_range = document.getElementById('number-slider');
const number_label = document.getElementById('number-label');

const dist_range = document.getElementById('dist-slider');
const dist_label = document.getElementById('dist-label');

const lat_range = document.getElementById('lat-range');
const lon_range = document.getElementById('lon-range');
const alt_range = document.getElementById('alt-range');

const request_pre = document.getElementById('requestRawOutput');
const response_pre = document.getElementById('responseRawOutput');

const good_bad_ratio_label = document.getElementById('good-bad-ratio');
const time_label = document.getElementById('time');
const mean_rssi_label = document.getElementById('mean-rssi');

var map = L.map('map', {
    center: [c_lat, c_lon],
    zoom: 13
});
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '<a href="https://cloudrf.com">CloudRF</a> | &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map);

const center_marker = L.marker([c_lat, c_lon], {
    draggable: true
}).addTo(map);

center_marker.bindTooltip("Center");

function map_range(value, i_min, i_max, o_min, o_max) {
    const mapped_val = (value - i_min) * (o_max - o_min) / (i_max - i_min) + o_min;
    return Math.min(o_max, Math.max(o_min, mapped_val));
}

function calculate_point(i, n, radius, lat, lon, alt) {
    const angle = 2 * Math.PI * i / n;

    const x_m = radius * Math.cos(angle);
    const y_m = radius * Math.sin(angle);

    const d_lat = (y_m) / 111320;
    const d_lon = (x_m) / (111320 * Math.cos(lat * Math.PI / 180));

    return {
        lat: lat + d_lat,
        lon: lon + d_lon,
        alt,
    }
}

function rssi_color(v) {
   let colour = 'green'

    if(v < -80){
        colour = 'orange'
    }

    if(v < -90){
        colour = 'red'
    }

    return colour
}

var drones = [];

function clear_drones() {
    drones.forEach(function(d) {
        map.removeLayer(d.marker);
    });

    drones = [];
}

function update_drones() {
    const distance_meters = dist_range.value;

    dist_label.textContent = "Radius: " + distance_meters + "m";

    clear_drones();

    let cols = Math.round(Math.sqrt(drone_count))
    let cc = 1
    let delta = distance_meters / 120000 // degs
    let rowMultiplier = 0
    let colMultiplier = 0

    c_lat = c_lat - (delta * cols)/2
    c_lon = c_lon - (delta * cols)/2

    for (let i = 0; i < drone_count; i++) {
        //let pos = calculate_point(i, drone_count, dist_range.value, c_lat, c_lon, c_alt);
        let latDiff = (rowMultiplier * delta)
        let lonDiff = (colMultiplier * delta)
        let pos = {lat:c_lat+latDiff,lon:c_lon+lonDiff,alt:c_alt}

        if(cc >= cols){
            rowMultiplier++
            cc = 0
            colMultiplier=0
        }else{
            colMultiplier++
        }
        cc++

        const marker = L.circleMarker([c_lat+latDiff, c_lon+lonDiff], {
            radius: 5,
            color: 'black'
        }).addTo(map);

        drones.push({
            pos,
            marker
        });
    }

    const radius = distance_meters / 1;

}

dist_range.addEventListener('input', function() {
    update_drones();

    calculate();
});

update_drones();

function update_number() {
    drone_count = number_range.value;
    number_label.textContent = "Drones: " + drone_count;

    calculate();
}

number_range.addEventListener('input', function() {
    update_number();
    update_drones();

    calculate();
})

update_number();

lat_range.addEventListener('change', function() {
    c_lat = parseFloat(lat_range.value);
    center_marker.setLatLng([c_lat, c_lon]);
    update_drones();

    calculate();
});

lon_range.addEventListener('change', function() {
    c_lon = parseFloat(lon_range.value);
    center_marker.setLatLng([c_lat, c_lon]);
    update_drones();

    calculate();
});

alt_range.addEventListener('change', function() {
    c_alt = parseFloat(alt_range.value);
    update_drones();

    calculate();
});

function calculate_good_bad_ratio(data) {
    try {
        let values = data.values;

        var total_good = 0;
        var total_bad = 0;

        var total_rssi = 0;

        let values_arr = Object.values(values);

        var counter = 1;
        var total_per_node_rssi = 0;

        const per_node_rssis = [];

        values_arr.forEach(function(v) {
            if (v > -80) {
                total_good++;
            } else if (v < -95) {
                total_bad++;
            }

            total_per_node_rssi += v;
            counter++;

            if (counter == drone_count) {
                counter = 1;
                per_node_rssis.push(total_per_node_rssi / (drone_count - 1));
                total_per_node_rssi = 0;
            }

            total_rssi += v;
        });

        let time = data.elapsed;
        let score = (100 * total_good / values_arr.length).toFixed(1)

        good_bad_ratio_label.textContent = "Good:Bad = " + total_good + ":" + total_bad + " (" + (score) + "%)";
        time_label.textContent = "Compute Time = " + time.toFixed(1) + "ms";
        mean_rssi_label.textContent = "Mean RSSI = " + (total_rssi / values_arr.length).toFixed(1) + "dBm";

        if(parseFloat(score) > 66){
            good_bad_ratio_label.style.background = 'green'
        }

        if(parseFloat(score) < 66){
            good_bad_ratio_label.style.background = 'orange'
        }

        if(parseFloat(score) < 50){
            good_bad_ratio_label.style.background = 'red'
        }
        console.log(score)

        per_node_rssis.forEach(function(v, i) {
            drones[i].marker.bindTooltip(`Mean RSSI: ${v.toFixed(2)}dBm`);

            drones[i].marker.setStyle({
                color: rssi_color(v)
            });
        });
    } catch (err) {
        console.error(err);
    }
}


// https://cloudrf.com/documentation/developer
async function calculate() {
    let radios = drones.map(function(d) {
        return {
            "lat": d.pos.lat,
            "lon": d.pos.lon,
            "alt": d.pos.alt,
            "frq": 2220,
            "txw": 0.1,
            "bwi": 1.2,
            "nf": "-100",
            "antenna": {
                "txg": 2,
                "txl": 0,
                "ant": 1,
                "azi": 0,
                "tlt": "0",
                "pol": "v"
            }
        };
    });

    let request =
    {
        "site": "Site",
        "ui": 3,
        "network": "Network",
        "radios": radios,
        "model": {
            "pm": 4,
            "pe": 2,
            "ked": 4,
            "rel": 50
        },
        "environment": {
            "elevation": 2,
            "landcover": 0,
            "buildings": 0,
            "obstacles": 0,
            "clt": "Minimal.clt"
        },
        "output": {
            "units": "m",
            "out": 2,
            "res": "10"
        }
    };

    request_pre.textContent = JSON.stringify(request, null, 2);

    const api_key = document.getElementById("apiKey").value;
    const api_url = document.getElementById("apiServiceBaseUrl").value;

    const url = api_url + "/multilink";

    const response = await fetch(url, {
        method: "POST",
        headers: {
            "key": api_key
        },
        body: JSON.stringify(request)
    });

    const data = await response.json();
    response_pre.textContent = JSON.stringify(data, null, 2);

    if(!data.error){
        console.log(data);
        calculate_good_bad_ratio(data);
    }
}

center_marker.on('dragend', function(event) {
    const pos = event.target.getLatLng();

    c_lat = pos.lat;
    c_lon = pos.lng;

    lat_range.value = c_lat.toFixed(5);
    lon_range.value = c_lon.toFixed(5);

    update_drones();

    calculate();
});


map.on('click', function(e) {
    const pos = e.latlng;

    c_lat = pos.lat;
    c_lon = pos.lng;

    lat_range.value = c_lat.toFixed(5);
    lon_range.value = c_lon.toFixed(5);

    center_marker.setLatLng([c_lat, c_lon]);

    update_drones();

    calculate();
});