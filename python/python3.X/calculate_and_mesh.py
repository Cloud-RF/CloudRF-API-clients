import requests
import csv
import sys
import os
import time
import json

from datetime import datetime

server="https://192.168.1.107"
strictSSL=False

def mesh(uid,net):
	r = requests.get(server+"/API/mesh/?uid="+str(uid)+"&network="+net, verify=strictSSL)
	j = json.loads(r.text)
	return j['filename']

def archiveDL(uid,key,fname,fileformat):
	dlargs={'uid': uid, 'key': key, 'file': fname, 'fmt': fileformat}
	url=server+"/API/archive/data.php"
	r = requests.get(url, params=dlargs, verify=strictSSL)
	if fileformat == 'shp':
		fileformat='shp.zip'
	filename = open("calculations"+os.sep+fname+"."+fileformat,"wb")
	filename.write(r.content)
	filename.close()
	print("Wrote %d bytes to %s.%s" % (len(r.text),fname,fileformat))

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
	time.sleep(2)
	start_time = time.time() # Stopwatch start
	row['net']+="_"+nonce
	# Extract UID and KEY for meshing after rows have processed
	uid=row['uid'] # Unique UID from cloudrf.com eg. 1234
	key=row['key'] # Secret API key from cloudrf.com
	net=row['net'] # Descriptive grouping. Used for meshing and *deleting* so set this carefully
	fileformat=row['file'] # kmz,shp,tiff,url,html

	r = requests.post(server+"/API/area", data=row, verify=strictSSL)
	print(r.text)
	j = json.loads(r.text)

	# Fetch the offered file from our archive...
	if 'kmz' in j:
		r = requests.get(j['kmz'], verify=strictSSL)
		fn="calculations"+os.sep+str(row['nam'])+".kmz"
		filename = open(fn,"wb")
		filename.write(r.content)
		filename.close()
		print("Saved to %s" % fn)
	if 'shp' in j:
		r = requests.get(j['shp'], verify=strictSSL)
		fn="calculations"+os.sep+str(row['nam'])+".shp.zip"
		filename = open(fn,"wb")
		filename.write(r.content)
		filename.close()
		print("Saved to %s" % fn)


	elapsed = round(time.time() - start_time,1) # Stopwatch
	print("Elapsed: "+str(elapsed)+"s")
	n=n+1

fname = mesh(uid,net) # Merge layers using our network name
time.sleep(1) # Recommended for SHP operations as they can be slow
archiveDL(uid,key,fname,fileformat) # Fetch meshed layer
