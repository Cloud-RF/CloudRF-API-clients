#!/usr/bin/python
import csv, os, requests, sys, time
# CloudRF API client script Copyright 2016 Farrant Consulting Ltd
#
# Reads in radio transmitter data from a CSV files and creates a propagation KMZ for each row
# Once complete, it will download the KMZ files
# The CSV file MUST be formatted according to the example!
# Before using you must create a CloudRF account and enter your API credentials in the data fields 'uid' and 'key'
# For help email: support@cloudrf.com

server="https://cloudrf.com" # Public server 

# Send job to server. Refer to cloudrf.com/pages/api for API parameters.
def calculate(args,nam):
	global uid
	global server
	if args.get('uid') > 0:
		uid = args.get('uid')
	print "Calculating path from %s,%s to %s,%s..." % (args.get('tla'),args.get('tlo'),args.get('rla'),args.get('rlo'))
	req = requests.post(server+"/API/ppa/ppa.php", args)
	result = req.text
	if result[0] != "/":
		print result
	else:
		downloadPPA(server+result+".txt",nam+".txt") # TEXT REPORT
		downloadPPA(server+result+".png",nam+".png") # PNG IMAGE
		print "Downloaded as ppa/"+nam


def downloadPPA(file,nam):
	f = requests.get(file)
	localFile=os.path.join("ppa",nam)
	data = f.content
	with open(localFile, "wb") as local_file:
		local_file.write(data)

if len(sys.argv) == 1:
	print "ERROR: Need a .csv file\neg. python calculate.py mydata.csv"
	quit()
	
if not os.path.exists("ppa"):
		os.makedirs("ppa")
		
# Open CSV file
csvfile = csv.DictReader(open(sys.argv[1]))
n=1
for row in csvfile:
	time.sleep(1)
	calculate(row,str(n))
	n=n+1
	
