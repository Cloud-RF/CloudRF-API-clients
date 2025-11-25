import requests
import json
import os
import math
import numpy as np
import zipfile
import urllib3
import argparse
import hashlib
from PIL import Image, ImageDraw
from io import BytesIO
 

# Copyright (c) 2025 Farrant Consulting Ltd T/A CloudRF

# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:

# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


def convert_to_delta_map(color_key,image,dbm):
    print (f"Converting Image to Delta Map with recieved power at {dbm}dBm")
    data = np.array(image)  
    mask = data[:, :, 3] > 0     

    # Iterate over raster and set/ignore pixels
    ys, xs = np.where(mask)
    for y, x in zip(ys, xs):
        r, g, b, a = data[y, x]
        pathloss = r
        power_watt = 2
        tx_power_dbm = 30 + 10 * math.log10(power_watt) # Convert Watts to dBm
        rx_power_dbm = tx_power_dbm - pathloss # Link budget
        diff = abs(rx_power_dbm  - dbm) # find the difference
        first_color_key_entry = None

        for color in color_key:
            if int(color["receivedPowerMargin"]) >= int(diff):
                first_color_key_entry = color
                break
         
        if first_color_key_entry != None:
            data[y, x, :4] = [first_color_key_entry["red"],
                    first_color_key_entry["green"],
                    first_color_key_entry["blue"],a]
        else:   
            data[y,x,3]=0
    
    new_image = Image.fromarray(data).convert("RGBA")  
    return new_image

def get_filename(d: dict) -> str:
  dict_str = json.dumps(d, sort_keys=True)
  dict_bytes = dict_str.encode('utf-8')
  hash = hashlib.md5(dict_bytes).hexdigest()
  file = f"{hash}.png" 
  return file

   
def load_config():
  with open('config.json', 'r') as f:
    config = f.read()

  try:  
    config_json = json.loads(config)
  except Exception as e:
    print("error with json config")
    exit(1)

  API_KEY = config_json["api_key"]
  API_SERVER = config_json["api_server"]
  COLOR_KEY = config_json["color_key"]
 
  tx_alt = config_json["alt"]
  tx_lat = config_json["lat"]
  tx_lon = config_json["lon"]
  tx_freq = config_json["freq"]
 
  with open('cf_calc_template.json', 'r') as f:
      payload = f.read()

  try:  
    PAYLOAD_JSON = json.loads(payload)
  except Exception as e:
    print("error with payload config")
    exit(1)    

  PAYLOAD_JSON["transmitter"]["lat"] =  tx_lat
  PAYLOAD_JSON["transmitter"]["lon"] =  tx_lon
  PAYLOAD_JSON["transmitter"]["alt"] =  tx_alt
  PAYLOAD_JSON["transmitter"]["frq"] =  tx_freq

  return API_SERVER,API_KEY,COLOR_KEY,PAYLOAD_JSON
 
def cf_download_png(url,file): 
  response = requests.get(url,verify=False)
  if response.status_code == 200:
      with open(file, "wb") as f:
          f.write(response.content)  
  else:
      print(f"Failed to download image. Status code: {response.status_code}")
      exit(1)


def check_existing_area(payload_json):
  directory = "cache"
  if not os.path.exists(directory):
      os.makedirs(directory)
  file = f"cache/{get_filename(payload_json)}"
  if os.path.isfile(file):
    print(f"Calculation cache hit for location: {payload_json["transmitter"]["lat"]}, {payload_json["transmitter"]["lon"]}")
    return True
  else:
    print("Calculation cache miss")
    return False


def cf_do_area_calc(server,key,payload_json):

  print(f"Making Area API request to {server} for a receiver at: {payload_json["transmitter"]["lat"]}, {payload_json["transmitter"]["lon"]}")
  url = f"https://{server}/area"
  headers = {
    'key': f"{key}",
    'Accept': 'application/json'
  }

  payload = json.dumps(payload_json)
  response = requests.request("POST", url, headers=headers, data=payload, verify=False)

  try:
    json_response = json.loads(response.text)
  except Exception as e:
    print(f"{e}")

  if "error" in json_response:
    print(f"Error: {json_response["error"]}")
    exit(1)

  if "PNG_Mercator" in json_response:
    png_mercator_url = json_response["PNG_Mercator"]

    with open(f"cache/{get_filename(payload_json)}.json", "w") as f:
      f.write(response.text)  
    file = f"cache/{get_filename(payload_json)}"
    cf_download_png(png_mercator_url,file)
  else:
     print("Missing PNG_Mercator in JSON" )
     
def load_calc(payload_json):
  print("Loading Area Calculation Result")
  file = f"cache/{get_filename(payload_json)}"
  image = Image.open(file).convert("RGBA")

  try:  
    with open(f"{file}.json", 'r') as f:
      config = f.read()
      calc_json = json.loads(config)
      bounds = calc_json["bounds"]
  except Exception as e:
    print(f"Unable to load result: {e}")
    exit(1)
  return image,bounds

