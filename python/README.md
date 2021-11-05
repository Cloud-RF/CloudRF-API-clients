# API v2 examples
These examples use API 2.0 and a default configuration with the Ibiza demo key in cloudrf.ini:

    [user]
	key = 101-IBIZA.DEMO.KEY

	[api]
	strict_ssl = True
	base_url = https://api.cloudrf.com

	[data]
	dir = out

# Hello world!
This simple cURL command creates a 5km radius point-to-multipoint at 20m resolution. The API key is passed in the header and the settings go in the body as JSON. 

    curl --location --request POST 'https://api.cloudrf.com/area' \
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
	
# Bash / cURL

###  Drone broadcast via AREA api
This will calculate a **point-to-multipoint** site defined in the CSV file. Each site will be saved as a KMZ.
The receiver lat/lon is ZERO as this is an omni-directional plot.

	./area.bash -i area.csv -t templates/drone.json -o out


### Drone link via PATH api
This will calculate a single **point-to-point**, then display the JSON in the console and fetch the PNG chart to the output folder. 
The receiver lat/lon is defined as this is a link.

       ./path.bash -i path.csv -t templates/drone_path.json -o out


