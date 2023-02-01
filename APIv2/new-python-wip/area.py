#!/usr/bin/env python3
import argparse
import datetime
import json
import os
import pathlib
import requests
import shutil
import stat
import sys
import textwrap
import urllib3

def areaCalculation(jsonData):
    now = datetime.datetime.now()
    requestName = now.strftime('%Y%m%d%H%M%S_' + now.strftime('%f')[:3])
    fullSaveBasePath = str(arguments.output_directory).rstrip('/') + '/' + requestName

    try:
        response = requests.post(
            url = str(arguments.base_url).rstrip('/') + '/area',
            headers = {
                'key': arguments.api_key
            },
            json = jsonData,
            verify = arguments.strict_ssl
        )
        if response.status_code != 200:
            print('An HTTP %d error occurred with your request. Full response from the CloudRF API is listed below.' % response.status_code)
            print(response.text)

            if response.status_code == 400:
                sys.exit('You likely have bad values in your input JSON/CSV. For good examples please consult https://github.com/Cloud-RF/CloudRF-API-clients')
            if response.status_code == 401:
                sys.exit('Your API key is likely incorrect.')
            if response.status_code == 500:
                sys.exit('A problem with the CloudRF API service appears to have occurred.')
        else:
            # Save the output based on what was requested
            if arguments.output_file_type == 'all':
                for type in allowedTypes:
                    getOutputFile(response.text, type, fullSaveBasePath)
            else:
                getOutputFile(response.text, arguments.output_file_type, fullSaveBasePath)

        if arguments.verbose:
            print(response.text)
        
        if arguments.save_raw_response:
            jsonFilePath = fullSaveBasePath + '.json'
            with open(jsonFilePath, 'w') as rawResponseFile:
                rawResponseFile.write(response.text)

            print('Raw response saved at ' + jsonFilePath)
        
    except requests.exceptions.SSLError:
        sys.exit('SSL error occurred. This is common with self-signed certificates. You can try disabling SSL verification with --no-strict-ssl.')

def checkApiKey():
    parts = str(arguments.api_key).split('-')
    externalPrompt = 'Please make sure that you are using the correct key from https://cloudrf.com/my-account'

    if len(parts) != 2:
        sys.exit('Your API key appears to be in the incorrect format. ' + externalPrompt)

    if not parts[0].isnumeric():
        sys.exit('Your API key UID component appears to be incorrect. ' + externalPrompt)

    if len(parts[1]) < 30:
        sys.exit('Your API key token component appears to be incorrect. ' + externalPrompt)

def checkPermissions():
    if not os.path.exists(arguments.input_template):
        sys.exit('Your input template JSON file (%s) could not be found. Please check your path. Please note that this should be in absolute path format.' % arguments.input_template)
    else:
        verboseLog('Input template JSON file (%s) found with file permissions: %s' % (arguments.input_template, oct(stat.S_IMODE(os.lstat(arguments.input_template).st_mode))))

    if arguments.input_csv:
        if not os.path.exists(arguments.input_csv):
            sys.exit('Your input CSV file (%s) could not be found. Please check your path. Please note that this should be in absolute path format.' % arguments.input_csv)
        else:
            verboseLog('Input CSV file (%s) found with file permissions: %s' % (arguments.input_csv, oct(stat.S_IMODE(os.lstat(arguments.input_csv).st_mode))))
    else:
        print('Input CSV has not been specified. Default values in input template JSON file will be used.')

    if not os.path.exists(arguments.output_directory):
        verboseLog('Output directory (%s) does not exist, attempting to create.' % arguments.output_directory)
        os.makedirs(arguments.output_directory)
        verboseLog('Output directory (%s) created successfully.' % arguments.output_directory)

    verboseLog('Output directory (%s) exists with permissions: %s' % (arguments.output_directory, oct(stat.S_IMODE(os.lstat(arguments.output_directory).st_mode))))

    try:
        # Check if any file can be written to the output directory
        testFilePath = str(arguments.output_directory).rstrip('/') + '/tmp'
        open(testFilePath, 'a')
        os.remove(testFilePath)
    except PermissionError:
        sys.exit('Unable to create files in output directory (%s)' % arguments.output_directory)

def checkValidJsonTemplate():
    try:
        with open(arguments.input_template, 'r') as jsonTemplateFile:
            return json.load(jsonTemplateFile)
    except PermissionError:
        sys.exit('Permission error when trying to read input template JSON file (%s)' % arguments.input_template)
    except json.decoder.JSONDecodeError:
        sys.exit('Input template JSON file (%s) is not a valid JSON file.' % arguments.input_template)
    except:
        sys.exit('An unknown error occurred when checking input template JSON file (%s)' % (arguments.input_template))

