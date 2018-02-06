import requests, csv, sys, os, time, json
server="https://cloudrf.com" 

if len(sys.argv) == 1:
	print "ERROR: Need a .csv file\neg. python coverage.py mydata.csv"
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
	print r.text
	try:
		j = json.loads(r.text)
		# Your ouptut is in this object eg. j['PNG_WGS84'], j['area'], j['bounds']
		if j['kmz']:
			#print j['kmz']
			r = requests.get(j['kmz'])
			fn="kmz"+os.sep+str(j['id'])+".kmz"
			file = open(fn,"w")
			file.write(r.content)
			file.close()
			print "Saved to %s" % fn
	except:
		pass


	elapsed = round(time.time() - start_time,1) # Stopwatch
	print "Elapsed: "+str(elapsed)+"s"
	n=n+1
