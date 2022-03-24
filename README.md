## Cloud-RF API clients
These code examples will automate the your RF modelling and integrate your app(s) with the powerful Cloud-RF API for path, area, points and network calculations.

Designed for any operating system with examples for Linux, MacOS and Windows they can be operated as standalone apps or with a spreadsheet of data in CSV and JSON formats.
An internet connection and account at https://cloudrf.com is required.

## PATH DEMO
A live demo of a lightweight "point to point" capability using radio templates to hide complexity and reduce error.
https://cloud-rf.github.io/CloudRF-API-clients/APIv2/Slippy%20maps/leaflet_path.html

![Ibiza VHF coverage with 3D buildings ](https://cloudrf.com/files/ibiza.vhf.jpg)
### Commercial use
You are free to use this API in commercial apps, even ones where you charge customers. 
Attribution is welcomed but not required.
Full terms and conditions are here: https://cloudrf.com/terms-and-conditions
You will be responsible for your account and how it is used. 

####  API technical description
A standard HTTP request with a JSON body with authentication in the HTTP header as a 'key'. The JSON body is a nested object with human readable sections eg. Transmitter->Antenna, Receiver->Antenna.

API endpoints are versioned as /v1/ for the legacy API and /v2/ for the current API.

## /v2 OpenAPI 3.0 specification (Swagger)
https://cloudrf.com/documentation/developer/swagger-ui/

### /v1 Legacy API
The legacy API with the long URLs was deprecated in June 2021. Documentation is [here](https://documenter.getpostman.com/view/3523402/7TFGb35)

# Hello world!
This simple cURL command creates a 5km radius point-to-multipoint at 25m resolution.  

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
            "res": 25,
            "rad": 5
        }
    }'

### Authentication
Authentication is required and looks like a long string which starts with a number, then a hyphen, then a long random string eg. 123-deadbeef
You should protect your API key as it can be used to create, view and delete calculations associated with your account.
To get a key, signup for an account at https://cloudrf.com

### Demo key
If you don't want to sign up for an account you can exercise the API using the following public use API key which is **limited to the island of Ibiza for testing**. You may be asked to wait if someone else is using the key as it is rate limited..

    uid = 101
    key = IBIZA.DEMO.KEY

*Ibiza is a Mediterranean island east of Spain which we have re-branded the "RF-party island". Ibiza's rugged terrain and coastlines are ideal for demonstrating RF propagation modelling.*
Map: https://www.google.com/maps/place/Ibiza/

### Documentation
Introduction https://cloudrf.com/documentation/introduction.html

3D interface https://cloudrf.com/documentation/interface.html

Postman code examples https://docs.cloudrf.com

Swagger (OAS3) spec https://cloudrf.com/documentation/developer/swagger-ui/

User documentation: https://cloudrf.com/documentation

Video tutorials: https://youtube.com/cloudrfdotcom

## Examples

### Point-to-multipoint "heatmap"  x3
The CSV file contains the sites and the JSON file contains the template for the transmitter/receiver/environment etc. Unique values (Latitude,Longitude) belong in the CSV and common criteria (Frequency, Power) belong in the JSON.

    python3 area.py -i 3sites.csv -t drone.json

### Point-to-point link
As before but this time a receiver location is defined.

    python3 path.py -i link.csv -t drone.json
    
### Route analysis 
A route of "points" is tested in a single call. The points object is an array of tuples (lat,lon,alt) in quotes as follows:
"[(38.916, 1.411, 1), (38.919, 1.411, 1), (38.922, 1.411), (38.93, 1.427), (38.921, 1.448), (38.976, 1.44)]"

    python3 points.py -i route.csv -t drone.json
    
### Network analysis
A previously created network is tested against a customer location for service.
This requires a network to exist in your account.

    python3 network.py -i network.csv
    
## Advanced
All programs come with a help menu which you can show with either -h or /?

### Outputs
Options vary by application but you can download outputs in different formats including KML, KMZ, GeoTIFF, SHP and ZIP.

### Handling data where every row has unique values
If there are no common criteria you can put every setting into a spreadsheet with unique column names and then use a 'custom' template with matching override tags on each option. You pick the column names - so long as they align to the right place in the JSON.

## Ingesting data from Tower Coverage

An example for using formatted data from Tower Coverage:

    python3 area.py -i towercoverage.csv -t custom.json

Note that the tower coverage API has Tx power in dBm and in CloudRF Tx the unit is Watts. Antenna codes are unique to the system so will also need re-mapping.
A calculator is here: https://www.rapidtables.com/convert/power/dBm_to_Watt.html

## Code and examples

We have example clients for Bash, Python, OpenLayers and LeafletJS.
If you'd like one adding email support@cloudrf.com



