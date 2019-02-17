import requests
import csv
import sys
import os
import time
import json

server="https://cloudrf.com"

if len(sys.argv) == 1:
	print "ERROR: Need a .csv file\neg. python pathprofile.py pathprofile.csv"
	quit()

if not os.path.exists("calculations"):
		os.makedirs("calculations")

# Open CSV file
csvfile = csv.DictReader(open(sys.argv[1]))
n=0
for row in csvfile:

	start_time = time.time() # Stopwatch start
	#print row
	r = requests.post(server+"/API/path", data=row)
	print r.text
	try:
		j = json.loads(r.text)
		# Your ouptut is in this object eg. jj['received_dBm']
		print "Distance: "+str(j['distanceKM'])+"km Received power: "+str(j['received_dBm'])+"dBm"
	except:
		pass
	# Pause script. Important otherwise server will ban you.
	time.sleep(3)

	elapsed = round(time.time() - start_time,1) # Stopwatch
	print "Elapsed: "+str(elapsed)+"s"
	n=n+1
