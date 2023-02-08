# API v2 examples
These examples use API 2.0 and a default configuration with the Ibiza demo key in cloudrf.ini:

    [user]
	key = 101-IBIZA.DEMO.KEY

	[api]
	strict_ssl = True
	base_url = https://api.cloudrf.com/v2

	[data]
	dir = out

# Hello world!
This simple cURL command creates a 5km radius point-to-multipoint at 20m resolution. The API key is passed in the header and the settings go in the body as JSON. 

    curl --location --request POST 'https://api.cloudrf.com/v2/area' \
    --header 'key: 101-IBIZA.DEMO.KEY' \
    --data-raw '{
        "site": "VHF160",
        "network": "APITEST",
        "transmitter": {
            "lat": 38.916,
            "lon": 1.448,
            "alt": 12,
            "frq": 160,
            "txw": 5,
            "bwi": 0.1
        },
        "receiver": {
            "lat": 0,
            "lon": 0,
            "alt": 0.1,
            "rxg": 2.15,
            "rxs": -100
        },
        "antenna": {
            "txg": 2.15,
            "txl": 0,
            "ant": 1,
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
            "mat": 0.25
        },
        "output": {
            "units": "metric",
            "col": "RAINBOW.dBm",
            "out": 2,
            "ber": 0,
            "mod": 0,
            "nf": -114,
            "res": 20,
            "rad": 5
        }
    }'

# Python3
Fetch the requirements from requirements.txt with pip:
		
    python3 -m pip install -r requirements.txt

###  Drone broadcast via AREA api
This will calculate 3 **point-to-multipoint** sites defined in the CSV file. Each site will be saved as a KMZ in the output folder.
The receiver lat/lon is ZERO as this is an omni-directional plot.

	python3 area.py -i 3sites.csv -t templates/drone.json

###  Drone broadcast via AREA api and super layer with MESH api
This will calculate 3 **point-to-multipoint** sites defined in the CSV file. Each site will be saved as a KMZ in the output folder.
The sites will then be merged using the mesh API into a super layer which is also downloaded as a KMZ.
WARNING: Use your own account OR an original network name in the CSV for this one as the '101' test account will likely contain random data.

	python3 area.py -i 3sites.csv -t templates/drone.json -m APITEST1

### Drone link via PATH api
This will calculate a single **point-to-point**, then display the JSON in the console and fetch the PNG chart to the output folder. 
The receiver lat/lon is defined as this is a link.

    python3 path.py -i link.csv -t templates/drone.json

### Drone path via POINTS api
This will calculate multiple **point-to-point** links in fast succession, **in reverse** from the transmitters back to a fixed receiver.
The receiver lat/lon is defined and the transmitters are in the CSV as tuples in a quoted array: "[(38.916, 1.411, 1), (38.919, 1.411, 1), (38.922, 1.411)]".

    python3 points.py -i route.csv -t templates/drone.json

### Best server check via NETWORK api
This will test a network for the best nearby sites. You must have already created sites for this to work.
The network file is simple and contains only the network name and customer location.

Example CSV data for network.csv:

    net,lat,lon,rxh,rxg
    DRONE_PATH,38.914,1.451,2,2.15

Example command:

    python3 network.py -i network.csv
    
### Validate drive test data from NEMO handy
If you have RSRP readings for a cell site in a CSV spreadsheet and know your tower parameters you can use the path API to find the error in your modelling parameters, and then improve them.
A good error should be < 10dB.


    python3 drivetest.py -t templates/enodeb.json -i drivetestdata.csv
	
	CloudRF API demo
	Reading data from ['drivetestdata.csv']
	Drivetest demo via /path API. CSV data should contain columns: rlat,rlon,measured
	Latitude	Longitude	Received	Modelled	Difference	Distance
	RxLat: 20.08488 RxLon: -97.99688 Measured: -67.7dBm Modelled: -40.7dBm Difference: 27dB Distance: 34m
	RxLat: 20.08449 RxLon: -97.99681 Measured: -69.6dBm Modelled: -46.4dBm Difference: 23dB Distance: 61m
	RxLat: 20.08347 RxLon: -97.99661 Measured: -81.2dBm Modelled: -54.7dBm Difference: 26dB Distance: 171m
	RxLat: 20.08248 RxLon: -97.99680 Measured: -85.5dBm Modelled: -62.9dBm Difference: 23dB Distance: 272m
	RxLat: 20.08149 RxLon: -97.99694 Measured: -84.2dBm Modelled: -65.3dBm Difference: 19dB Distance: 381m
	RxLat: 20.08075 RxLon: -97.99754 Measured: -104.3dBm Modelled: -63.2dBm Difference: 41dB Distance: 463m
	RxLat: 20.08047 RxLon: -97.99799 Measured: -99.5dBm Modelled: -66.9dBm Difference: 33dB Distance: 500m
	RxLat: 20.07949 RxLon: -97.99812 Measured: -107.7dBm Modelled: -93.7dBm Difference: 14dB Distance: 610m
	RxLat: 20.07850 RxLon: -97.99784 Measured: -109.4dBm Modelled: -85.1dBm Difference: 24dB Distance: 716m
	RxLat: 20.07749 RxLon: -97.99784 Measured: -105.9dBm Modelled: -91.4dBm Difference: 14dB Distance: 827m
	RxLat: 20.07648 RxLon: -97.99803 Measured: -108.7dBm Modelled: -87.4dBm Difference: 21dB Distance: 941m
	RxLat: 20.07547 RxLon: -97.99821 Measured: -105.5dBm Modelled: -81.2dBm Difference: 24dB Distance: 1055m
	RxLat: 20.07447 RxLon: -97.99843 Measured: -111.0dBm Modelled: -89.6dBm Difference: 21dB Distance: 1168m
	RxLat: 20.07368 RxLon: -97.99851 Measured: -112.0dBm Modelled: -105.1dBm Difference: 7dB Distance: 1256m
	RxLat: 20.07349 RxLon: -97.99865 Measured: -109.5dBm Modelled: -98.5dBm Difference: 11dB Distance: 1279m
	RxLat: 20.07262 RxLon: -97.99950 Measured: -116.5dBm Modelled: -72.4dBm Difference: 44dB Distance: 1388m
	RxLat: 20.07248 RxLon: -97.99965 Measured: -118.6dBm Modelled: -72.1dBm Difference: 46dB Distance: 1406m
	RxLat: 20.07093 RxLon: -98.00095 Measured: -112.0dBm Modelled: -105.0dBm Difference: 7dB Distance: 1604m
	RxLat: 20.07153 RxLon: -98.00107 Measured: -112.4dBm Modelled: -111.0dBm Difference: 1dB Distance: 1543m
	RxLat: 20.07196 RxLon: -98.00152 Measured: -108.8dBm Modelled: -93.6dBm Difference: 15dB Distance: 1510m
	RxLat: 20.07149 RxLon: -98.00240 Measured: -97.8dBm Modelled: -77.3dBm Difference: 20dB Distance: 1589m
	RxLat: 20.07099 RxLon: -98.00253 Measured: -101.0dBm Modelled: -94.3dBm Difference: 7dB Distance: 1646m



