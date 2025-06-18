import serial
from datetime import datetime
import math
import simplekml
import time
import json
import requests
import os
from dotenv import load_dotenv

# Tait DMR coverage script
#
# Sends location requests using CCDI packets to connected portables to model their coverage with CloudRF
# Requires either a Silver CloudRF account or a SOOTHSAYER server to make the coverage or you can 
# comment multisiteRequest() out to just put pins on a KML

# DWYW License
# This program is free software. It comes without warranty, to the
# extent permitted by applicable law. You may redistribute and/or
# modify it under the terms of the Do Whatever You Want (DWYW) license.
# See https://jmthornton.net/dwyw for more details.

load_dotenv()
local_radio = "104" # Local radio ID eg. 103
radios = {
"101":{"callsign": "1","lat":0,"lon":0,"alt":0,"template":"TP9300.json"},
"102":{"callsign": "2","lat":0,"lon":0,"alt":0,"template":"TP9300.json"},
"104":{"callsign": "4","lat":51.8662,"lon":-2.2045,"alt":10,"template":"TP9300.json"}}
api_endpoint = os.getenv("api_endpoint")
api_key = os.getenv("api_key")
interval = 10 # Recommended range 10 to 60. Don't go too low or you will piss people off (and it won't work)
ser = serial.Serial('/dev/ttyUSB0', baudrate=19200)
web_service = "http://10.0.0.10:8000/"


def download(url,file_name):
    get_response = requests.get(url,stream=True)
    with open(file_name, 'wb') as f:
        for chunk in get_response.iter_content(chunk_size=1024):
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)

def checksum_calc(s):
    sum = 0
    for c in s:
        sum += ord(c)
    sum = -(sum % 256)
    return '%2X' % (sum & 0xFF)        

def send(msg):
    cc = checksum_calc(msg)
    msg = msg+cc+"\r"
    ser.write(msg.encode("utf-8")) 

def parseNMEA(tela,nmea):
    section = nmea.split("$GPGGA")[1].split(",")
    lat = section[2]
    lat_direction = section[3]
    lon = section[4]
    lon_direction = section[5]
    alt = section[9]

    try:
        lat = round(math.floor(float(lat) / 100) + (float(lat) % 100) / 60, 6)
        if lat_direction == 'S':
            lat = lat * -1

        lon = round(math.floor(float(lon) / 100) + (float(lon) % 100) / 60, 6)
        if lon_direction == 'W':
            lon = lon * -1
        radios[tela]["lat"] = lat
        radios[tela]["lon"] = lon
        radios[tela]["alt"] = alt
        return(tela,lat,lon,alt)
    except:
        pass


def multisiteRequest():
    # For each radio which has geo data
    transmitters = []
    for r in radios:
        if radios[r]["lat"] != 0 and radios[r]["lon"] != 0:
            with open(radios[r]["template"]) as jd: # Radio settings are defined in the template. Examples on Github.
                contents = jd.read()
                d = json.loads(contents)
                jd.close()
                tx = d["transmitter"]
                tx["lat"] = radios[r]["lat"]
                tx["lon"] = radios[r]["lon"]
                tx["antenna"] = d["antenna"]
                transmitters.append(tx)
    d["transmitter"] = ""
    d["antenna"] = ""
    d["transmitters"] = transmitters
    headers = {'Content-type': 'application/json', 'Accept': 'text/plain', 'Key': api_key}
    print(d)
    r = requests.post(api_endpoint+"/multisite", data=json.dumps(d), headers=headers)
    response = json.loads(r.text)
    print(response["kmz"],response["elapsed"])
    download(response["kmz"],"coverage.kmz")
    return(web_service+"coverage.kmz")


while True:
    kml = simplekml.Kml()
    kml.newpoint(name=radios[local_radio]["callsign"], coords=[(radios[local_radio]["lon"],radios[local_radio]["lat"])],description=datetime.now().isoformat())

    for radio in radios:
        if radio != local_radio:
            msg = "a1B05206%08dGPGGA,%08d" % (int(radio),int(local_radio)) # NMEA request 
            print("Requesting location for radio %s..." % radio)
            send(msg)
            count=0
            while count < interval:
                send("q011")  # get result
                data = ser.read_until(b'\r').decode("utf-8")
                print(data)
                # Listen for loc reports
                if "r0A54" in data:
                    radio = data.split("FF")[1][:-3] # trim checksum and CR
                    print("GPS report from %s" % radio)

                if "$GPGGA" in data:
                    nmea = parseNMEA(str(radio),data)
                    if nmea[2]:
                        kml.newpoint(name=radios[radio]["callsign"], coords=[(nmea[2],nmea[1])],description=datetime.now().isoformat()+"\n"+"Radio ID: "+radio)
                        print("Updated KML with radio %s at %s,%s" % (radio,nmea[1],nmea[2]))
                    break
                else:
                    time.sleep(1)
                    count+=1
    try:
        netlink = kml.newnetworklink(name="DMR Coverage")
        netlink.link.refreshmode = simplekml.RefreshMode.oninterval
        networklink.link.refreshinterval = interval
        netlink.link.href = multisiteRequest()
    except:
        pass
    kml.save("tait-dmr.kml")
    time.sleep(interval)

ser.close()