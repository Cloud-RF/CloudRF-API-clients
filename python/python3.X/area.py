import requests
import csv
import sys
import os
import time
import json

server="https://cloudrf.com"

if len(sys.argv) == 1:
	print("ERROR: Need a .csv file\neg. python coverage.py mydata.csv")
	quit()

if not os.path.exists("calculations"):
		os.makedirs("calculations")

# Open CSV file
csvfile = csv.DictReader(open(sys.argv[1]))
n=0
for row in csvfile:
	# Pause script. Important otherwise server will ban you.
	time.sleep(1)
	start_time = time.time() # Stopwatch start
	#print row
	r = requests.post(server+"/API/area", data=row)
	print(r.text)
	#try:
	j = json.loads(r.text)
	if 'kmz' in j:
		#print j['kmz']
		r = requests.get(j['kmz'])
		fn="calculations"+os.sep+str(row['nam'])+".kmz"
		filename = open(fn,"wb")
		filename.write(r.content)
		filename.close()
		print("Saved to %s" % fn)
	if 'shp' in j:
		#print j['kmz']
		r = requests.get(j['shp'])
		fn="calculations"+os.sep+str(row['nam'])+".shp.zip"
		filename = open(fn,"wb")
		filename.write(r.content)
		filename.close()
		print("Saved to %s" % fn)


	elapsed = round(time.time() - start_time,1) # Stopwatch
	print("Elapsed: "+str(elapsed)+"s")
	n=n+1