class PythonValidator:
    def version():
        requiredMajor = 3
        minimumMinor = 8

        if sys.version_info.major != requiredMajor or sys.version_info.minor < minimumMinor:
            sys.exit('Your Python version (%s) does not meet the minimum required version of %s' % (
                    str(sys.version_info.major) + '.' + str(sys.version_info.minor), 
                    str(requiredMajor) + '.' + str(minimumMinor)
                )
            )

def getOutputFile(rawJson, outputType, saveBasePath):
    print('Getting output file: ' + outputType)

    responseJson = json.loads(rawJson)

    if outputType == 'png':
        # PNG links exist already in the response JSON so we can just grab them from there
        streamToFile(responseJson['PNG_Mercator'], saveBasePath + '.3857.png')
        print('3857 projected PNG saved to ' + saveBasePath + '.3857.png')
        streamToFile(responseJson['PNG_WGS84'], saveBasePath + '.4326.png')
        print('4326 projected PNG saved to ' + saveBasePath + '.4326.png')
    else:
        # Anything else we just pull out of the archive
        savePath = saveBasePath + '.' + outputType
        streamToFile(
            url = str(arguments.base_url).rstrip('/') + '/archive/' + responseJson['sid'] + '/' + outputType,
            savePath = savePath
        )
        print('%s file saved to %s' % (outputType, savePath))

def streamToFile(url, savePath):
    response = requests.get(url, stream = True, verify = arguments.strict_ssl)
    with open(savePath, 'wb') as outputFile:
        shutil.copyfileobj(response.raw, outputFile)
    del response
    return savePath

def verboseLog(message):
    if arguments.verbose:
        print(message)

# We combine multiple formatter classes into one, this allows us to show default values and have nice styling with --help
class ArgparseCustomFormatter(argparse.RawDescriptionHelpFormatter, argparse.ArgumentDefaultsHelpFormatter):
    pass

if __name__ == '__main__':
    PythonValidator.version()

    allowedTypes = ['kmz', 'png', 'shp', 'tiff']

    # Argument parsing
    parser = argparse.ArgumentParser(
        description = textwrap.dedent(f'''
            CloudRF Area API

            Area coverage performs a circular sweep around a transmitter out to a user defined radius.
            It factors in system parameters, antenna patterns, environmental characteristics and terrain data to show a heatmap in customisable colours and units.
        '''),
        formatter_class = ArgparseCustomFormatter,
        epilog = 'For more details about this script please consult the GitHub documentation at https://github.com/Cloud-RF/CloudRF-API-clients'
    )

    currentScriptPath = str(pathlib.Path(__file__).parent.resolve()).rstrip('/') + '/output'

    parser.add_argument('-t', '--input-template', dest = 'input_template', required = True, help = 'Absolute path to input JSON template used as part of the calculation.')
    parser.add_argument('-i', '--input-csv', dest = 'input_csv', help = 'Absolute path to input CSV, used in combination with --input-template to customise your template to a specific usecase.')
    parser.add_argument('-k', '--api-key', dest = 'api_key', required = True, help = 'Your API key to the CloudRF API service.')
    parser.add_argument('-u', '--base-url', dest = 'base_url', default = 'https://api.cloudrf.com/', help = 'The base URL for the CloudRF API service.')
    parser.add_argument('--no-strict-ssl', dest = 'strict_ssl', action="store_false", default = True, help = 'Do not verify the SSL certificate to the CloudRF API service.')
    parser.add_argument('-r', '--save-raw-response', dest = 'save_raw_response', default = False, action = 'store_true', help = 'Save the raw response from the CloudRF API service. This is saved to the --output-directory value.')
    parser.add_argument('-o', '--output-directory', dest = 'output_directory', default = currentScriptPath, help = 'Absolute directory path of where outputs are saved.')
    parser.add_argument('-s', '--output-file-type', dest = 'output_file_type', choices = ['all'] + allowedTypes, help = 'Type of file to be downloaded.', default = 'kmz')
    parser.add_argument('-v', '--verbose', action="store_true", default = False, help = 'Output more information on screen. This is often useful when debugging.')

    arguments = parser.parse_args()

    if arguments.verbose:
        parser.print_help()
        print()

    if not arguments.strict_ssl:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    checkApiKey()
    checkPermissions()
    jsonTemplate = checkValidJsonTemplate()

    if jsonTemplate['receiver']['lat'] != 0:
        print('Your template has a value in the receiver.lat key which will prevent an area calculation. Setting a safe default.')
        jsonTemplate['receiver']['lat'] = 0

    if jsonTemplate['receiver']['lon'] != 0:
        print('Your template has a value in the receiver.lon key which will prevent an area calculation. Setting a safe default.')
        jsonTemplate['receiver']['lon'] = 0

    areaCalculation(jsonTemplate)

    print('Process completed. Please check your output folder (%s)' % arguments.output_directory)