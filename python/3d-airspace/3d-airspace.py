import copy
import requests
import urllib3
import numpy as np
import time
from osgeo import gdal, osr
import sys
from pathlib import Path
import json
import os

# SERVER SETTINGS
CLOUDRF_API = "https://api.cloudrf.com"
try:
    CLOUDRF_API_KEY = os.environ['CLOUDRF_API_KEY'] 
except:
    print("Environment variable CLOUDRF_API_KEY not defined. Set it with 'export CLOUDRF_API_KEY={your api key}'")
    quit()

REQUEST_VERIFY_SSL = True
SLEEP_INTERVAL = 0.3 # Required for public API

def get_geotiff_info(filename):
    ds = gdal.Open(filename)
    if ds is None:
        raise ValueError(f"Could not open {filename}")
    
    gt = ds.GetGeoTransform()
    proj = ds.GetProjection()
    srs = osr.SpatialReference(wkt=proj)
    
    if not srs.IsGeographic() or srs.GetAttrValue('GEOGCS') != 'WGS 84':
        print("Warning: Image may not be in WGS-84 projection")
    
    width = ds.RasterXSize
    height = ds.RasterYSize
    
    bands = ds.RasterCount
    if bands == 4:  # Assuming RGBA
        alpha = ds.GetRasterBand(4).ReadAsArray()
    elif bands == 2:  # Grayscale + Alpha
        alpha = ds.GetRasterBand(2).ReadAsArray()
    else:
        alpha = np.ones((height, width), dtype=np.uint8) * 255
    
    ds = None
    return gt, width, height, alpha

def pixel_to_geo(px, py, gt):
    lon = gt[0] + px * gt[1] + py * gt[2]
    lat = gt[3] + px * gt[4] + py * gt[5]
    return lon, lat

def find_edge_at_bearing(center_lon, center_lat, bearing, alpha, gt, width, height):
    # Convert bearing to standard math angle (counterclockwise from east)
    angle_rad = np.radians(90 - bearing)
    
    max_dist = max(width, height)
    min_dist = int(max_dist/20) # start from offset due to antenna nulls creating alpha pixels
    for dist in range(min_dist, max_dist):
        dx = dist * np.cos(angle_rad)
        dy = -dist * np.sin(angle_rad)  # Negative because y increases downward
        
        px_center = (center_lon - gt[0]) / gt[1]
        py_center = (center_lat - gt[3]) / gt[5]
        
        px = int(px_center + dx)
        py = int(py_center + dy)
        
        if px < 0 or px >= width or py < 0 or py >= height:
            px = max(0, min(width - 1, px))
            py = max(0, min(height - 1, py))
            return pixel_to_geo(px, py, gt)
        
        if alpha[py, px] < 128:  # Threshold for transparency
            px_prev = int(px_center + (dist - 1) * np.cos(angle_rad))
            py_prev = int(py_center - (dist - 1) * np.sin(angle_rad))
            px_prev = max(0, min(width - 1, px_prev))
            py_prev = max(0, min(height - 1, py_prev))
            return pixel_to_geo(px_prev, py_prev, gt)
    
    return pixel_to_geo(px, py, gt)

def get_image_center(gt, width, height, alpha):
    opaque = alpha >= 128
    
    if not np.any(opaque):
        px = width / 2
        py = height / 2
    else:
        y_coords, x_coords = np.where(opaque)
        px = np.mean(x_coords)
        py = np.mean(y_coords)
    
    return pixel_to_geo(px, py, gt)

