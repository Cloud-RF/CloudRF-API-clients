## Cloud-RF API clients
These code examples will automate the your RF modelling and integrate your app(s) with the powerful Cloud-RF API for path, area, points and network calculations.

Designed for any operating system with examples for Linux, MacOS and Windows they can be operated as standalone apps or with a spreadsheet of data in CSV and JSON formats.
An internet connection and account at https://cloudrf.com is required.

![Ibiza VHF coverage with 3D buildings ](https://cloudrf.com/files/ibiza.vhf.jpg)
### Commercial use
You are free to use this API in commercial apps, even ones where you charge customers, but you **must provide attribution to CloudRF**. If you want an exemption, you need to request written permission via support@cloudrf.com
Full terms and conditions are here: https://cloudrf.com/terms-and-conditions
You will be responsible for your account and how it is used.

####  API technical description
A standard HTTP request with a JSON body with authentication in the HTTP header as a 'key'. The JSON body is a nested object with human readable sections eg. Transmitter->Antenna, Receiver->Antenna.


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


