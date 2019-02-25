import requests, csv, sys, os, time, json
server="https://cloudrf.com"

if len(sys.argv) == 1:
	print("ERROR: Need a .csv file\neg. python pathprofile.py pathprofile.csv")
	quit()

if not os.path.exists("calculations"):
		os.makedirs("calculations")

# Open CSV file
csvfile = csv.DictReader(open(sys.argv[1]))
n=0
for row in csvfile:

	start_time = time.time() # Stopwatch start
	#print(row)
	r = requests.post(server+"/API/path", data=row)
	print(r.text)

	try:
		j = json.loads(r.text)
		# Your ouptut is in this object eg. jj['received_dBm']
		if j['distanceKM']:
			print("Distance: "+str(j['distanceKM'])+"km Received power: "+str(j['received_dBm'])+"dBm")
		if j["report"]: # Is there a text report?
			r = requests.get(j['report'])
			fn="calculations"+os.sep+str(j['report'].split("/")[-1])
			filename = open(fn,"wb")
			filename.write(r.content)
			filename.close()
			print("Report saved to %s" % fn)
		if j["chart"]: # A PNG chart?
			r = requests.get(j['chart'])
			fn="calculations"+os.sep+str(j['chart'].split("/")[-1])
			filename = open(fn,"wb")
			filename.write(r.content)
			filename.close()
			print("PNG saved to %s" % fn)		
	except Exception as err:
		if "<html>" in r.text[0:6]: # SLEIPNIR HTML output. To turn into a PNG, open in a browser and click the camera button
			html=r.text
			fn="calculations"+os.sep+"PPA"+str(n)+".html"
			filename = open(fn,"w")
			filename.write(html)
			filename.close()
			print("HTML report saved to %s" % fn)			
		#print(str(err))
		continue
	# Pause script. Important otherwise server will ban you.
	time.sleep(3)

	elapsed = round(time.time() - start_time,1) # Stopwatch
	print("Elapsed: "+str(elapsed)+"s")
	n=n+1
