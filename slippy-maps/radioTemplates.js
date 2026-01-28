var myTemplates = [
    {
        "site": "4GHz parabolic, 21dBi",
        "network": "CloudRF-API-clients-DEMO",
        "transmitter": {
            "lat": 38.916,
            "lon": 1.448,
            "alt": 2,
            "frq": 4000,
            "txw": 1,
            "bwi": 0.1
        },
        "receiver": {
            "lat": 0,
            "lon": 0,
            "alt": 10,
            "rxg": 21,
            "rxs": -99
        },
        "antenna": {
            "txg": 21,
            "txl": 0,
            "ant": 0, // 0 is a custom pattern
            "azi": 0, // azimuth is overridden by our tool
            "tlt": 0,
            "hbw": 5,
            "vbw": 5,
            "fbr": 25,
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
            "cll": 2
        },
        "output": {
            "units": "metric",
            "col": "RAINBOW.dBm",
            "out": 2,
            "nf": -114,
            "res": 10,
            "rad": 2
        }
    },
    {
        "site": "PMR446 2W handheld",
        "network": "CloudRF-API-clients-DEMO",
        "transmitter": {
            "lat": 38.916,
            "lon": 1.448,
            "alt": 2,
            "frq": 446,
            "txw": 2,
            "bwi": 0.1
        },
        "receiver": {
            "lat": 0,
            "lon": 0,
            "alt": 2,
            "rxg": 1,
            "rxs": -99
        },
        "antenna": {
            "txg": 1,
            "txl": 0,
            "ant": 39, // dipole
            "azi": 0, 
            "tlt": 0,
            "pol": "v"
        },
        "model": {
            "pm": 1,
            "pe": 2,
            "cli": 6,
            "ked": 1,
            "rel": 95,
            "ter": 4
        },
        "environment": {
            "clm": 0,
            "cll": 2
        },
        "output": {
            "units": "metric",
            "col": "RAINBOW.dBm",
            "out": 2,
            "nf": -114,
            "res": 10,
            "rad": 3
        }
    }
];