def cutout_triangle(bearing,spread,image):
  print(f"Cutting Triangle with bearing {bearing}")
  mask = Image.new("L", image.size, 0)
  draw = ImageDraw.Draw(mask)

  # Tip of triangle at image center
  tip_x = image.width // 2
  tip_y = image.height // 2
  tip = (tip_x, tip_y)

  # Parameters
  length = 50000       # Distance from center to base corners
  bearing = (bearing  -1) % 360    # Compass bearing in degrees (0° = North, 90° = East)
  spread = spread           # Horizontal error in degrees eg. 10 deg RMSE

  def compass_to_math(deg):
      return math.radians(90 - deg)

  angle_left = compass_to_math(bearing - spread)
  angle_right = compass_to_math(bearing + spread)

  left = (
      tip_x + length * math.cos(angle_left),
      tip_y - length * math.sin(angle_left)
  )
  right = (
      tip_x + length * math.cos(angle_right),
      tip_y - length * math.sin(angle_right)
  )

  draw.polygon([tip, left, right], fill=255)

  result = Image.new("RGBA", image.size)
  result.paste(image, (0, 0), mask)

  return result



if __name__ == "__main__":
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--lob", type=float,required=True, help="Line of bearing")
    parser.add_argument("--dbm", type=float,required=True, help="Recieved Power (dBm)")
    parser.add_argument("--kmz", type=str,required=True, help="Filename to call the KMZ")
    
    args = parser.parse_args()
    lob = args.lob
    dbm = args.dbm
    kmz = args.kmz

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    API_SERVER,API_KEY,COLOR_KEY,PAYLOAD_JSON = load_config()
    if check_existing_area(PAYLOAD_JSON) == False:
        cf_do_area_calc(API_SERVER,API_KEY,PAYLOAD_JSON)

    calc_image,(north,east,south,west)  =load_calc(PAYLOAD_JSON)
    cutout_triangle_image=cutout_triangle(lob,5,calc_image)
    img_result=convert_to_delta_map(COLOR_KEY,cutout_triangle_image,dbm)

    print(f"Generating KMZ: {kmz}")
    

    KML= f"""
<?xml version="1.0" encoding="UTF-8"?>
  <kml xmlns="http://www.opengis.net/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2" xmlns:kml="http://www.opengis.net/kml/2.2" xmlns:atom="http://www.w3.org/2005/Atom">
  <Document>
    <LookAt>
      <longitude>{PAYLOAD_JSON["transmitter"]["lon"]}</longitude>
      <latitude>{PAYLOAD_JSON["transmitter"]["lat"]}</latitude>
      <altitude>0</altitude>
      <heading>0</heading>
      <tilt>0</tilt>
      <range>5000</range> <!-- smaller = zoomed in -->
      <altitudeMode>relativeToGround</altitudeMode>
    </LookAt>
    <name>Enhanced DF</name>

    <Folder>
      <name>GroundOverlays</name>
      <GroundOverlay>
        <name>{PAYLOAD_JSON["transmitter"]["lon"]},{PAYLOAD_JSON["transmitter"]["lat"]},{lob},{dbm}</name>
        <Icon>
          <href>image.png</href>
        </Icon>
        
        <LatLonBox>
            <north>{north}</north>
            <south>{south}</south>
            <east>{east}</east>
            <west>{west}</west>
            <rotation>0.0</rotation>
        </LatLonBox>
      </GroundOverlay>  
    </Folder>
    <Folder>
      <name>Markers</name>
      <Placemark>
      <name></name> <!-- leave empty if you don't want text -->
      <Style>
        <IconStyle>
          <scale>1</scale> <!-- adjust size -->
          <Icon>
            <!-- A small dot icon -->
            <href>http://maps.google.com/mapfiles/kml/paddle/red-circle.png</href>
          </Icon>
        </IconStyle>
        <LabelStyle>
          <scale>0</scale> <!-- hide label text -->
        </LabelStyle>
      </Style>
      <Point>
        <coordinates>{PAYLOAD_JSON["transmitter"]["lon"]},{PAYLOAD_JSON["transmitter"]["lat"]}</coordinates>
      </Point>
    </Placemark>


    </Folder>
  </Document>
</kml>
""".strip()

    zip_buffer = BytesIO()
    img_buffer = BytesIO()
    img_result.save(img_buffer, format="PNG")
    img_bytes = img_buffer.getvalue()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
      zip_file.writestr("doc.kml", KML)
      zip_file.writestr(f"image.png", img_bytes)
    with open(f"{kmz}", "wb") as f:
        f.write(zip_buffer.getvalue())

    print(f"Done. You can now open {kmz} in a KMZ viewer")