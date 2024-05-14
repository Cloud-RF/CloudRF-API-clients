import simplekml # type: ignore
from urllib.request import Request, urlopen
import requests
import json
from time import sleep
from math import atan, pi

requests.packages.urllib3.disable_warnings() # dissable warnings from API requests. make terminal clearer

########### CONSTANTS DO NOT CHANGE ###########

FEET_TO_METRES_CONSTANT = 0.3048 # ADSB works in feat, KML works in metres
RF_API_SERVER = "https://api.cloudrf.com" # CloudRF API
RF_API_KEY = "" # API key for CloudRF contained in api-key.txt
ADSB_API_SERVER = "https://api.adsb.lol/v2/callsign/" # ADSB API
REQUEST_HEADERS = {"User-Agent": "Mozilla/5.0"} # dont look like a bot

###############################################


######### FEEL FREE TO CHANGE SETTINGS #########

SIMULATION_RESOLUTION = 200 # resolution in metres
SIMULATION_RADIUS = 90 # simulation radius in metres

SLEEP_TIME = 2 # seconds between each update, 2 recommended

################################################

callsign = input("Enter callsign for plane: ") # get callsign for ADSB API

lon = 0
lat = 0

prevlat = 0
prevlon = 0

with open("api-key.txt") as file:
    RF_API_KEY = file.read().rstrip()

while True:

    kml = simplekml.Kml()

    # make request to ADSB API for plane data
    req = Request(
        url = ADSB_API_SERVER + callsign,
        headers = REQUEST_HEADERS
    )   

    planeData = json.load(urlopen(req)) # load JSON from ADSB request

    if len(planeData["ac"]) > 0: # check if plane has position data

        alt = 0

        if (planeData["ac"][0]["alt_baro"]) != "ground": # check plane is not grounded
            alt = float(planeData["ac"][0]["alt_baro"]) # update altitude

        alt *= FEET_TO_METRES_CONSTANT # ADSB works in feat, KML works in metres

        # update previous latitude and longditude if the plane has moved
        if float(planeData["ac"][0]["lat"]) != lat: prevlat = lat
        if float(planeData["ac"][0]["lon"]) != lon: prevlon = lon

        # update current latitude and longditude
        lat = float(planeData["ac"][0]["lat"])
        lon = float(planeData["ac"][0]["lon"])

        # calculate change in longditude and latitude for heading calculation
        dlat = lat - prevlat
        dlon = lon - prevlon

        heading = 0

        if dlat != 0: # check for zeros in denominator
            heading = atan(dlon / dlat) # calculate heading
            heading *= 180 / pi # convert radians to degrees

        while (heading < 0): heading += 360 # check for negative heading

        data = {                      # parameters send to CloudRF API
            "site": "A1",
            "engine": 1,
            "network": "Testing",
            "transmitter": {
                "lat": lat,
                "lon": lon,
                "alt": alt,
                "frq": 123,
                "txw": 10,
                "bwi": 0.1
            },
            "model": {
                "pm": 7,
                "pe": 2,
                "ked": 0
            },
            "receiver": {
                "lat": 0,
                "lon": 0,
                "alt": 2,
                "rxg": 2,
                "rxs": -100
            },
            "antenna": {
                "txg": 21,
                "txl": 1,
                "ant": 0,
                "azi": int(heading),
                "tlt": 45,
                "hbw": 120,
                "vbw": 120,
                "pol": "v",
                "fbr": 40
            },
            "environment": {
                "elevation": 2,
                "landcover": 0,
                "buildings": 0
            },
            "output": {
                "units": "metric",
                "col": "RAINBOW.dBm",
                "out": 2,
                "ber": 2,
                "mod": 7,
                "nf": -100,
                "res": SIMULATION_RESOLUTION,
                "rad": SIMULATION_RADIUS
            }
        }

        # make request to CloudRF API
        resp = requests.post(RF_API_SERVER + "/area",
                         json = data,
                         headers = {'key': RF_API_KEY},
                         verify = False
                         )

        if "elapsed" in resp.json(): # if a heatmap has been returned
            netlink = kml.newnetworklink(name = "Coverage")
            netlink.link.href = resp.json()["kmz"]
            netlink.link.viewrefreshmode = simplekml.ViewRefreshMode.onrequest

            print(str(resp.json()["elapsed"]) + "ms elapsed calculating heatmap. Press Ctrl+C to stop")

        else: print(resp.json()) # see why no heatmap was returned / what was returned instead

        point = kml.newpoint(name = "Plane " + callsign, coords = [(lon, lat, alt)])  # lon, lat, optional height
        point.altitudemode = simplekml.AltitudeMode.absolute # altitude relative to sea level
        point.extrude = 1 # draw line from plane to ground

        kml.save("lineofsight.kml") # save pin and heatmap to kml file

        sleep(SLEEP_TIME) # sleep to not spam CloudRF

    else:
        print("Plane dose not have position data, try another plane")
        break