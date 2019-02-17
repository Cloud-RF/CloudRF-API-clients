#!/usr/bin/python
import csv
import os
import requests
import sys
import time
# CloudRF API client script Copyright 2016 Farrant Consulting Ltd
#
# Reads in radio transmitter data from a CSV files and creates a propagation KMZ for each row
# Once complete, it will download the KMZ files
# The CSV file MUST be formatted according to the example!
# Before using you must create a CloudRF account and enter your API credentials in the data fields 'uid' and 'key'
# For help email: support@cloudrf.com

server="https://cloudrf.com" # Public server

# Send job to server. Refer to cloudrf.com/pages/api for API parameters.
def bestserver(args):
	global server
	print "Finding best server(s) for %s, %s %sfm, %sdBi" % (args.get('lat'),args.get('lon'),args.get('rxh'),args.get('rxg'))
	req = requests.post(server+"/API/network/index.php", args)
	result = req.text
	print result


def downloadPPA(file,nam):
	f = requests.get(file)
	localFile=os.path.join("ppa",nam)
	data = f.content
	with open(localFile, "wb") as local_file:
		local_file.write(data)

if len(sys.argv) == 1:
	print "ERROR: Need a .csv file\neg. python bestserver.py customers.csv"
	quit()

# Open CSV file
csvfile = csv.DictReader(open(sys.argv[1]))
n=1
for row in csvfile:
	bestserver(row)
	n=n+1
