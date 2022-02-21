import rasterio
import sys
import csv
import math
import numpy as np

# Offline calibration script for CloudRF field testing
# Create a GeoTIFF in CloudRF and field measurements in CSV to use this.
# CSV format: latitude,longitude,id where id is the measured rssi in dBm

receiverError = 3.1 # Typically 0.5 to 3.0dB. See receiver_calibration.py.

def coordPicker(lat,lon,src):
	bounds = src.bounds
	widthDeg = bounds.right-bounds.left
	heightDeg = bounds.top-bounds.bottom
	xOffset = round(((lon-bounds.left) / widthDeg) * src.width) # %
	yOffset = round(((bounds.top-lat) / heightDeg) * src.height)
	a = src.read(1)
	val = a[yOffset][xOffset]
	if val != 255:
		return val * -1
	return 0	

if len(sys.argv) < 2:
	print("Compare a CloudRF GeoTIFF with field measurements")
	print("Use: python3 Offline_Calibration.py measurements.csv coverage.tiff")
	quit()

with open(sys.argv[1]) as csvfile:
	reader = csv.DictReader(csvfile)
	src = rasterio.open(sys.argv[2])
	
	rssi = "id" # CloudRF CSV import for customer locations: latitude,longitude,id 
	errorCount = 0
	totalError = 0
	minError = 0
	maxError = 0
	rssi_predicted = []
	rssi_actual = []
	for row in reader:
		dBm = coordPicker(float(row["latitude"]),float(row["longitude"]),src)
		if dBm < 0:
			if dBm < -150:
				print("This looks like a colour schema! This script requires Greyscale GIS")
				quit()
			rssi_predicted.append(dBm)
			rssi_actual.append(float(row[rssi]))

			error = float(row[rssi])-dBm
			errorCount += 1
			totalError += error
			meanError = totalError / errorCount
			print("Lat: %.6f Lon %.6f Measured: %.1fdBm Modelled: %.1fdBm Error: %.1fdB Mean error: %.1fdB" % 
			(float(row["latitude"]),float(row["longitude"]),float(row[rssi]),dBm,error,meanError))
			
			# Find extreme errors
			if error < minError:
				minError = error
			if error > maxError:
				maxError = error
	
	# Print report						

	MSE = np.square(np.subtract(rssi_actual,rssi_predicted)).mean()
	RMSE = math.sqrt(MSE)

	print("\nModel error is mean %.1fdB, pure RMSE %.1fdB based upon %d measurements" % (meanError,RMSE,errorCount))
	print("Receiver measurement error: %.1fdB" % receiverError)
	
	# Adjust RMSE based on receiver accuracy
	RMSE -= receiverError
	print("RMSE adjusted for receiver error: %.1fdB" % RMSE)

	msg = "are very inaccurate. Check your inputs"

	if RMSE > 0:
		msg = "are excellent"
	if RMSE > 3:
		msg = "are very good"
	if RMSE > 6:
		msg = "are good"				
	if RMSE > 9:
		msg = "are ok"

	print("The modelling inputs %s." % msg) 
