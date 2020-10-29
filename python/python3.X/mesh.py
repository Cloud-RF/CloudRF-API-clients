import requests
import sys
import os
import time
server="https://cloudrf.com"
fileformat = "kmz" # kmz, shp, tiff, url, html

def mesh(uid,net):
	r = requests.get(server+"/API/mesh/mesh.php?uid="+str(uid)+"&network="+net)
	print(r.text)
	result = r.text.split("/")
	fname = result[len(result)-1].split(".")[0]
	return fname

def archiveDL(uid,key,fname,fileformat):
	dlargs={'uid': uid, 'key': key, 'file': fname, 'fmt': fileformat}
	r = requests.get(server+"/API/archive/data.php", params=dlargs)
	file = open("networks"+os.sep+fname+"."+fileformat,"wb")
	file.write(r.content)
	file.close()
	print("Wrote %d bytes to %s.%s" % (len(r.text),fname,fileformat))

if len(sys.argv) < 3:
	print("ERROR: Need a UID, API key and network\neg. python mesh.py 1 8d7f8df78d7f8d7f8d7f87df MY_NET")
	quit()

uid = sys.argv[1]
key = sys.argv[2]
net = sys.argv[3]

if not os.path.exists("networks"):
		os.makedirs("networks")

fname = mesh(uid,net)
archiveDL(uid,key,fname,fileformat)
