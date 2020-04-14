#!/usr/bin/python3
from pykml import parser
import os
import sys
import requests
import time
import json
import simplekml
# CloudRF.com Best Server path demo
# Parses a KML path and feeds it into the CloudRF 'best server' API
# Creates a new KML with the outputs, styled based on RSSI


# CHANGE THESE TO MATCH YOUR ACCOUNT/SYSTEM

uid = 21531 # CloudRF account UID 
key = 'b353f1ceae63fd07931722b5f39e7bd87a1b138d' #9352413cad59aad4d1ecd851f54e2c13476cce87' # CloudRF account Key
network = 'pathdemo'
rxHeight = 2 # Height, Metres
rxGain = 3 # Gain, dBi

redZone = -100 # Bad/No signal
blueZone = -90 # Weak signal
greenZone = -80 # Good signal

server="https://cloudrf.com" # Public API

# EDIT BELOW HERE AT YOUR OWN RISK

#################################################################################################################

kml = simplekml.Kml(open=1)

# Send job to server. Refer to cloudrf.com/pages/api for API parameters.
def bestserver(args):
	print("Finding the best server(s) at %s,%s,%sm with %sdBi antenna..." % (args.get('lat'),args.get('lon'),args.get('rxh'),args.get('rxg')))
	req = requests.post(server+"/API/network/", data=args)
	towers = json.loads(req.text)
	rssi = -140
	shortResult="Network: "+args.get('net')+"<table border='1'><th>Tower<th>RSSI dBm<th>Distance Km"
	if len(towers) > 0:
		for tower in towers:
			print(tower["Server name"],tower["Transmitters"][0]["Signal power at receiver dBm"])
			if tower["Transmitters"][0]["Signal power at receiver dBm"] > rssi:
				rssi = tower["Transmitters"][0]["Signal power at receiver dBm"]
			shortResult+="<tr><td>"+tower["Server name"]+"<td>"+str(tower["Transmitters"][0]["Signal power at receiver dBm"])+"<td>"+str(tower["Transmitters"][0]["Distance to receiver km"])
		shortResult+="</table>Powered by <a href='https://cloudrf.com'>CloudRF.com</a>"

		# Make a KML linestring
		line = kml.newlinestring(name=str(round(rssi))+"dBm",description=shortResult)
		line.coords = [(args.get('prevlon'),args.get('prevlat')),(args.get('lon'),args.get('lat'))]
		line.style.linestyle.width = 100


		# Colour coding by RSSI
		col = simplekml.Color.red
		if rssi > blueZone:
			col = simplekml.Color.blue
		if rssi > greenZone:
			col = simplekml.Color.green
		line.style.linestyle.color = col

		pnt = kml.newpoint(name=str(round(rssi))+"dBm",description=shortResult)
		pnt.coords = [(args.get('lon'),args.get('lat'))]
		pnt.style.labelstyle.color = col

if len(sys.argv) < 2:
	print("Needs a KML file as an argument: eg. RouteCoverage.py myroute.kml")
	quit()

with open(sys.argv[1]) as xml:
	doc = parser.parse(xml).getroot()
	coords = doc.Document.Placemark.LineString.coordinates.text.split(" ")
	if len(coords) < 2:
		print("Not enough points in this path. Needs at least 2")
		quit()
	prevlat = 0
	prevlon = 0
	for point in coords:
		pt = point.strip("\n\t ").split(",")
		args = {}
		if len(pt) > 1:
			args["lat"] = pt[1]
			args["lon"] = pt[0]
			if prevlat and prevlon:
				args["prevlat"] = prevlat
				args["prevlon"] = prevlon
			else:
				args["prevlat"] = float(pt[1])-0.001
				args["prevlon"] = pt[0]
			args["rxh"] = rxHeight
			args["rxg"] = rxGain
			args["uid"] = uid
			args["key"] = key
			args["net"] = network
			bestserver(args)
			prevlat=pt[1]
			prevlon=pt[0]
	kml.save("RouteCoverageResult.kml")
