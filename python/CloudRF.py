#!/usr/bin/env python3

import argparse
import csv
import datetime
import json
import os
import pathlib
import re
import requests
import stat
import sys
import textwrap
import time
import urllib3

from core.ArgparseCustomFormatter import ArgparseCustomFormatter
from core.PythonValidator import PythonValidator

class CloudRF:
    allowedOutputTypes = []
    calledFromPath = None
    description = 'CloudRF'
    requestType = None

    ALLOWED_REQUEST_TYPES = ['area', 'interference', 'mesh', 'multisite', 'network', 'path', 'points']
    CSV_REQUIRED_HEADERS_MULTISITE = ['lat', 'lon', 'alt', 'frq', 'txw', 'bwi', 'antenna.txg', 'antenna.txl', 'antenna.ant', 'antenna.azi', 'antenna.tlt', 'antenna.hbw', 'antenna.vbw', 'antenna.fbr', 'antenna.pol']
    CSV_REQUIRED_HEADERS_POINTS = ['lat', 'lon', 'alt']
    URL_GITHUB = 'https://github.com/Cloud-RF/CloudRF-API-clients'

    def __init__(self, REQUEST_TYPE):
        # Where was the script called from?
        self.calledFromPath = pathlib.Path(__file__).parent.resolve()
        self.requestType = REQUEST_TYPE

        PythonValidator.version()
        self.__validateRequestType()

        # We use the first argument passed in to determine the type of request, but this conflicts with argparse, need to remove it
        sys.argv.pop(1)

        self.__argparseInitialiser()

        # If we are in verbose mode then just output everything
        if self.__arguments.verbose:
            self.__parser.print_help()
            print()

        if not self.__arguments.strict_ssl:
            self.__verboseLog('Strict SSL disabled.')
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        self.__validateApiKey()
        self.__validateFileAndDirectoryPermissions()

        if self.requestType in ['area', 'multisite', 'path', 'points']:
            self.__jsonTemplate = self.__validateJsonTemplate()
            self.__csvInputList = self.__validateCsv()

            if self.__arguments.input_csv and self.__csvInputList:
                # For points/multisite requests the CSV input is handled differently to others
                if self.requestType == 'points':
                    newJsonData = self.__customiseJsonPointsFromCsv(templateJson = self.__jsonTemplate, csvListOfDictionaries = self.__csvInputList)
                    self.__calculate(jsonData = newJsonData)
                elif self.requestType == 'multisite':
                    newJsonData = self.__customiseJsonMultisiteFromCsv(templateJson = self.__jsonTemplate, csvListOfDictionaries = self.__csvInputList)
                    self.__calculate(jsonData = newJsonData)
                else:
                    # CSV has been used, run a request for each of the CSV rows
                    for row in self.__csvInputList:
                        # Adjust the input JSON template to meet the values which are found in the CSV row
                        newJsonData = self.__customiseJsonFromCsvRow(templateJson = self.__jsonTemplate, csvRowDictionary = row)
                        self.__calculate(jsonData = newJsonData)
            else:
                # Just run a calculation based on the template
                self.__calculate(jsonData = self.__jsonTemplate)

        elif self.requestType in ['interference', 'network', 'mesh']:
            # Each of these do not use JSON data, instead they make use of parameters which are expected in argparse
            self.__calculate(jsonData = None)

        sys.exit('Process completed. Please check your output folder (%s)' % self.__arguments.output_directory)

    def __argparseInitialiser(self):
        self.__parser = argparse.ArgumentParser(
            description = textwrap.dedent(self.description),
            formatter_class = ArgparseCustomFormatter,
            epilog = 'For more details about this script please consult the GitHub documentation at %s.' % self.URL_GITHUB
        )

        # Some endpoints have common inputs
        if self.requestType in ['area', 'multisite', 'path', 'points']:
            self.__parser.add_argument('-t', '--input-template', dest = 'input_template', required = True, help = 'Absolute path to input JSON template used as part of the calculation.')

            if self.requestType == 'points' or self.requestType == 'multisite':
                if self.requestType == 'points':
                    requiredCsvHeaders = self.CSV_REQUIRED_HEADERS_POINTS
                elif self.requestType == 'multisite':
                    requiredCsvHeaders = self.CSV_REQUIRED_HEADERS_MULTISITE

                self.__parser.add_argument('-i', '--input-csv', dest = 'input_csv', required = True, help = 'Absolute path to input CSV of points to be used in your request. The CSV header row must be included with the keys of: %s' % requiredCsvHeaders)
            else:
                self.__parser.add_argument('-i', '--input-csv', dest = 'input_csv', help = 'Absolute path to input CSV, used in combination with --input-template to customise your template to a specific usecase. The CSV header row must be included. Header row values must be defined in dot notation format of the template key that they are to override in the template, for example transmitter latitude will be named as "transmitter.lat".')

        if self.requestType in ['interference', 'mesh', 'network']:
            self.__parser.add_argument('-nn', '--network-name', dest = 'network_name', required = True, help = 'The name of the network which you wish to run the analysis on.')

        # Network only has specific requirements
        if self.requestType == 'network':
            self.__parser.add_argument('-lat', '--latitude', dest = 'latitude', required = True, help = 'The latitude of the receiver in decimal degrees.')
            self.__parser.add_argument('-lon', '--longitude', dest = 'longitude', required = True, help = 'The longitude of the receiver in decimal degrees.')
            self.__parser.add_argument('-alt', '--altitude', dest = 'altitude', required = True, help = 'The altitude of the receiver in meters.')

        rawOutputPath = str(self.calledFromPath).rstrip('/').rstrip('\\')
        outputPath = os.path.join(rawOutputPath, 'output')

        self.__parser.add_argument('-k', '--api-key', dest = 'api_key', required = True, help = 'Your API key to the CloudRF API service.')
        self.__parser.add_argument('-u', '--base-url', dest = 'base_url', default = 'https://api.cloudrf.com/', help = 'The base URL for the CloudRF API service.')
        self.__parser.add_argument('--no-strict-ssl', dest = 'strict_ssl', action="store_false", default = True, help = 'Do not verify the SSL certificate to the CloudRF API service.')
        self.__parser.add_argument('-srq', '--save-raw-request', dest = 'save_raw_request', default = False, action = 'store_true', help = 'Save the raw request made to the CloudRF API service. This is saved to the --output-directory value.')
        self.__parser.add_argument('-r', '--save-raw-response', dest = 'save_raw_response', default = False, action = 'store_true', help = 'Save the raw response from the CloudRF API service. This is saved to the --output-directory value.')
        self.__parser.add_argument('-o', '--output-directory', dest = 'output_directory', default = outputPath, help = 'Absolute directory path of where outputs are saved.')

        outputFileChoices = ['all'] + self.allowedOutputTypes if len(self.allowedOutputTypes) > 1 else self.allowedOutputTypes
        self.__parser.add_argument('-s', '--output-file-type', dest = 'output_file_type', choices = outputFileChoices, help = 'Type of file to be downloaded.', default = self.allowedOutputTypes[0])
        self.__parser.add_argument('-v', '--verbose', action="store_true", default = False, help = 'Output more information on screen. This is often useful when debugging.')
        self.__parser.add_argument('-w', '--wait', dest = 'wait', default = 3, help = 'Time in seconds to wait before running the next calculation.')
        
        self.__arguments = self.__parser.parse_args()

    def __calculate(self, jsonData):
        now = datetime.datetime.now()

        calculationName = self.requestType
        if isinstance(jsonData, dict) and "network" in jsonData and "site" in jsonData:
            calculationName = jsonData["network"] + "_" + jsonData["site"]
        elif self.requestType in ['interference', 'mesh', 'network']:
            calculationName = self.__arguments.network_name

        requestName = now.strftime('%Y-%m-%d_%H%M%S_' + calculationName) 
        rawSaveBasePath = str(self.__arguments.output_directory).rstrip('/').rstrip('\\')
        saveBasePath = os.path.join(rawSaveBasePath, requestName)

        self.__verboseLog('Waiting %d seconds...' % (int(self.__arguments.wait)))
        time.sleep(int(self.__arguments.wait))
        self.__verboseLog('Running %s calculation: %s' % (self.requestType, requestName))

        try:
            if jsonData:
                fixedJsonData = self.__fixPotentiallyBrokenRequestJson(jsonData)

                # If we have JSON data then we can pass the JSON straight through
                self.__verboseLog('Request JSON:')
                self.__verboseLog(fixedJsonData)

                response = requests.post(
                    url = str(self.__arguments.base_url).rstrip('/') + '/' + self.requestType,
                    headers = {
                        'key': self.__arguments.api_key
                    },
                    json = fixedJsonData,
                    verify = self.__arguments.strict_ssl
                )

                if self.__arguments.save_raw_request:
                    saveJsonRequestPath = saveBasePath + '.request.json'
                    with open(saveJsonRequestPath, 'w') as rawRequestFile:
                        rawRequestFile.write(json.dumps(fixedJsonData, indent = 4))
                    print('Raw request saved at %s' % saveJsonRequestPath)
            elif self.requestType in ['interference', 'network', 'mesh']:
                # Other requests use params rather than a JSON body
                requestParams = {}

                if self.requestType == 'network':
                    requestParams['net'] = self.__arguments.network_name
                    requestParams['lat'] = self.__arguments.latitude
                    requestParams['lon'] = self.__arguments.longitude
                    requestParams['rxh'] = self.__arguments.altitude
                elif self.requestType in ['interference', 'mesh']:
                    requestParams['network'] = self.__arguments.network_name

                response = requests.post(
                    url = str(self.__arguments.base_url).rstrip('/') + '/' + self.requestType,
                    headers = {
                        'key': self.__arguments.api_key
                    },
                    params = requestParams,
                    verify = self.__arguments.strict_ssl
                )

            if self.__arguments.save_raw_request:
                saveRequestPath = saveBasePath + '.request.txt'
                with open(saveRequestPath, 'w') as rawRequestFile:
                    rawRequestFile.write(response.request.url)
                print('Raw request saved at %s' % saveRequestPath)

            self.__checkHttpResponse(httpStatusCode = response.status_code, httpRawResponse = response.text)
            self.__saveOutputFileTypes(httpRawResponse = response.text, saveBasePath = saveBasePath)

            self.__verboseLog('Raw response:')
            self.__verboseLog(response.text)

            if self.__arguments.save_raw_response:
                saveJsonResponsePath = saveBasePath + '.response.json'
                with open(saveJsonResponsePath, 'w') as rawResponseFile:
                    rawResponseFile.write(response.text)

                print('Raw response saved at %s' % saveJsonResponsePath)

        except requests.exceptions.SSLError:
            sys.exit('SSL error occurred. This is common with self-signed certificates. You can try disabling SSL verification with --no-strict-ssl.')
        except requests.exceptions.ConnectionError:
            sys.exit('Unable to connect to CloudRF API service at %s. Please check your network settings, or if you are trying to use a custom endpoint please use the --base-url flag.' % self.__arguments.base_url)

    def __checkHttpResponse(self, httpStatusCode, httpRawResponse):
        if httpStatusCode != 200:
            print('An HTTP %d error occurred with your request. Full response from the CloudRF API is listed below.' % httpStatusCode)
            print(httpRawResponse)

            if httpStatusCode == 400:
                sys.exit('HTTP 400 refers to a bad request. You likely have bad values in your input JSON/CSV. For good examples please consult %s' % self.URL_GITHUB)
            elif httpStatusCode == 401:
                sys.exit('HTTP 401 refers to an unauthorised request. Your API key is likely incorrect.')
            elif httpStatusCode == 403:
                sys.exit('HTTP 403 refers to a forbidden request. Your API key appears to be correct but you do not appear to have permission to make your request.')
            elif httpStatusCode == 500:
                sys.exit('HTTP 500 refers to an issue with the server. A problem with the CloudRF API service appears to have occurred.')
            else:
                sys.exit('An unknown HTTP error has occured. Please consult the above response from the CloudRF API, or %s' % self.URL_GITHUB)

    def __customiseJsonFromCsvRow(self, templateJson, csvRowDictionary):
        for key, value in csvRowDictionary.items():
            # We are using dot notation so split out on this
            parts = str(key).split('.')

            # Should be a maxium of 2 parts so we can just be explicit here and update the template JSON
            if len(parts) == 2:
                templateJson[parts[0]][parts[1]] = value
            elif len(parts) == 1:
                templateJson[key] = value
            else:
                sys.exit('Maximum depth of dot notation 2. Please check your input CSV.')
        
        return templateJson
    
    def __customiseJsonMultisiteFromCsv(self, templateJson, csvListOfDictionaries):
        # This is only for multisite requests
        if self.requestType != 'multisite':
            sys.exit('Unable to customise JSON points when request type is not "multisite".')

        # All of the points are in an array/list, initialise it
        templateJson['transmitters'] = []

        for row in csvListOfDictionaries:
            transmitter = {
                'lat': row['lat'],
                'lon': row['lon'],
                'alt': row['alt'],
                'frq': row['frq'],
                'txw': row['txw'],
                'bwi': row['bwi'],
                'antenna': {
                    'txg': row['antenna.txg'],
                    'txl': row['antenna.txl'],
                    'ant': row['antenna.ant'],
                    'azi': row['antenna.azi'],
                    'tlt': row['antenna.tlt'],
                    'hbw': row['antenna.hbw'],
                    'vbw': row['antenna.vbw'],
                    'fbr': row['antenna.fbr'],
                    'pol': row['antenna.pol']
                }
            }
            templateJson['transmitters'].append(transmitter)

        return templateJson

    def __customiseJsonPointsFromCsv(self, templateJson, csvListOfDictionaries):
        # This is only for points requests
        if self.requestType != 'points':
            sys.exit('Unable to customise JSON points when request type is not "points".')

        # The transmitter location should be the very first point
        templateJson['transmitter']['lat'] = csvListOfDictionaries[0]['lat']
        templateJson['transmitter']['lon'] = csvListOfDictionaries[0]['lon']

        # All of the points are in an array/list, initialise it
        templateJson['points'] = []

        for row in csvListOfDictionaries:
            point = {
                'lat': row['lat'],
                'lon': row['lon'],
                'alt': row['alt']
            }
            templateJson['points'].append(point)

        return templateJson
    
    def __fixPotentiallyBrokenRequestJson(self, jsonData):
        if self.requestType == 'area':
            if jsonData['receiver']['lat'] != 0:
                print('Your template has a value in the receiver.lat key which will prevent an area calculation. Setting a safe default.')
                jsonData['receiver']['lat'] = 0

            if jsonData['receiver']['lon'] != 0:
                print('Your template has a value in the receiver.lon key which will prevent an area calculation. Setting a safe default.')
                jsonData['receiver']['lon'] = 0

        return jsonData
    
    def __retrieveOutputFile(self, httpRawResponse, fileType, saveBasePath):
        self.__verboseLog('Retrieving output file: %s' % fileType)

        responseJson = json.loads(httpRawResponse)

        if self.requestType == 'area':
            if fileType == 'png':
                # PNG links exist already in the response JSON so we can just grab them from there
                #pngPath3857 = saveBasePath + '.3857.png'
                #self.__streamUrlToFile(responseJson['PNG_Mercator'], pngPath3857)
                #self.__verboseLog('3857 projected PNG saved to %s' % pngPath3857)
                pngPath4326 = saveBasePath + '.4326.png'
                self.__streamUrlToFile(responseJson['PNG_WGS84'], pngPath4326)
                self.__verboseLog('4326 projected PNG saved to %s' % pngPath4326)
            else:
                # Anything else we just pull out of the archive
                savePath = saveBasePath + '.' + fileType
                self.__streamUrlToFile(
                    requestUrl = str(self.__arguments.base_url).rstrip('/') + '/archive/' + responseJson['sid'] + '/' + fileType,
                    savePath = savePath
                )
                self.__verboseLog('%s file saved to %s' % (fileType, savePath))
        
        elif self.requestType == 'interference':
            if fileType == 'png':
                # PNG links exist already in the response JSON so we can just grab them from there
                pngPath3857 = saveBasePath + '.3857.png'
                self.__streamUrlToFile(responseJson['png_mercator'], pngPath3857)
                self.__verboseLog('3857 projected PNG saved to %s' % pngPath3857)
                pngPath4326 = saveBasePath + '.4326.png'
                self.__streamUrlToFile(responseJson['png_wgs84'], pngPath4326)
                self.__verboseLog('4326 projected PNG saved to %s' % pngPath4326)
        
        elif self.requestType == 'mesh':
            if fileType == 'png':
                # PNG links exist already in the response JSON so we can just grab them from there
                pngPath3857 = saveBasePath + '.3857.png'
                self.__streamUrlToFile(responseJson['png_mercator'], pngPath3857)
                self.__verboseLog('3857 projected PNG saved to %s' % pngPath3857)
                pngPath4326 = saveBasePath + '.4326.png'
                self.__streamUrlToFile(responseJson['png_wgs84'], pngPath4326)
                self.__verboseLog('4326 projected PNG saved to %s' % pngPath4326)
            if fileType == 'kmz':
                kmzPath = saveBasePath + '.kmz'
                self.__streamUrlToFile(responseJson['kmz'], kmzPath)
                self.__verboseLog('Mesh KMZ saved to %s' % kmzPath)
        
        elif self.requestType == 'multisite':
            if fileType == 'png':
                # PNG links exist already in the response JSON so we can just grab them from there
                pngPath4326 = saveBasePath + '.4326.png'
                self.__streamUrlToFile(responseJson['PNG_WGS84'], pngPath4326)
                self.__verboseLog('4326 projected PNG saved to %s' % pngPath4326)
        
        elif self.requestType == 'network':
            # Network returns an array of responses
            if fileType == 'png':
                count = 1
                for row in responseJson:
                    pngPath = saveBasePath + '_' + str(count) + '.png'
                    self.__streamUrlToFile(row['Chart image'], pngPath)
                    self.__verboseLog('Path profile PNG saved to %s' % pngPath)
                    count += 1
            if fileType == 'txt':
                txtPath = saveBasePath + '.txt'
                count = 1
                with open(txtPath, 'a') as txtOutputFile:
                    for row in responseJson:
                        txtOutputFile.write('Site %d (%s, %s): %s dBm\n' % (
                                                                        count, 
                                                                        row['Transmitters'][0]['Latitude'],
                                                                        row['Transmitters'][0]['Longitude'],
                                                                        row['Transmitters'][0]['Signal power at receiver dBm'],
                                                                      )
                                                                    )
                        count += 1
                txtOutputFile.close()
                self.__verboseLog('TXT saved to %s' % txtPath)

        elif self.requestType == 'path':
            if fileType == 'png':
                pngPath = saveBasePath + '.png'
                self.__streamUrlToFile(responseJson['Chart image'], pngPath)
                self.__verboseLog('Path profile PNG saved to %s' % pngPath)
            if fileType == 'kmz':
                kmzPath = saveBasePath + '.kmz'
                self.__streamUrlToFile(responseJson['kmz'], kmzPath)
                self.__verboseLog('Path profile KMZ saved to %s' % kmzPath)
        
        elif self.requestType == 'points':
            if fileType == 'kmz':
                kmzPath = saveBasePath + '.kmz'
                self.__streamUrlToFile(responseJson['kmz'], kmzPath)
                self.__verboseLog('Points KMZ saved to %s' % kmzPath)
        
        else:
            sys.exit('Unable to retrieve output file of unsupported request type.')
    
    def __saveOutputFileTypes(self, httpRawResponse, saveBasePath):
        if self.__arguments.output_file_type == 'all':
            # Get all of the available file types for this request
            for type in self.allowedOutputTypes:
                self.__retrieveOutputFile(httpRawResponse = httpRawResponse, fileType = type, saveBasePath = saveBasePath)
        else:
            self.__retrieveOutputFile(httpRawResponse = httpRawResponse, fileType = self.__arguments.output_file_type, saveBasePath = saveBasePath)

    def __streamUrlToFile(self, requestUrl, savePath):
        response = requests.get(requestUrl, stream = True, verify = self.__arguments.strict_ssl)

        # If we are retrieving a stream
        if response.headers.get('Content-Disposition'):
            # The file extension may be different on the server side, so we should use that by default
            serverFilename = re.findall("filename=(.+)", response.headers.get('Content-Disposition'))[0]
            serverFilename = serverFilename.replace('"', '')
            serverFileExtension = serverFilename.split('.', 1)[1]

            savePathBaseFilename = savePath.split('.', 1)[0]
            savePath = savePathBaseFilename + '.' + serverFileExtension

        with open(savePath, 'wb') as outputFile:
            outputFile.write(response.content)
        del response

    def __validateApiKey(self):
        parts = str(self.__arguments.api_key).split('-')
        externalPrompt = 'Please make sure that you are using the correct key from https://cloudrf.com/my-account'

        if len(parts) != 2:
            sys.exit('Your API key appears to be in the incorrect format. %s' % externalPrompt)

        if not parts[0].isnumeric():
            sys.exit('Your API key UID component (part before "-") appears to be incorrect. %s' % externalPrompt)

        if len(parts[1]) != 40:
            sys.exit('Your API key token component (part after "-") appears to be incorrect. %s' % externalPrompt)

    def __validateCsv(self):
        if self.__arguments.input_csv:
            try:
                returnList = []

                with open(self.__arguments.input_csv, 'r') as csvInputFile:
                    reader = csv.DictReader(csvInputFile)

                    for row in reader:
                        for key, value in row.items():
                            if not key or not value:
                                raise AttributeError('There is an empty header or value in the input CSV file (%s)' % self.__arguments.input_csv)
                            
                            # Some requests doesn't customise the JSON template, instead the CSV are a list of points/sites which are passed through to the request
                            if self.requestType == 'points' or self.requestType == 'multisite':
                                submittedHeaders = list(row.keys())
                                
                                if self.requestType == 'points':
                                    requiredHeaders = self.CSV_REQUIRED_HEADERS_POINTS
                                elif self.requestType == 'multisite':
                                    requiredHeaders = self.CSV_REQUIRED_HEADERS_MULTISITE
                                
                                if set(requiredHeaders) != set(submittedHeaders):
                                    raise AttributeError('You have a bad CSV header. You are missing at least one of the following header keys from your CSV: %s' % requiredHeaders)

                            # We are using dot notation, a header should never be more than 2 deep
                            parts = str(key).split('.')

                            if len(parts) > 2:
                                raise AttributeError('Maximum depth of dot notation is 2. You have a value with a depth of %d in the input CSV file (%s)' % (len(parts), self.__arguments.input_csv))

                        returnList.append(row)
                        
                return returnList
            except PermissionError:
                sys.exit('Permission error when trying to read input CSV file (%s)' % self.__arguments.input_csv)
            except AttributeError as e:
                sys.exit(e)
            except:
                sys.exit('An unknown error occurred when checking input CSV file (%s)' % (self.__arguments.input_csv))

    def __validateFileAndDirectoryPermissions(self):
        if hasattr(self.__arguments, 'input_template') and self.__arguments.input_template:
            if not os.path.exists(self.__arguments.input_template):
                sys.exit('Your input template JSON file (%s) could not be found. Please check your path. Please note that this should be in absolute path format.' % self.__arguments.input_template)
            else:
                self.__verboseLog('Input template JSON file (%s) found with file permissions: %s' % (self.__arguments.input_template, oct(stat.S_IMODE(os.lstat(self.__arguments.input_template).st_mode))))

        if hasattr(self.__arguments, 'input_csv'):
            if self.__arguments.input_csv:
                if not os.path.exists(self.__arguments.input_csv):
                    sys.exit('Your input CSV file (%s) could not be found. Please check your path. Please note that this should be in absolute path format.' % self.__arguments.input_csv)
                else:
                    self.__verboseLog('Input CSV file (%s) found with file permissions: %s' % (self.__arguments.input_csv, oct(stat.S_IMODE(os.lstat(self.__arguments.input_csv).st_mode))))
            else:
                print('Input CSV has not been specified. Default values in input template JSON file will be used.')

        if not os.path.exists(self.__arguments.output_directory):
            self.__verboseLog('Output directory (%s) does not exist, attempting to create.' % self.__arguments.output_directory)
            os.makedirs(self.__arguments.output_directory)
            self.__verboseLog('Output directory (%s) created successfully.' % self.__arguments.output_directory)

        self.__verboseLog('Output directory (%s) exists with permissions: %s' % (self.__arguments.output_directory, oct(stat.S_IMODE(os.lstat(self.__arguments.output_directory).st_mode))))

        try:
            # Check if any file can be written to the output directory
            rawTestFilePath = str(self.__arguments.output_directory).rstrip('/').rstrip('\\')
            testFilePath = os.path.join(rawTestFilePath, 'tmp')
            open(testFilePath, 'a')
            os.remove(testFilePath)
        except PermissionError:
            sys.exit('Unable to create files in output directory (%s)' % self.__arguments.output_directory)

    def __validateJsonTemplate(self):
        try:
            with open(self.__arguments.input_template, 'r') as jsonTemplateFile:
                return json.load(jsonTemplateFile)
        except PermissionError:
            sys.exit('Permission error when trying to read input template JSON file (%s)' % self.__arguments.input_template)
        except json.decoder.JSONDecodeError:
            sys.exit('Input template JSON file (%s) is not a valid JSON file.' % self.__arguments.input_template)
        except:
            sys.exit('An unknown error occurred when checking input template JSON file (%s)' % (self.__arguments.input_template))

    def __validateRequestType(self):
        if self.requestType and self.requestType in self.ALLOWED_REQUEST_TYPES:
            self.__verboseLog('Valid request type of %s being used.' % self.requestType)

            if self.requestType == 'area':
                self.allowedOutputTypes = ['kmz', 'png', 'shp', 'tiff']
                self.description = '''
                    CloudRF Area API

                    Area coverage performs a circular sweep around a transmitter out to a user defined radius.
                    It factors in system parameters, antenna patterns, environmental characteristics and terrain data to show a heatmap in customisable colours and units.
                '''
            elif self.requestType == 'interference':
                self.allowedOutputTypes = ['png']
                self.description = '''
                    CloudRF Interference API

                    Interference will use a common network name to merge and analyse sites within that network to show the best site at a given location.
                    In order to properly use the interference API you area required to have area calculations already completed which have a common network name.
                '''
            elif self.requestType == 'mesh':
                self.allowedOutputTypes = ['kmz', 'png']
                self.description = '''
                    CloudRF Mesh API

                    Mesh merges multiple area calculations into a single super layer based on a common network name.
                    In order to properly use the mesh API you area required to have area calculations already completed which have a common network name.
                '''
            elif self.requestType == 'multisite':
                self.allowedOutputTypes = ['png']
                self.description = '''
                    CloudRF Multisite API

                    Multisite creates multiple area multipoint calculations in a single request.
                    It uses multiple transmitter locations to produce one response which factors in each transmitter.
                '''
            elif self.requestType == 'network':
                self.allowedOutputTypes = ['png', 'txt']
                self.description = '''
                    CloudRF Network API

                    Network allows to find the best site for a given location based upon a common network name.
                    In order to properly use the network API you area required to have area calculations already completed which have a common network name.
                '''
            elif self.requestType == 'path':
                self.allowedOutputTypes = ['kmz', 'png']
                self.description = '''
                    CloudRF Path API

                    Path profile studies the link from one site to another in a direct line.
                    It factors in system parameters, antenna patterns, environmental characteristics and terrain data to produce a JSON report containing enough values to incorporate into your analysis or create a chart from.
                '''
            elif self.requestType == 'points':
                self.allowedOutputTypes = ['kmz']
                self.description = '''
                    CloudRF Points API

                    Points calculates multiple point-to-point links in one call.
                    It uses points to test many transmitters to one receiver and is commonly used for route analysis or calculating signal at known locations.
                '''

        else:
            sys.exit('Unsupported request type of "%s" being used. Allowed request types are: %s' % (self.requestType, self.ALLOWED_REQUEST_TYPES))

    def __verboseLog(self, message):
        try:
            if self.__arguments.verbose:
                print(message)
        except:
            pass

if __name__ == '__main__':
    try:
        CloudRF(
            REQUEST_TYPE = sys.argv[1]
        )
    except IndexError:
        sys.exit('This script should be executed by specifying the request type you wish to run. Please pass in one of the following arguments after the call of this script: %s' % CloudRF.ALLOWED_REQUEST_TYPES)
