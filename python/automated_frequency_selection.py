import copy
import requests
import urllib3
import numpy as np

# Compare a pool of frequencies to recommend the best one for a link

FREQUENCIES = [600, 1220, 2222]

CLOUDRF_API = "https://api.cloudrf.com"
CLOUDRF_API_KEY = ""
REQUEST_VERIFY_SSL = True

TEMPLATE = {
    "network": "FreqSelection",
    "transmitter": {
        "lat": 51.833420,
        "lon": -2.233008,
        "alt": 10,
        "txw": 10,
        "bwi": 1,
    },
    "antenna": {
        "txg": 2.15,
        "ant": 1,
    },
    "receiver": {
        "lat": 51.879889,
        "lon": -2.264917,
        "alt": 2,
        "rxs": 10,
    },
    "model": {
        "pm": 10,
        "pe": 2,
        "ked": 4,
        "rel": 50,
    },
    "environment": {
        "clt": "Minimal.clt",
        "elevation": 2,
        "landcover": 1,
        "buildings": 1,
        "obstacles": 1,
    },
    "output": {
        "out": 4,
        "nf": "database",
        "res": 30,
    },
}

if __name__ == "__main__":

    if not REQUEST_VERIFY_SSL:
        urllib3.disable_warnings()

    results = []

    for freq in FREQUENCIES:

        request = copy.deepcopy(TEMPLATE)
        request["transmitter"]["frq"] = freq
        request["site"] = f"Freq_{freq}"

        response = requests.post(
            f"{CLOUDRF_API}/path",
            json=request,
            headers={"key": CLOUDRF_API_KEY},
            verify=REQUEST_VERIFY_SSL,
        ).json()

        received_power = np.array(response["Transmitters"][0]["dBm"])
        noise_floor = np.array(response["Transmitters"][0]["Noise_dBm"])
        channel_noise = response["Transmitters"][0]["Johnson Nyquist noise dB"]

        snr = received_power - noise_floor - channel_noise

        count_above_threshold = (snr > TEMPLATE["receiver"]["rxs"]).sum()

        results.append([freq, 100.0 * count_above_threshold / len(received_power)])

    freq_title = "Frequency (MHz)"
    percent_title = "Percentage above threshold (%)"
    print(f"|-{'-' * len(freq_title)}-|-{'-' * len(percent_title )}-|")
    print(f"| {freq_title} | {percent_title} |")
    print(f"|-{'-' * len(freq_title)}-|-{'-' * len(percent_title )}-|")
    for freq, percent in results:
        print(f"| {freq:{len(freq_title)}.2f} | {percent:{len(percent_title)}.2f} |")
    print(f"|-{'-' * len(freq_title)}-|-{'-' * len(percent_title )}-|")
