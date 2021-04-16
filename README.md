## Cloud-RF API clients
These code examples will help you integrate your app(s) with the powerful Cloud-RF API for path, area and whole network calculations. Designed for any operating system with examples for Linux, MacOS and Windows they can be operated as standalone apps with a CSV spreadsheet of data.

![Ibiza VHF coverage with 3D buildings ](https://cloudrf.com/files/ibiza.vhf.jpg)
### Commercial use is ok, reselling is not
The Cloud-RF API is typically used for front office with a custom branded interface, back office processing with network data and network maps with dynamic updates. If you have just discovered mapbox and now want to to resell access to our API you must seek written authorisation by emailing support@cloudrf.com
Full terms and conditions are here: https://cloudrf.com/terms-and-conditions

### Authentication
Authentication is required. This consists of a user identifier (uid) and a private key (key).
You should protect your API key as it can be used to create, view and delete calculations associated with your account.
To get a uid and key, signup for an account at https://cloudrf.com
### Demo key
If you don't want to sign up for an account you can exercise the API using the following public use API key which is **limited to the island of Ibiza for testing**. You may be asked to wait if someone else is using the key as it is rate limited..

    uid = 101
    key = IBIZA.DEMO.KEY
    
*Ibiza is a Mediterranean island east of Spain which we have re-branded the "RF-party island". Ibiza's rugged terrain and coastlines are ideal for demonstrating RF propagation modelling.*

### Documentation
API reference https://api.cloudrf.com
User documentation: https://cloudrf.com/docs
Video tutorials: https://youtube.com/cloudrfdotcom

### Preparing the configuration file
These examples use a configuration file called **cloudrf.ini** which contains your credentials, API endpoint (for private servers) and a folder path for downloads such as KMZ files. 

    [user]
	uid = 101
	key = IBIZA.DEMO.KEY
	
	[api]
	base_url = https://cloudrf.com
	strict_ssl = True
	
	[data]
	dir = out

### Preparing your data
The HTTP API accepts key-value parameters where frq=868 is "Frequency 868MHz" 
These examples use a comma separated values (CSV) format for processing rows of data but you can use any structured data in your clients and any programming language. 

If data is missing required fields (frequency, height, location...) it will reject the row with an error. If a field is included but out of bounds like a height of -100m it will reject the row with an error. For a list of fields and acceptable parameters see https://api.cloudrf.com

# Cloud-RF API "Hello world!" 
Impress your Boss and paste this URL into your browser to make a 868MHz heatmap:

    https://cloudrf.com/API/area?res=30&col=RAINBOW.dBm&rxs=-120&rad=10&frq=868&pm=1&cll=0&azi=0&txw=0.1&fmt=4&out=2&net=IBIZA&nam=hello_world&txg=2.15&tlt=0&ant=39&dis=m&rxg=2.15&uid=101&key=IBIZA.DEMO.KEY&txh=8&rxh=1&lat=38.916&lon=1.448

![Ibiza UHF coverage](https://cloudrf.com/files/helloworld.kmz.jpg)
The response will be a JSON object which contains links to different formats and image metadata such as the coverage area in squared km. There are two different images for different map types: PNG_Mercator for a 2D web/leaflet map or PNG_WGS84 for a 3D Google Earth/Cesium map.

	{
	"kmz": "https://cloudrf.com/API/archive/data?file=0415165022_IBIZA_hello_world&uid=101&fmt=kmz&key=IBIZA.DEMO.KEY",
	"PNG_WGS84": "https://cloudrf.com/users/101/0415165022_IBIZA_hello_world.4326.png",
	"PNG_Mercator": "https://cloudrf.com/users/101/0415165022_IBIZA_hello_world.3857.png",
	"bounds": [39.03145,1.563455,38.80055,1.332545],
	"id": "13896",
	"sid": "NVVoMHpSWUhUVk5aNFN3VHg3dkJ2dz09",
	"area": "33.965 km2",
	"coverage": "11%",
	"key": [],
	"elapsed": 1683,
	"balance": "1"
	}

# Area API
The area API (Point to multipoint) produces heatmap images which you can overlay on a map. You need to define settings for a location, a transmitter, receiver(s), environment and the model.
![Radio coverage heatmap](https://cloudrf.com/files/cll0.png)
## Processing speed
The time an area coverage call takes is determined by two key parameters, **resolution (res) in metres and radius (rad) in kilometres**. A coarse resolution (60) and low radius (5) could take under a second. A fine resolution (5) and high radius (50) could take a minute. The API engine, Sleipnir, is faster than open source engines but it's not magic and still has to do *lots* of trigonometry. 
For best performance you are recommended to pick a resolution which matches your requirements and a radius no further than you need. A good resolution for a wide area plot in the countryside would be 30(m) whilst a good resolution for inside a city with LiDAR would be 5(m). Very rarely will you get a better result going lower than 5m.

## Python
The python example uses a list of pre-defined sites for a Drone flight from a CSV file.
To use it you need to specify an input file ( -i ) as a minimum. Add verbosity ( -v) and responses ( -r ) ) to get more details. This example will generate some coastal plots around Ibiza and download the KMZ layer only.

    python3 area.py -i area.csv

All parameters are described with --help:

    python3 area.py --help
	CloudRF API demo
	usage: area.py [-h] [-i data_file [data_file ...]]
	               [-s {kmz,kml,kmzppa,shp,tiff,url,html,all} [{kmz,kml,kmzppa,shp,tiff,url,html,all} ...]]
	               [-o output_dir] [-r] [-v]

	CloudRF Area application

	Area coverage performs a circular sweep around a transmitter out to a user defined radius.
	It factors in system parameters, antenna patterns, environmental characteristics and terrain data
	to show a heatmap in customisable colours and units.

	This demonstration program utilises the CloudRF Area API to generate any
	of the possible file outputs offered by the API from ['kmz', 'kml', 'kmzppa', 'shp', 'tiff', 'url', 'html'].
	The API arguments are sourced from csv file(s).
	please use -s all to generate ALL outputs available.

	Please refer to API Reference https://api.cloudrf.com/

	optional arguments:
	  -h, --help            show this help message and exit
	  -i data_file [data_file ...]
	                        data input filename(csv)
	  -s {kmz,kml,kmzppa,shp,tiff,url,html,all} [{kmz,kml,kmzppa,shp,tiff,url,html,all} ...]
	                        type of output file to be downloaded
	  -o output_dir         output directory where files are downloaded
	  -r                    save response content (json/html)
	  -v                    Output more information on screen


## Bash
A Bash script to also calculate sites, parse the JSON and fetch the KMZ files:

     ./area.bash -i area.csv

Script options available with -h switch:

     ./area.bash -h
	area.bash API demo
	usage: area.py [-h] [-i data_file] [-o output_dir] [-r] [-v]

	CloudRF Area application

	Area coverage performs a circular sweep around a transmitter out to a user defined radius.
	It factors in system parameters, antenna patterns, environmental characteristics and terrain data
	to show a heatmap in customisable colours and units.

	This demonstration program utilises the CloudRF Area API to generate a kmz output
	The API arguments are sourced from csv file(s).

	Please refer to API Reference https://api.cloudrf.com/

	arguments:
	  -h, --help            show this help message and exit
	  -i data_file          data input filename(csv)
	  -o output_dir         output directory where files are downloaded
	  -r                    save response content (json/html)
	  -v                    Output more information on screen

# Path API
The path profile analysis API takes the same inputs as the area API plus a destination. Unlike an area calculation, this fast API call is focused on just one link / path.
The destination is set with the receiver latitude (rla) and receiver longitude (rlo) values as decimal degrees.
![Path Profile Analysis](https://cloudrf.com/files/ibiza.path.png)

## Python
This example calculates paths from a spreadsheet / CSV file. For each path it requests a PNG image instead of the JSON output (default). The JSON output contains a substantial amount of data about a path including obstacle locations, recommended heights to clear fresnel zones and landcover codes and heights.

    python3 path.py -i path.csv
	   downloading from https://cloudrf.com/API/archive/data?file=0415195224_DRONE_PATH_A1&uid=101&fmt=kmz&key=IBIZA.DEMO.KEY
	   downloading from https://cloudrf.com/API/archive/data?file=0415195225_DRONE_PATH_A2&uid=101&fmt=kmz&key=IBIZA.DEMO.KEY

    
## Bash
The bash example parses the JSON to return just the received power in dBm.

    ./path.bash -i path.csv
	  api_end_point=https://cloudrf.com/API/area
	  "Signal power at receiver dBm": -125.4 
	  "Signal power at receiver dBm": -84.8 
	  "Signal power at receiver dBm": -131.6 

# Network API
The network "best server" API is an automated sequence of path profile calculations against adjacent nodes in a network. To use it, you must have a network defined at the API already (using the area API).
Used properly it is the most powerful of all CloudRF's APIs as it can show detailed information about coverage at a location in near real-time and is well suited to integration into a third party map or interface.
![Best server analysis](https://cloudrf.com/files/ibiza.network.jpg)
## Python
The python demo script parses the JSON then downloads the linked PNG image from the server with a second call. This is slower than just parsing the signal power from the JSON due to on-demand image creation at the server.

    python3 network.py -i network.csv
	CloudRF API demo
	Reading data from ['network.csv']
	Will download ['chart']
	All files generated to out
	Network "best server" API demo
	Querying location for best server(s):
	url https://cloudrf.com/API/archive/data?ppa=0853ee63&uid=101
	saving 0853ee63.png
	url https://cloudrf.com/API/archive/data?ppa=365cdfe1&uid=101
	...
	


## Bash
The Bash demo script parses the JSON to extract the signal power for each link in the network DRONE_PATH.

    ./network.bash -i network.csv 
	api_end_point=https://cloudrf.com/API/network/
	"Server ID": 13773 
	"Distance to receiver km": 0.087 
	"Signal power at receiver dBm": -64.9 
	"Server ID": 7131 
	"Distance to receiver km": 0.087 
	"Signal power at receiver dBm": -65.5 
	...

# Advanced topics
 ## Clutter and attenuation
 CloudRF employs a more pragmatic approach to clutter definition than legacy premium tools which expected users to concern themselves with the attenuation coefficients for timber, bricks, concrete, trees, trees in winter, trees in summer and so on for every meter of every city... This design works if you are focused on accurate planning in one city (and the eye watering price of this data limits the scope) but falls over as soon as you move out of that city/area of focus...
 
If you set a res value of 16(m) or lower, the API will use LiDAR/Photogrammetry data if available and add 3D buildings, if available, for your area of interest on top of the surface model. An obstacles attenuation is defined with the material (mat) coefficient which supports every type of obstacle from "sparse deciduous woods (in winter)" to good old concrete.

cll = Clutter mode. 0 = OFF, 1 = HARD / LOS, 2 = SOFT / NLOS
mat = Material attenuation coefficient. 0.001 to 1.0 dB/m

Here are three examples of the same urban site at 5m resolution / 1km radius, where there is a surface model and 3D buildings available. Changing the cll and mat values produces three very different plots using the same surface model:

    Clutter OFF:
        https://cloudrf.com/API/area?res=8&col=RAINBOW.dBm&rxs=-120&rad=1&frq=868&pm=1&azi=0&txw=0.1&fmt=4&out=2&net=IBIZA&nam=hello_world&txg=2.15&tlt=0&ant=39&dis=m&rxg=2.15&uid=101&key=IBIZA.DEMO.KEY&txh=4&rxh=2&lat=38.9105&lon=1.4292&cll=0
      
    Clutter HARD  / LOS
        https://cloudrf.com/API/area?res=8&col=RAINBOW.dBm&rxs=-120&rad=1&frq=868&pm=1&azi=0&txw=0.1&fmt=4&out=2&net=IBIZA&nam=hello_world&txg=2.15&tlt=0&ant=39&dis=m&rxg=2.15&uid=101&key=IBIZA.DEMO.KEY&txh=4&rxh=2&lat=38.9105&lon=1.4292&cll=1
     
    Clutter SOFT  / NLOS with 0.1 dB/m attenuation
        https://cloudrf.com/API/area?res=8&col=RAINBOW.dBm&rxs=-120&rad=1&frq=868&pm=1&azi=0&txw=0.1&fmt=4&out=2&net=IBIZA&nam=hello_world&txg=2.15&tlt=0&ant=39&dis=m&rxg=2.15&uid=101&key=IBIZA.DEMO.KEY&txh=4&rxh=2&lat=38.9105&lon=1.4292&cll=2&mat=0.1

![Clutter OFF](https://cloudrf.com/files/cll0.png)![Clutter HARD / LOS](https://cloudrf.com/files/cll1.png)![Clutter SOFT / NLOS](https://cloudrf.com/files/cll2.mat0.1.png)
## Antenna patterns

CloudRF has over 26k antenna patterns in its database from different manufacturers, each with a unique code. #39 is a half wave dipole. #0 is a custom pattern...
An antenna pattern and direction/azimuth can be specified with "ant" and "azi".

![Polar plot vertical](https://cloudrf.com/files/antenna.v.jpg)![Polar plot horizontal](https://cloudrf.com/files/antenna.h.jpg)
If you want to define a custom pattern you can do this with the beamwidth parameters: "hbw", "vbw" and "fbr" which are Horizontal beamwidth (degrees), vertical beamwidth (degrees) and front-to-back ratio as dB. If you are not sure about fbr just use the gain value (txg).

A 120 degree panel, with 9dBi gain, orientated east would look like:

    ...&ant=0&hbw=120&vbw=120&txg=9&fbr=9&azi=90

*TIP: You can visually create patterns in the CloudRF web interface to see what the polar plots for different parameters looks like.*

