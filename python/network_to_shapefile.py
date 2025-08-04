"""
This script merges a CloudRF network into a single ESRI Shapefile.

Data fields can be specified by editing the CONSTANT_DATA_FIELDS.

The current fields are from the FCC Broadband Data Collection specification section 8.1.1.

The script downloads the Shapefile from CloudRF to NETWORK_NAME-in.zip,
and creates a Shapefile called NETWORK_NAME-out.zip with the specified fields.
"""

import requests
import zipfile
import shapefile  # pyshp
import shutil

API = "https://api.cloudrf.com"
API_KEY = "YOUR API KEY HERE"
NETWORK = "BDCDEMO" # Your Network from CloudRF

DISABLE_SSL_VERIFICATION = False

MAX_DBM = -60
MIN_DBM = -105

# Edit these fields to match your data/network and add your own

CONSTANT_DATA_FIELDS = {
    "providerid": {
        "type": "number",
        "value": 130403,
    },
    "brandname": {
        "type": "text",
        "value": "Tarana",
    },
    "technology": {
        "type": "number",
        "value": 500,
    },
    "mindown": {
        "type": "number",
        "value": 7.0,
    },
    "minup": {
        "type": "number",
        "value": 1.0,
    },
    "environmnt": {"type": "number", "value": 1},
}

VARIABLE_DATA_FIELDS = {"minsignal": {"type": "number", "func": lambda dBm: dBm}}

FIELD_TYPES = {
    "text": "C",
    "number": "N",
}

if DISABLE_SSL_VERIFICATION:
    import urllib3

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

if __name__ == "__main__":

    mesh_response = requests.get(
        f"{API}/mesh",
        params={"network": NETWORK},
        headers={"key": API_KEY},
        verify=not DISABLE_SSL_VERIFICATION,
    )
    mesh_response.raise_for_status()
    mesh_response = mesh_response.json()

    shp_url = mesh_response["kmz"][:-3] + "shp"

    shp_file_in = f"{NETWORK}-in.zip"
    shp_file_out = f"{NETWORK}-out"

    sh_response = requests.get(
        shp_url, stream=True, verify=not DISABLE_SSL_VERIFICATION
    )
    with open(shp_file_in, "wb") as out_file:
        shutil.copyfileobj(sh_response.raw, out_file)

    color_key = {}
    for entry in mesh_response["key"]:
        assert entry["l"].endswith("dBm")
        color_key[entry["r"]] = float(entry["l"][:-3])
        print(entry)

    with shapefile.Reader(shp_file_in) as r, shapefile.Writer(shp_file_out) as w:

        for name, field in CONSTANT_DATA_FIELDS.items():
            if field["type"] not in FIELD_TYPES:
                raise Exception(f"Unrecognized field {field['type']}")
            w.field(name, FIELD_TYPES[field["type"]])

        for name, field in VARIABLE_DATA_FIELDS.items():
            if field["type"] not in FIELD_TYPES:
                raise Exception(f"Unrecognized field {field['type']}")
            w.field(name, FIELD_TYPES[field["type"]])

        for shape_record in r.iterShapeRecords():
            dBm = color_key[shape_record.record[0]]
            dBm = max(dBm, MIN_DBM)
            dBm = min(dBm, MAX_DBM)

            w.shape(shape_record.shape)

            records = []

            for field in CONSTANT_DATA_FIELDS.values():
                records.append(field["value"])

            for field in VARIABLE_DATA_FIELDS.values():
                records.append(field["func"](dBm))

            w.record(*records)

    with zipfile.ZipFile(f"{shp_file_out}.zip", "w") as zip_file:
        zip_file.write(f"{shp_file_out}.shp")
        zip_file.write(f"{shp_file_out}.shx")
        zip_file.write(f"{shp_file_out}.dbf")