def create_kml(polygons, request, output_file):
    # BGR not RGB because Google 
    colours = ["0e0ef8","0e6bf8","0ec7f7","0ef7cb","0ef76e","0df611","66f60d","c2f60d","f5cd0d","f5710d"]

    kml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
    <kml xmlns="http://www.opengis.net/kml/2.2">
    <Document>
        <name>3D RADAR coverage</name>
        <Style id="c0">
        <LineStyle>
            <color>ff0e0ef8</color>
            <width>5</width>
        </LineStyle>
        <PolyStyle>
            <color>000e0ef8</color>
        </PolyStyle>
        </Style>
        <Style id="c1">
        <LineStyle>
            <color>ff0e6bf8</color>
            <width>5</width>
        </LineStyle>
        <PolyStyle>
            <color>000e6bf8</color>
        </PolyStyle>        
        </Style>
        <Style id="c2">
        <LineStyle>
            <color>ff0ec7f7</color>
            <width>5</width>
        </LineStyle>
        <PolyStyle>
            <color>000ec7f7</color>
        </PolyStyle>        
        </Style>
         <Style id="c3">
        <LineStyle>
            <color>ff0ef7cb</color>
            <width>5</width>
        </LineStyle>
        <PolyStyle>
            <color>000ef7cb</color>
        </PolyStyle>        
        </Style>
        <Style id="c4">
        <LineStyle>
            <color>ff0ef76e</color>
            <width>5</width>
        </LineStyle>
        <PolyStyle>
            <color>000ef76e</color>
        </PolyStyle>        
        </Style>
        <Style id="c5">
        <LineStyle>
            <color>ff0df611</color>
            <width>5</width>
        </LineStyle>
        <PolyStyle>
            <color>000df611</color>
        </PolyStyle>        
        </Style>
        <Style id="c6">
        <LineStyle>
            <color>ff66f60d</color>
            <width>5</width>
        </LineStyle>
        <PolyStyle>
            <color>0066f60d</color>
        </PolyStyle>        
        </Style>        
        <Style id="c7">
        <LineStyle>
            <color>ffc2f60d</color>
            <width>5</width>
        </LineStyle>
        <PolyStyle>
            <color>00c2f60d</color>
        </PolyStyle>        
        </Style>   
        <Style id="c8">
        <LineStyle>
            <color>fff5cd0d</color>
            <width>5</width>
        </LineStyle>
        <PolyStyle>
            <color>00f5cd0d</color>
        </PolyStyle>        
        </Style>   
        <Style id="c9">
        <LineStyle>
            <color>fff5710d</color>
            <width>5</width>
        </LineStyle>
        <PolyStyle>
            <color>00f5710d</color>
        </PolyStyle>        
        </Style>   
        <Style id="radaricon">
		<IconStyle>
			<scale>1.5</scale>
			<Icon>
				<href>http://maps.google.com/mapfiles/kml/shapes/target.png</href>
			</Icon>
		</IconStyle>
	    </Style>                                                               
    """

    kml_content += """
    	<Placemark>
		<name>RADAR</name>
		<description><![CDATA[<br><textarea rows='20'>"""+json.dumps(request, indent=2)+"""</textarea><br>3D RADAR by <a href='https://cloudrf.com'>CloudRF</a>]]></description>
		<styleUrl>#radaricon</styleUrl>
		<Point>
			<coordinates>"""+str(request["transmitter"]["lon"])+","+str(request["transmitter"]["lat"])+","+str(request["transmitter"]["alt"])+"""</coordinates>
		</Point>
	</Placemark>
    """

    index = 0
    for polygon in polygons:
        kml_content += f"""
        <Placemark>
        <name>"""+str(polygon[0][2])+"""</name>
        <styleUrl>#c"""+str(index)+"""</styleUrl>
        <Polygon>
            <extrude>0</extrude>
            <altitudeMode>relativeToSeaFloor</altitudeMode>
            <outerBoundaryIs>
            <LinearRing>
                <coordinates>
        """
        # Colours back to 0
        if index > 9:
            index = 0
        else:
            index += 1

        for lon, lat, alt in polygon:
            kml_content += f"              {lon},{lat},{alt}\n"

        kml_content += f"              {polygon[0][0]},{polygon[0][1]},{polygon[0][2]}\n"
        
        kml_content += """            </coordinates>
            </LinearRing>
            </outerBoundaryIs>
        </Polygon>
        </Placemark>"""

    kml_content += f""" </Document>
    </kml>"""
    
    with open(output_file, 'w') as f:
        f.write(kml_content)
    
    print(f"KML created: {output_file}")

def analyze_geotiff(input_file, altitude):
    gt, width, height, alpha = get_geotiff_info(input_file)
    center_lon, center_lat = get_image_center(gt, width, height, alpha)
    coordinates = []
    
    for bearing in range(0, 360, 1):
        lon, lat = find_edge_at_bearing(center_lon, center_lat, bearing, 
                                       alpha, gt, width, height)
        coordinates.append((round(lon,6), round(lat,6), altitude))
     
    return coordinates

if __name__ == "__main__":
    if not REQUEST_VERIFY_SSL:
        urllib3.disable_warnings()

    gdal.DontUseExceptions()
    kmlPoints = []

    if len(sys.argv) < 2:
        print("Usage: 3d-radar.py template.json")
        quit()

    try:
        with open(sys.argv[1]) as json_data:
            TEMPLATE = json.load(json_data)
    except:
        print("Failed to load JSON template: %s" % sys.argv[1])
        quit()

    MAX_HEIGHT = TEMPLATE["receiver"]["alt"] # Receiver altitude determines the analysis ceiling
    STEPS = 10 # Colours loop after 10

    STEP = MAX_HEIGHT / STEPS
    ALT = STEP
    HEIGHTS = []
    while ALT <= MAX_HEIGHT:
        HEIGHTS.append(ALT)
        ALT += STEP

    for height in HEIGHTS:
        request = copy.deepcopy(TEMPLATE)
        request["receiver"]["alt"] = height
        request["site"] += str(height)

        response = requests.post(
            f"{CLOUDRF_API}/area",
            json=request,
            headers={"key": CLOUDRF_API_KEY},
            verify=REQUEST_VERIFY_SSL,
        ).json()

        try:
            print(height,response["tiff_4326"],response["elapsed"])
        except:
            print(response)

        response = requests.get(response["tiff_4326"], stream=True)
        with open(request["site"]+".tif", mode="wb") as file:
            file.write(response.content)

        points = analyze_geotiff(request["site"]+".tif", height)
        kmlPoints.append(points)
        time.sleep(SLEEP_INTERVAL)

    create_kml(kmlPoints, request, "3dradar.kml")