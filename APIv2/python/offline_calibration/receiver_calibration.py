import sys
import csv
import math
import numpy as np

# Receiver calibration script for CloudRF field testing
# Use readings from the same position and orientation as used during the survey, ideally at several kilometres with line of sight.
# CSV format: latitude,longitude,id where id is the measured rssi in dBm


if len(sys.argv) < 1:
	print("Calibrate a receiver with field measurements")
	print("Use: python3 receiver_calibration.py measurements.csv")
	quit()

with open(sys.argv[1]) as csvfile:
	reader = csv.DictReader(csvfile)
	
	rssi = "id" # CloudRF CSV import for customer locations: latitude,longitude,id 
	rssi_actual = []
	for row in reader:
		rssi_actual.append(float(row[rssi]))
	print(rssi_actual)
	print("Mean: %.1fdB" % np.mean(rssi_actual))
	print("Error: %.1fdB" % np.std(rssi_actual))
	
	if np.std(rssi_actual) > 4:
		print("Variation is > 4. These readings are bad! Measurements should be from the same location.")
