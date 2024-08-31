# CloudRF Python Client

In this directory contains a Python client which can be used to interface with the CloudRF API.

## Installation

To get started quickly with this example, you should ensure that you have Python installed on your machine, then you should `pip` install the libraries in the [requirements.txt](requirements.txt) file:

```bash
python3 -m pip install -r requirements.txt
# or
python -m pip install -r requirements.txt
```

Once done then you can execute the [CloudRF.py](CloudRF.py) script. This script has been written to be as verbose and helpful as possible and so should provide useful feedback when you have passed in an incorrect or missing parameter.

```bash
python3 CloudRF.py
# or
python CloudRF.py
```

Depending on your system you may or may not be required to specify the version of Python, as indicated above. For all other examples in this README the examples will be explicitly passing in the version of Python, however depending on your system you may be required to not use the version.

Upon executing the above you will be presented with an error message, this is normal. This error message will detail that along with executing the script you should also be passing in the type of request which you are looking run, for example:

```bash
python3 CloudRF.py area
```

The above example will initialise the `CloudRF.py` script in `area` mode and will go through the process for an `area` API request.

For each of the request types you can use the `-h` or `--help` flag to output in full a description of what the request type is along with all required and optional parameters.


```bash
usage: CloudRF.py [-h] -t INPUT_TEMPLATE [-i INPUT_CSV] -k API_KEY [-u BASE_URL] [--no-strict-ssl] [-srq] [-r] [-o OUTPUT_DIRECTORY] [-s {all,kmz,png,shp,tiff,url}] [-v] [-w WAIT]

CloudRF Area API

Area coverage performs a circular sweep around a transmitter out to a user defined radius.
It factors in system parameters, antenna patterns, environmental characteristics and terrain data to show a heatmap in customisable colours and units.

options:
  -h, --help            show this help message and exit
  -t INPUT_TEMPLATE, --input-template INPUT_TEMPLATE
                        Absolute path to input JSON template used as part of the calculation. (default: None)
  -i INPUT_CSV, --input-csv INPUT_CSV
                        Absolute path to input CSV, used in combination with --input-template to customise your template to a specific usecase. The CSV header row must be included.
                        Header row values must be defined in dot notation format of the template key that they are to override in the template, for example transmitter latitude will
                        be named as "transmitter.lat". (default: None)
  -k API_KEY, --api-key API_KEY
                        Your API key to the CloudRF API service. (default: None)
  -u BASE_URL, --base-url BASE_URL
                        The base URL for the CloudRF API service. (default: https://api.cloudrf.com/)
  --no-strict-ssl       Do not verify the SSL certificate to the CloudRF API service. (default: True)
  -srq, --save-raw-request
                        Save the raw request made to the CloudRF API service. This is saved to the --output-directory value. (default: False)
  -r, --save-raw-response
                        Save the raw response from the CloudRF API service. This is saved to the --output-directory value. (default: False)
  -o OUTPUT_DIRECTORY, --output-directory OUTPUT_DIRECTORY
                        Absolute directory path of where outputs are saved. (default: /home/alex/CloudRF-API-clients/python/output)
  -s {all,kmz,png,shp,tiff,url}, --output-file-type {all,kmz,png,shp,tiff,url}
                        Type of file to be downloaded. (default: kmz)
  -v, --verbose         Output more information on screen. This is often useful when debugging. (default: False)
  -w WAIT, --wait WAIT  Time in seconds to wait before running the next calculation. (default: 3)

For more details about this script please consult the GitHub documentation at https://github.com/Cloud-RF/CloudRF-API-clients.

```
## Hello World!

The below example will do a single `area` request based upon the values in the `5G-CBand-sector.json` template and save a KMZ file

```bash
python3 CloudRF.py area \
    --api-key MY-API-KEY \
    --input-template ../templates/5G-CBand-sector.json -s kmz
```

## Options

The script has a number of parameters which can be passed in to adjust the request and response.

### API Key

The `-k` or `--api-key` flag is required by all request types to authenticate against the CloudRF API service.

```bash
python3 CloudRF.py area --api-key YOUR-API-KEY-HERE
```

### Base URL

The `-u` or `--base-url` flag can be used to define a different endpoint for the CloudRF API service which could be a private SOOTHSAYER server.

By default the script is set to use `https://api.cloudrf.com`.

```bash
python3 CloudRF.py area --base-url https://soothsayer.local
```

### Disable Strict SSL

When customising the `--base-url` you may be using a server which has a self-signed SSL certificate and therefore the connection over HTTPS can not be verified and will fail. A workaround for this is to disable strict SSL verification if you trust the server which you are making the request to. This is done with the `--no-strict-ssl` flag.

By default this value is disabled.

```bash
python3 CloudRF.py area --no-strict-ssl
```

### Input Template

Making use of the `-t` or `--input-template` is used to customise your request body through the use of a JSON template, such as those available in the [templates](../templates/) directory. The argument passed into this flag should be given as an absolute path.

```bash
python3 CloudRF.py area --input-template ../templates/5G-CBand-sector.json
```

For most request types `-t` or `--input-template` is a required flag.

### Input CSV Template

Making use of the `-i` or `--input-csv` flag is to pass multiple values through to your request. The argument pass into this flag should be given as an absolute path.

