# DF enhancement demo

This demo script accepts a line of bearing (LoB) and a received power reading (dBm) and outputs a KMZ layer. 

## Usage

```
python3 cf_lob.py --lob 122 --dbm -88 --kmz out.kmz

Calculation cache hit for location: 51.05966, -2.7462
Loading Area Calculation Result
Cutting Triangle with bearing 122.0
Converting Image to Delta Map with recieved power at -88.0dBm
Generating KMZ: out.kmz
Done. You can now open out.kmz in a KMZ viewer
```
