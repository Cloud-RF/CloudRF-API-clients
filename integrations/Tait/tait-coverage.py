import serial
from datetime import datetime, timedelta
import math
import simplekml
import time
import json
import requests
import os
from dotenv import load_dotenv
import socket

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
local_radio = "102" # Local radio ID eg. 103

# UDP broadcast for CoT messages for ATAK
server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

radios = {
"101":{"callsign": "One","lat":0,"lon":0,"alt":0,"template":"TP9300.json"},
"102":{"callsign": "Two","lat":0,"lon":0,"alt":0,"template":"TP9300.json"},
"103":{"callsign": "Three","lat":0,"lon":0,"alt":0,"template":"TP9300.json"},
"104":{"callsign": "Four","lat":0,"lon":0,"alt":0,"template":"TP9300.json"}}

api_endpoint = os.getenv("api_endpoint")
api_key = os.getenv("api_key")
interval = 5 # Recommended range 5 to 60. Don't go too low or you will piss people off (and it won't work)

# A 5s timeout has been added to handle offline radios
ser = serial.Serial('/dev/ttyUSB0', baudrate=19200, timeout=5)

# You can serve up the .kml on TCP 8000 with: python3 -m http.server
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

# https://github.com/Cloud-RF/cotroutesim/blob/main/simulate.py
# bot = {"uid": name,"cs": name, "lat": lat, "lon": lon}
def cot_bot(bot):
    ts=datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
    tots=(datetime.now()+timedelta(minutes=5)).strftime('%Y-%m-%dT%H:%M:%SZ')
    msg='<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\
    <event version="2.0" uid="'+bot["uid"]+'" type="a-f-G-U-C" time="'+ts+'" start="'+ts+'" stale="'+tots+'" how="h-e">\
    <point lat="'+str(bot["lat"])+'" lon="'+str(bot["lon"])+'" hae="2" ce="9999999" le="9999999"/>\
    <detail><takv os="0" version="1.1" device="" platform="Tait plugin"/>\
    <contact callsign="'+bot["cs"]+'" endpoint="*:-1:stcp"/><uid Droid="'+bot["uid"]+'"/>\
    <precisionlocation altsrc="" geopointsrc="USER"/><__group role="Radio demo" name="Orange"/>\
    <status battery="100"/><track course="0.0" speed="0.0"/></detail></event>'

    server.sendto(msg.encode("utf-8"), ('<broadcast>', 4242))
    return msg.encode("utf-8")

while True:
    kml = simplekml.Kml()
    kml.newpoint(name=radios[local_radio]["callsign"], coords=[(radios[local_radio]["lon"],radios[local_radio]["lat"])],description=datetime.now().isoformat())

    for radio in radios:
        if radio != local_radio:
            msg = "a1B05206%08dGPGGA,%08d" % (int(radio),int(local_radio)) # NMEA request 
            print("Requesting location for radio %s..." % radio)
            send(msg)
            count=0
            while count < 5: # try 5 times only 
                data = ser.read_until(b'\r').decode("utf-8") # times out after 5s
                #print("%s" % data)

                # Listen for loc reports
                if "r0A54" in data:
                    rxd_radio = data.split("FF")[1][:-3] # trim checksum and CR
                    print("GPS report from %s (%ds)" % (rxd_radio,count))
                    if rxd_radio != radio:
                        print("Not our radio!: %s" % rxd_radio)

                if "$GPGGA" in data and rxd_radio == radio:
                    nmea = parseNMEA(str(radio),data)
                    if nmea[2]:
                        kml.newpoint(name=radios[radio]["callsign"], coords=[(nmea[2],nmea[1])],description=datetime.now().isoformat()+"\n"+"Radio ID: "+radio)
                        print("Updated KML with radio %s at %s,%s (%ds)" % (radio,nmea[1],nmea[2],count))

                        # Send CoT
                        bot = {"uid": "Tait"+str(radio),"cs": str(radios[radio]["callsign"]), "lat": nmea[1], "lon": nmea[2]}
                        try:
                            cot_bot(bot)
                        except:
                            print("Error sending CoT")

                    time.sleep(1) # breathe in between Tx requests
                    break
                else:
                    count+=1
    try:
        netlink = kml.newnetworklink(name="DMR Coverage")
        netlink.link.refreshmode = simplekml.RefreshMode.oninterval
        netlink.link.refreshinterval = interval
        netlink.link.href = multisiteRequest()
    except:
        pass

    kml.save("tait-dmr.kml")
    time.sleep(interval)

ser.close()
