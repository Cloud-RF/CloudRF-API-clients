import requests
import json
import time
import Keypad
from LCD1602 import CharLCD1602
import urllib3

# Raspberry Pi + CloudRF "AGC" demo for reducing RF power and saving batteries
#
# Requires a Freenove electronics starter kit or equivalent kit with a LCD and keypad
# Put your API key into api-key.txt and a JSON request template into radio_template.json
# API address:
# If you are using CloudRF, this is api.cloudrf.com
# If you have a SOOTHSAYER server, enter the IP
# If you rock and have an ARM instance of our API, it's localhost ;)
CloudRFAPI="localhost"

urllib3.disable_warnings()

# DEMO PATH
START_LAT = 51.761826
START_LON = -2.353536
END_LAT = 51.74
END_LON = -2.367
STEP_COUNT = 40
STEP_INTERVAL_S = 0.5

# DEMO POWER LEVELS
INITIAL_POWER_W = 2
MIN_POWER_W = 0.01
MAX_POWER_W = 2
TARGET_SIGNAL_POW_DBM = -90
THRESHOLD_SIGNAL_POW_DBM = -100

# MESSAGES FOR LCD
WARNING_MESSAGE = "WARNING"
ERROR_MESSAGE = "FAILURE"

def get_reciever_signal_pow_dbm(api_key, power, lat, lon, req_json):
    req_json["transmitter"]["txw"] = power
    req_json["transmitter"]["lat"] = lat
    req_json["transmitter"]["lon"] = lon

    response = requests.post(
        url = "https://"+CloudRFAPI+"/path",
        headers = {
            "key": api_key,
        },
        json = req_json,
        verify = False
    )

    signal_pow_dbm =  response.json()["Transmitters"][0]["Signal power at receiver dBm"]
    print("[{:.07f},{:.07f}] Tx power {:.05f}W -> Rx signal power {:.05f}dBm" .format(lat, lon, power, signal_pow_dbm))
 
    return signal_pow_dbm

def create_keypad():
    rows = 4
    cols = 4
    keys = [ '1', '2', '3', 'A', '4', '5', '6', 'B', '7', '8', '9', 'C', '*', '0', '#', 'D']
    row_pins = [18, 23, 24, 25]
    col_pins = [10, 22, 27, 17]
    debounce = 30 

    keypad = Keypad.Keypad(keys, row_pins, col_pins, rows, cols) 
    keypad.setDebounceTime(debounce)

    return keypad

def create_lcd():
    lcd = CharLCD1602()
    lcd.init_lcd()
    lcd.clear()

    return lcd

print("Program is starting...")
api_key = None

with open("./api-key.txt", "r") as f:
    api_key = f.read().strip("\n")

req_json = None
with open("radio_template.json") as f:
    req_json = json.load(f)

keypad = create_keypad()
lcd = create_lcd()
curr_power_w = INITIAL_POWER_W
curr_step = 0
curr_lat = START_LAT
curr_lon = START_LON
curr_signal_power_dbm = get_reciever_signal_pow_dbm(api_key, curr_power_w, curr_lat, curr_lon, req_json)
auto_power_mode = False

# Write to screen
lcd.clear()
lcd.write(0, 0, "{}, {}".format(str(curr_lat)[:7], str(curr_lon)[:7]))
lcd.write(0, 1, "{}W, {}dBm".format(curr_power_w, curr_signal_power_dbm))

last_step_time_s = time.process_time()

# Walk the path
try:
    while(True):
        if curr_step >= STEP_COUNT:
            break
        
        key = keypad.getKey()

        if key == "A":
            auto_power_mode = not auto_power_mode

        curr_time_s = time.process_time()

        if curr_time_s > last_step_time_s + STEP_INTERVAL_S:
            curr_step += 1
            curr_lat += (END_LAT - START_LAT) / STEP_COUNT
            curr_lon += (END_LON - START_LON) / STEP_COUNT
            curr_signal_power_dbm = get_reciever_signal_pow_dbm(api_key, curr_power_w, curr_lat, curr_lon, req_json)

            if auto_power_mode:
                curr_power_w = curr_power_w / pow(10, (curr_signal_power_dbm - TARGET_SIGNAL_POW_DBM) / 10)
                curr_power_w = max(MIN_POWER_W, min(curr_power_w, MAX_POWER_W))
                print("[{:.07f},{:.07f}] Auto power adjusted Tx power to {:.05f}W".format(curr_lat, curr_lon, curr_power_w))
                curr_signal_power_dbm = get_reciever_signal_pow_dbm(api_key, curr_power_w, curr_lat, curr_lon, req_json)

            if curr_power_w == MAX_POWER_W: 
                print("[{:.07f},{:.07f}] Using maximum Tx power".format(curr_lat, curr_lon))
            elif curr_power_w == MIN_POWER_W:
                print("[{:.07f},{:.07f}] Using minimum Tx power".format(curr_lat, curr_lon))

            lcd.clear()
            if curr_signal_power_dbm >= TARGET_SIGNAL_POW_DBM:
                lcd.write(0, 0, "{}, {}".format(str(curr_lat)[:7], str(curr_lon)[:7]))
                lcd.write(0, 1, "{}W, {}dBm".format(str(curr_power_w)[:4], str(curr_signal_power_dbm)[:4]))
            elif curr_signal_power_dbm >= THRESHOLD_SIGNAL_POW_DBM:
                lcd.write(0, 0, "{}, {}".format(str(curr_lat)[:7], str(curr_lon)[:7]))
                lcd.write(0, 1, "{} {}dBm".format(WARNING_MESSAGE, curr_signal_power_dbm)) 
                print("[{:.07f},{:.07f}] {}".format(curr_lat, curr_lon, WARNING_MESSAGE))
            else:
                lcd.write(0, 0, "{}, {}".format(str(curr_lat)[:7], str(curr_lon)[:7]))
                lcd.write(0, 1, "{} {}dBm".format(ERROR_MESSAGE, curr_signal_power_dbm))
                print("[{:.07f},{:.07f}] {}".format(curr_lat, curr_lon, ERROR_MESSAGE))

            last_step_time_s = curr_time_s

except KeyboardInterrupt:
    pass