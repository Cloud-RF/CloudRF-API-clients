import csv
import json
import sys


# Example CSV with header
#
# name,longitude,latitude,id,group
# 1,10.7612,46.0565,a,neta
# 2,10.7612,46.057,b,neta
# 3,10.7612,46.058,c,netb
# 4,10.7612,46.059,d,netb

#
#with open(sys.argv[1], newline='') as csvfile:
#    cr = csv.DictReader(csvfile, delimiter=',')
#    for row in cr:
#      print(row)
#      template = {"a": 1, "b": 2, "c": {"c1": 1, "c2": 2}, "Antenna":{}}
#      print("Creating template %s" % row["name"]+".json")
#      template["Name"] = row["name"]
#      template["Antenna"]["Gain"] = 1
#      with open(row["name"]+".json", "w",  encoding='utf-8') as jsonfile:
#        json.dump(template, jsonfile,indent=2)

with open(sys.argv[1], newline='') as csvfile:
    cr = csv.DictReader(csvfile, delimiter=',')
    for row in cr:
      print(row)
      template = {"version": 1, "reference": 2, "template": {"name": 4, "service": 5, "created_at":6, "owner":7, "bom_value":8}, "site": 9, "network": 10, "engine": 11, "coordinates": 12, "transmitter":{"lat": 13, "lon": 14, "alt": 15, "frq": 16, "txw": 17, "bwi": 18, "powerUnit": 19 }, "receiver": {"lat": 20, "lon": 21, "alt": 22, "rxg": 23, "rxs": 24}, "feeder":{"flt": 25, "fll": 26, "fcc": 27}, "antenna":{"mode": 28, "txg": 29,"txl": 30, "ant": 31, "azi": 32, "tlt": 33, "hbw": 34, "vbw": 35, "fbr": 35, "pol": 36 }, "model":{"pm": 37, "pe": 38, "ked": 39, "rel": 40}, "environment":{"elevation":41, "landcover": 42, "buildings": 43, "obstacles": 44, "clt": 45}, "output":{"units": 46, "col": 47, "out": 48, "ber": 49, "mod": 50, "nf": 51, "res": 52, "rad": 53}}
      print("Creating template %s" % row["name"]+".json")
      template["version"] = row["version"]
      template["reference"] = row["reference"]
      template["template"]["name"] = row["name"]
      template["template"]["service"] = row["service"]
      template["template"]["created_at"] = row["created_at"]
      template["template"]["owner"] = row["owner"]
      template["template"]["owner"] = row["owner"]
      template["template"]["bom_value"] = (row["bom_value"])
      template["site"] = row["site"]
      template["network"] = row["network"]
      template["engine"] = int(row["engine"])
      template["coordinates"] = int(row["coordinates"])
      template["transmitter"]["lat"] = float(row["lat"])
      template["transmitter"]["lon"] = float(row["lon"])
      template["transmitter"]["alt"] = float(row["alt"])
      template["transmitter"]["frq"] = float(row["frq"])
      template["transmitter"]["txw"] = float(row["txw"])
      template["transmitter"]["bwi"] = float(row["bwi"])
      template["transmitter"]["powerUnit"] = row["powerUnit"]
      template["receiver"]["lat"] = float(row["rxlat"])
      template["receiver"]["lon"] = float(row["rxlon"])
      template["receiver"]["alt"] = float(row["rxalt"])
      template["receiver"]["rxg"] = float(row["rxg"])
      template["receiver"]["rxs"] = float(row["rxs"])
      template["feeder"]["flt"] = row["flt"]
      template["feeder"]["fll"] = float(row["fll"])
      template["feeder"]["fcc"] = float(row["fcc"])
      template["antenna"]["mode"] = row["mode"]
      template["antenna"]["txg"] = float(row["txg"])
      template["antenna"]["txl"] = float(row["txl"])
      template["antenna"]["ant"] = float(row["ant"])
      template["antenna"]["azi"] = float(row["azi"])
      template["antenna"]["tlt"] = float(row["tlt"])
      template["antenna"]["hbw"] = float(row["hbw"])
      template["antenna"]["vbw"] = float(row["vbw"])
      template["antenna"]["fbr"] = float(row["fbr"])
      template["antenna"]["pol"] = row["pol"]
      template["model"]["pm"] = float(row["pm"])
      template["model"]["pe"] = float(row["pe"])
      template["model"]["ked"] = float(row["ked"])
      template["model"]["rel"] = float(row["rel"])
      template["environment"]["elevation"] = float(row["elevation"])
      template["environment"]["landcover"] = float(row["landcover"])
      template["environment"]["buildings"] = float(row["buildings"])
      template["environment"]["obstacles"] = float(row["obstacles"])
      template["environment"]["clt"] = row["clt"]
      template["output"]["units"] = row["units"]
      template["output"]["col"] = row["col"]
      template["output"]["out"] = float(row["out"])
      template["output"]["ber"] = float(row["ber"])
      template["output"]["mod"] = float(row["mod"])
      template["output"]["nf"] = float(row["nf"])
      template["output"]["res"] = float(row["res"])
      template["output"]["rad"] = float(row["rad"])





      with open(row["name"]+".json", "w",  encoding='utf-8') as jsonfile:
        json.dump(template, jsonfile,indent=2)