```bash
python3 CloudRF.py area --input-csv /home/user/CloudRF-API-clients/python/area.csv
```

The CSV file should include a header row whereby header keys are given in dot notation format, for example to specify the `lat` key on the `transmitter` object would have a header key value of `transmitter.lat` in the CSV.

Depending on your request type will determine how the CSV file is used:

- For `area` and `path` requests the CSV is optional is used to send a request for each of the row you have in the CSV. The values which you specify in the CSV will override the values which you have set in the `--input-template` flag. You are free to override as many or as few values as you wish, there are no requirements to set all values. If you do not specify the flag then the values within the JSON template from `--input-template` will be used.
- For `points` and `multisite` requests this flag is required and each of the row in the CSV represents a point or site for your request. As such the CSV must include all of the fields for the point or site. Please consult to `--help` dialog to see which headers are required for each request.

You can find examples CSVs for each of the requests at:

- [area](area.csv)
- [multisite](multisite.csv)
- [path](path.csv)
- [points](points.csv)

### Save Raw Request

You can use the `--save-raw-request` flag to save the request which was sent to the CloudRF API. This is useful for debugging, or to understand the request which is being made.

By default this value is disabled.

### Save Raw Response

You can use the `--save-raw-response` flag to save the response which was returned from the CloudRF API. This is useful for debugging, or to understand the response which was sent back.

By default this value is disabled.

### Define Output Directory

You can use the `--output-directory` flag to specify where you wish for your output files to be saved.

By default this value is set to the relative directory of `output` from the same path as the `CloudRF.py` script. For example, if your `CloudRF.py` script is located in `/home/user/CloudRF.py`, then the default output directory will be `/home/user/output`.

### Define Output File Type

You can use the `--output-file-type` flag to specify the output file type of a particular request. 

### Verbose Debugging

You can use the `--verbose` 

### Other Flags Not Listed Here

You are encouraged to make use of the `-h`/`--help` flag to understand what each of the available options are as all request types can be customised based upon these flags, but also to view default values which are used before they are customised.

## Example Usage

Below shows some examples of the uses of this Python script.

Please note that for more verbose instructions on each of the request types then you can the `--help` flag to provide full details of how to use each.

### Area

#### Basic Area Request

The below example will do a single `area` request based upon the values in the `5G-CBand-sector.json` template and fetch the KMZ afterwards.

```bash
python3 CloudRF.py area \
    --api-key MY-API-KEY \
    --input-template ../templates/5G-CBand-sector.json -s kmz
```

#### Fully Customised Area Request

The below example is fully customised of all that available options. 

It runs numerous requests based upon the rows in `area.csv` which override any values in `5G-CBand-sector.json`. It uses `https://soothsayer` as the CloudRF API service and disabled SSL verification. It saves all output types, the raw request and raw response to the `5G-outputs` directory and runs in `verbose` mode to aid with any potential issues which may occur during the process.

```bash
python3 CloudRF.py area \
    --api-key MY-API-KEY \
    --input-template ../templates/5G-CBand-sector.json \
    --input-csv area.csv \
    --base-url https://soothsayer \
    --no-strict-ssl \
    --save-raw-request \
    --save-raw-response \
    --output-directory 5G-outputs \
    --output-file-type all \
    --verbose
```

### Interference

The below example shows a basic `interference` request for the network name of `MY-NETWORK`. This assumes that you have already created `area` calculations with the network name of `MY-NETWORK` to be used to build the interference layer.

```bash
python3 CloudRF.py interference \
    --api-key MY-API-KEY \
    --network-name MY-NETWORK
```

### Mesh

The below example shows a basic `mesh` request for the network name of `MY-NETWORK`. This assumes that you have already created `area` calculations with the network name of `MY-NETWORK` to be used to build the mesh network layer.

```bash
python3 CloudRF.py mesh \
    --api-key MY-API-KEY \
    --network-name MY-NETWORK
```

### Multisite

The below example shows how a `multisite` request can be executed. Please note that an input CSV is required to customise sites in order to execute a successful `multisite` request. An example CSV can be found at [multisite.csv](multisite.csv).

```bash
python3 CloudRF.py multisite \
    --api-key MY-API-KEY \
    --input-template ../templates/5G-CBand-sector.json \
    --input-csv multisite.csv
```

### Network

The below example shows a basic request for the network name of `MY-NETWORK`. This assumes that you have already created `area` calculations with the network name of `MY-NETWORK` to be used to build the mesh network layer.

```bash
python3 CloudRF.py network \
    --api-key MY-API-KEY \
    --network-name MY-NETWORK \
    --latitude 38.911892 \
    --longitude 1.442087 \
    --altitude 10
```

### Path

The below example shows a basic use case for the `path` API.

```bash
python3 CloudRF.py path \
    --api-key MY-API-KEY \
    --input-template ../templates/5G-CBand-sector.json
```

### Points

The below example shows a basic use case for the `points` API. Please note that a CSV of points is required. An example CSV can be found at [points.csv](points.csv).

```bash
python3 CloudRF.py points \
    --api-key MY-API-KEY \
    --input-template ../templates/5G-CBand-sector.json \
    --input-csv points.csv
```
