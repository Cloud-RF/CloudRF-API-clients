import requests
import csv
import sys
import os
import time
import json

from datetime import datetime

server="https://cloudrf.com"

def mesh(uid,net):
	r = requests.get(server+"/API/mesh/?uid="+str(uid)+"&network="+net)
	print(r.text)
	result = r.text.split("/")
	fname = result[len(result)-1].split(".")[0]
	return fname

def archiveDL(uid,key,fname,format):
	dlargs={'uid': uid, 'key': key, 'file': fname, 'fmt': format}
	r = requests.get(server+"/API/archive/data.php", params=dlargs)
	filename = open("calculations"+os.sep+fname+"."+format,"wb")
	filename.write(r.content)
	filename.close()
	print("Wrote %d bytes to %s.%s" % (len(r.text),fname,format))

if len(sys.argv) == 1:
	print("ERROR: Need a .csv file\neg. python coverage.py mydata.csv")
	quit()

if not os.path.exists("calculations"):
		os.makedirs("calculations")

# Open CSV file
csvfile = csv.DictReader(open(sys.argv[1]))
n=0

# Ensure we only mesh these sites and not older ones with same network
nonce=datetime.now().strftime('%H%M')

for row in csvfile:
	# Pause. Important otherwise server might reject your requests. See https://cloudrf.com/plans for rate limits.
	time.sleep(1)
	start_time = time.time() # Stopwatch start
	row['net']+="_"+nonce
	# Extract UID and KEY for meshing after rows have processed
	uid=row['uid'] # 1234
	key=row['key'] # abcdefabcdefabcdef...
	net=row['net'] # DEMO_NETWORK
	format=row['file'] # kmz,shp,tiff,url,html

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

fname = mesh(uid,net)
archiveDL(uid,key,fname,format)
