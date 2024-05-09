import simplekml
import json
import random
import time
import requests
import time
requests.packages.urllib3.disable_warnings() 

# Model n radios, using a pool of API keys for parallel processing
# Style links using traffic light thresholds: green = good, orange = marginal, red = bad
# Write a KML to disk where viewers can load it dynamically
# Send a multisite (GPU) request to create a KMZ which is also saved locally for viewers

# VARIABLES
radios=4
step=200 # m
interval=2 # s
ratelimit=0
degree_step = step / 120e3
api_server = "https://192.168.20.56"
api_keys=[""] # put API keys here, comma separated
start_location={"id": -1, "lat": 32.75, "lon": -97.3313, "alt": 2} # Fort Worth, TX
multisite=1
heightAMSL=200
# VARIABLES ENDS


print("%d radios starting at %.3f,%.3f heading north at %.1f m/s (degree step %.5f)" % (radios,start_location["lat"],start_location["lon"],step/interval,degree_step))

while True:
    kml = simplekml.Kml()
    radio_locs=[]
    d=0
    random.seed()
    while d < radios:
        lat = start_location["lat"] + random.uniform(degree_step*-1,degree_step)
        lon = start_location["lon"] + random.uniform(degree_step*-2,degree_step*2)
        height = random.uniform(1,10)
        drone = {"id": d, "lat": round(lat,5), "lon": round(lon,5), "alt": round(height)}
        radio_locs.append(drone)
        point = kml.newpoint(name=d, extrude=1, coords=[(round(lon,5),round(lat,5), height+heightAMSL)])  
        point.altitudemode = simplekml.AltitudeMode.absolute
        point.style.iconstyle.icon.href = 'http://maps.google.com/mapfiles/kml/shapes/earthquake.png'
        d+=1

    d=0
    fails=0
    start = time.time()
    goodlinks=0
    while d < len(radio_locs):
        p = d % len(api_keys)
        key = api_keys[p]
        # iterate over positions and select all except current
        transmitters = []
        for p in radio_locs:
            if p["id"] != d:
                tx = {
                "lat": 0,
                "lon": 0,
                "alt": 1
                }
                tx["lat"] = p["lat"]
                tx["lon"] = p["lon"]
                tx["alt"] = p["alt"]
                transmitters.append(tx)

                #linestring = kml.newlinestring(name="tx "+str(p["id"]))
                #linestring.coords = [(p["lon"],p["lat"],p["alt"]), (radio_locs[d]["lon"],radio_locs[d]["lat"],radio_locs[d]["alt"])]
                #linestring.altitudemode = simplekml.AltitudeMode.relativetoground

        request = {
            "site": "Links",
            "network": "#random",
            "transmitter": {
                "lat": radio_locs[d]["lat"],
                "lon": radio_locs[d]["lon"],
                "alt": radio_locs[d]["alt"],
                "frq": 2250,
                "txw": 1,
                "bwi": 0.1
            },
            "points": transmitters,
            "receiver": {
                "lat": radio_locs[d]["lat"],
                "lon": radio_locs[d]["lon"],
                "alt": radio_locs[d]["alt"],
                "rxg": 1,
                "rxs": -110
            },
            "model": {
                "pm": 7,
                "pe": 2,
                "ked": 0,
                "rel": 99
            },
            "environment": {
                "clt": "Minimal.clt",
                "elevation": 1,
                "landcover": 0,
                "buildings": 0,
                "obstacles": 0
            },
            "output": {
                "units": "m",
                "col": "TRAFFIC.dBm",
                "out": 2,
                "nf": -100,
                "res": 3,
                "rad": 1
            }
        }
        multisiteRequest = request
        #print(request)
        print("Testing radio %d against %d others with API key %s" % (d,len(transmitters),key[:1]), end="")
        time.sleep(ratelimit)
        resp = requests.post(api_server+"/points", json = request, headers={'key': key}, verify=False)
        if "elapsed" in resp.json():
            print(" = %dms" % resp.json()["elapsed"])
            links = resp.json()["Transmitters"]
        else:
            print(request)
            print(resp.json())
            fails+=1

        for tx in links:
            if "Latitude" in tx:
                #print(tx["Signal power at receiver dBm"])
                if tx["Signal power at receiver dBm"] > -90:
                    if "Ground elevation m" in tx:
                        linestring = kml.newlinestring(name=str(tx["Signal power at receiver dBm"]))
                        linestring.coords = [(tx["Longitude"],tx["Latitude"],tx["Ground elevation m"]+tx["Antenna height m"]), (radio_locs[d]["lon"],radio_locs[d]["lat"],radio_locs[d]["alt"]+tx["Ground elevation m"])]
                        linestring.altitudemode = simplekml.AltitudeMode.absolute
                        linestring.style.linestyle.color = 'ff0000ff'  # Red
                        if tx["Signal power at receiver dBm"] > -80:
                            linestring.style.linestyle.color = 'ff00c3fc'  # Orange
                        if tx["Signal power at receiver dBm"] > -70:
                            linestring.style.linestyle.color = 'ff00fc17'  # Green
                            goodlinks+=1


        d+=1


    # metrics
    end = time.time()
    possLinks=radios*(radios-1)
    print("Tested %d random radios / %d links in %.1fs with %d good links (%.1f%%) and %d failures" % (radios,possLinks, end-start, goodlinks,(goodlinks/possLinks)*1e2,fails))
 
    
     # Coverage via Multisite API?
    if multisite:
        multisiteRequest.pop("transmitter")
        multisiteRequest.pop("points")
        multisiteTransmitters = transmitters

        t = 0
        while t < len(multisiteTransmitters):
            multisiteTransmitters[t]["frq"] = 2250
            multisiteTransmitters[t]["txw"] = 10
            multisiteTransmitters[t]["bwi"] = 0.1
            multisiteTransmitters[t]["antenna"] = {"txg": 2.15, "ant": 1, "pol": "v", "tlt": 0, "txl": 0, "azi": 0}
            t+=1

        start = time.time()
        multisiteRequest["transmitters"] = multisiteTransmitters
        resp = requests.post(api_server+"/multisite", json = multisiteRequest, headers={'key': key}, verify=False)
        if "elapsed" in resp.json():
            netlink = kml.newnetworklink(name="Coverage")
            netlink.link.href = resp.json()["kmz"]
            netlink.link.viewrefreshmode = simplekml.ViewRefreshMode.onrequest

    end = time.time()
    print("Computed multisite coverage in %.1fs" % (end-start))
    time.sleep(interval)
    kml.save("radios.kml")
    radios+=4
    step+=200
    degree_step = step / 120e3
