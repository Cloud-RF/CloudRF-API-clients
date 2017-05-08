import requests, csv, random, sys, os, time
server="https://cloudrf.com" 
delay = 1 
# Use the nonce to prevent yourself accidentally adding test calculations to a good network
nonce = "" #random.randint(1,99)
format = "kmz" # shp, tiff, url, html
# Send job to server. Refer to cloudrf.com/pages/api for API parameters.

def archiveDL(uid,key,fname,format):
	dlargs={'uid': uid, 'key': key, 'file': fname, 'fmt': format}
	r = requests.get(server+"/API/archive/data.php", params=dlargs)
	file = open("calculations"+os.sep+fname+"."+format,"w")
	file.write(r.content)
	file.close()
	print "Wrote %d bytes to %s.%s" % (len(r.text),fname,format)

def calculate(args):
	global uid
	net = args.get('net')+str(nonce) # Add nonce to avoid meshing unwanted legacy layers
	args['net']=net

	if args.get('uid') > 0:
		uid = args.get('uid')
	
	print "\nCalculating %s for network %s with %skm radius at %s pixels/degree..." % (args.get('nam'),net,args.get('rad'),args.get('res'))
	r = requests.post(server+"/API/api.php", data=args)
	result = r.text.split("/")
	fname = result[len(result)-1].split(".")[0]
	print r.text[:-1]
	archiveDL(args.get('uid'),args.get('key'),fname,format)


if len(sys.argv) == 1:
	print "ERROR: Need a .csv file\neg. python coverage.py mydata.csv"
	quit()
	
if not os.path.exists("calculations"):
		os.makedirs("calculations")

# Open CSV file
csvfile = csv.DictReader(open(sys.argv[1]))
n=0
for row in csvfile:
	# Pause script. Important otherwise server will refuse repeat requests
	time.sleep(delay)
	start_time = time.time() # Stopwatch start
	calculate(row)
	elapsed = round(time.time() - start_time,1) # Stopwatch stop
	print "Elapsed: "+str(elapsed)+"s"
	n=n+1
