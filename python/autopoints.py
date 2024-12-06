
import argparse
import json
import pandas
import requests

if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument("--lat", required = True, help = 'Receiever latitiude.')
    parser.add_argument("--lon", required = True, help = 'Receiever longitude.')
    parser.add_argument("--alt", required = True, help = 'Receiever altitude (m).')

    parser.add_argument("-t", "--template-json", dest="template", required = True, help = 'Path to radio settings template json file.')

    parser.add_argument("-k", "--api-key", dest="key", required=True, help = "cloudrf.com API key.")

    parser.add_argument("-i", "--input-csv", dest="input", required = True, help = 'Path to input csv file containing transmitter positions. Expected headers are "lat", "lon", and "alt".')
    parser.add_argument("-o", "--output-csv", dest="output", required = True, help = 'Path to output csv file, where results will be written.')

    args = parser.parse_args()

    print(f"Receiver latitiude: {args.lat}")
    print(f"Receiver longitude: {args.lon}")
    print(f"Receiver altitude: {args.alt}")

    df = pandas.read_csv(args.input)

    print(f"Transmitter count: {len(df.index)}")

    with open(args.template) as template:
        request = json.load(template)

    request['receiver']['lat'] = args.lat
    request['receiver']['lon'] = args.lon
    request['receiver']['alt'] = args.alt

    request['points'] = []

    for index, row in df.iterrows():
        request['points'].append({'lat': row.lat, 'lon': row.lon, 'alt': row.alt})

    print("API Call:")
    print()
    print(json.dumps(request, indent = 4))
    print()

    response = requests.post(
        url = "https://api.cloudrf.com/points",
        headers = {
            'key': args.key
        },
        json = request,
    )

    print(f"Response Code: {response.status_code}")

    if response.status_code != 200:
        print(f"Response body: {response.content}")
        exit(1)

    result = response.json()

    print(f"Response:")
    print()
    print(json.dumps(result, indent = 4))
    print()

    output = []

    for transmitter in result["Transmitters"]:
        output.append({"server": transmitter["server"], "lat": transmitter["Latitude"], "lon": transmitter["Longitude"], "alt": transmitter["Antenna height m"], "distance": transmitter["Distance to receiver km"], "path_loss": transmitter["Computed path loss dB"],"received_power": transmitter["Signal power at receiver dBm"]})

    output = pandas.DataFrame(output)

    print("Result:")
    print(output)

    output.to_csv(args.output, index = False)