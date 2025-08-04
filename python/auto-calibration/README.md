# CloudRF Area Calibration Script

This Python script allows you to calibrate an input CloudRF template against input CSV survey data, and to save time with obtaining the best error when using CloudRF.

The script works with Python. Please note that this script has been tested against a minimum of Python `3.13`. Other versions may work, but results may vary.

## Quick Start

If you have Docker installed on your system, you can run this script quickly with the following:

```bash
docker run -it \
    -v "$(pwd)":/app \
    -w /app \
    python:latest \
    bash -c "pip install pandas rasterio requests && \
    ./area-calib.py -k <YOUR-CLOUDRF-API-KEY>"
```

This is the script in it's most simple format. It will install required Python modules and then go ahead and work against the public CloudRF API to calibrate against input data.

You can also run this script directly on your system, but ensure that you have the correct recommended version of Python installed, along with supporting modules.

## Script Arguments

A number of arguments are supported, and some expected, by the Python script. You can see a full list of these by passing in the `--help` argument:

```console
usage: area-calib.py [-h] [-i INPUT_CSV] [-t INPUT_TEMPLATE] [-u BASE_URL] [--no-strict-ssl] -k API_KEY [-w WAIT] [--population-count POPULATION_COUNT] [--max-generation MAX_GENERATION] [--elite-count ELITE_COUNT]
                     [--discrete-mutation-rate DISCRETE_MUTATION_RATE] [--continuous-mutation-variability CONTINUOUS_MUTATION_VARIABILITY]

CloudRF Area Calibration

This script attempts to fit calibration data against CloudRF area calculations, and then uses a genetic algorithm to calibrate the settings.

The number of area calls required will be POPULATION_COUNT X (MAX_GENERATION + 1)

options:
  -h, --help            show this help message and exit
  -i, --input-csv INPUT_CSV
                        Absolute path to input CSV reference data to be used in calibration. The CSV header row must be included. (default: data.csv)
  -t, --input-template INPUT_TEMPLATE
                        Absolute path to input CloudRF JSON template used as part of the calculation to calibrate against. (default: CloudRF_template.json)
  -u, --base-url BASE_URL
                        The base URL for the CloudRF API service. (default: https://api.cloudrf.com/)
  --no-strict-ssl       Do not verify the SSL certificate to the CloudRF API service. (default: True)
  -k, --api-key API_KEY
                        Your API key to the CloudRF API service. (default: None)
  -w, --wait WAIT       Time in seconds to wait before running the next calculation. (default: 0.1)
  --population-count POPULATION_COUNT
                        The number of configs in a generation. (default: 10)
  --max-generation MAX_GENERATION
                        The maximum number of generations to run. (default: 10)
  --elite-count ELITE_COUNT
                        The number of elite configs to retain for the next generation, chosen by best fit. (default: 3)
  --discrete-mutation-rate DISCRETE_MUTATION_RATE
                        The mutation rate for discrete parameters. (default: 0.1)
  --continuous-mutation-variability CONTINUOUS_MUTATION_VARIABILITY
                        The variability for continuous mutations. (default: 0.2)
```

More details are provided below:

- `--help` - This argument provides a list of all parameters accepted by the script.
- `--input-csv` | `-i` - This argument is the input CSV which contains your survey data. This CSV should contain headers, and the headers should contain each of `latitude`, `longitude`, and `received_power`. An example CSV is provided in [data.csv](data.csv).
- `--input-template` | `-t` - This argument is the input CloudRF JSON template for the site you are calibrating against. This can be exported directly from your CloudRF product. An example of this is provided in [CloudRF_template.json](CloudRF_template.json).
- `--base-url` | `-u` - This argument allows you to override which CloudRF API you are working against. By default this is the production CloudRF API, but you may wish to override it to run against your own SOOTHSAYER server, if you have one.
- `--no-strict-ssl` - This argument disables SSL verification. This is useful when you are working in environments where a self-signed SSL certificate is used, such as if you are using SOOTHSAYER.
- `--api-key` | `-k` - This argument is the API key to be used for entering your API against the CloudRF API.
- `--wait` | `-w` - This argument sets a small sleep/wait between requests. This can be useful when working against CloudRF environments which are enforcing rate limiting to avoid hitting errors.
- `--population-count` - The script works around a genetic algorithm. This argument allows you to specify the total number of population with the starting genetic config, where each config might have some very slightly different values to allow for calibration. Please note that larger population counts provides larger variety to calibration against, but increases the processing time and API calls.
- `--max-generation` - This is the total number of generations which will be produced in total. Each generation is tweaked slightly with the purpose of finding a better calibration. Please note that increasing the number of generations may result in better calibration, but with longer processing times and more API calls.
- `--elite-count` - This argument is the number of elite configurations to keep between generations. A higher number will mean less variety between generations, but may lead to better calibration.
- `--discrete-mutation-rate` - This argument configures how much discrete parameters are likely to mutate. A higher number increases the probability of mutation.
- `--continuous-mutation-variability` - This argument configures the variability of mutation for continuous parameters. A higher number will increase the variability of mutation.

## Example Outputs

Taking the example data provided in [CloudRF_template.json](CloudRF_template.json) and [data.csv](data.csv), below shows an example output for the default values:

- Population count - `10`.
- Max generation - `10`.
- Elite count - `3`.
- Discrete mutation rate - `0.1`.
- Continuous mutation variability - `0.2`.
