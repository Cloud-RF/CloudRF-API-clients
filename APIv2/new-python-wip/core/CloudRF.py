#!/usr/bin/env python3

# This file is not meant to be called directly. It should be imported.
if __name__ != '__main__':
    import argparse
    import csv
    import datetime
    import json
    import os
    import requests
    import shutil
    import stat
    import sys
    import textwrap
    import urllib3

    from .ArgparseCustomFormatter import ArgparseCustomFormatter
    from .PythonValidator import PythonValidator

class CloudRF:
    allowedOutputTypes = []
    calledFromPath = None
    description = 'CloudRF'
    requestType = None

    CSV_REQUIRED_HEADERS_MULTISITE = ['lat', 'lon', 'alt', 'frq', 'txw', 'bwi', 'antenna.txg', 'antenna.txl', 'antenna.ant', 'antenna.azi', 'antenna.tlt', 'antenna.hbw', 'antenna.vbw', 'antenna.fbr', 'antenna.pol']
    CSV_REQUIRED_HEADERS_POINTS = ['lat', 'lon', 'alt']

    URL_GITHUB = 'https://github.com/Cloud-RF/CloudRF-API-clients'

    def __init__(self, REQUEST_TYPE, ALLOWED_OUTPUT_TYPES, DESCRIPTION, CURRENT_PATH):
        self.allowedOutputTypes = ALLOWED_OUTPUT_TYPES
        # Where was the script called from?
        self.calledFromPath = CURRENT_PATH
        self.description = DESCRIPTION
        self.requestType = REQUEST_TYPE

        PythonValidator.version()
        self.__validateRequestType()
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

        sys.exit('Process completed. Please check your output folder (%s)' % self.__arguments.output_directory)

    def __argparseInitialiser(self):
        self.__parser = argparse.ArgumentParser(
            description = textwrap.dedent(self.description),
            formatter_class = ArgparseCustomFormatter,
            epilog = 'For more details about this script please consult the GitHub documentation at %s.' % self.URL_GITHUB
        )

        outputPath = str(self.calledFromPath).rstrip('/') + '/output'

        self.__parser.add_argument('-t', '--input-template', dest = 'input_template', required = True, help = 'Absolute path to input JSON template used as part of the calculation.')

        if self.requestType == 'points' or self.requestType == 'multisite':
            if self.requestType == 'points':
                requiredCsvHeaders = self.CSV_REQUIRED_HEADERS_POINTS
            elif self.requestType == 'multisite':
                requiredCsvHeaders = self.CSV_REQUIRED_HEADERS_MULTISITE

            self.__parser.add_argument('-i', '--input-csv', dest = 'input_csv', required = True, help = 'Absolute path to input CSV of points to be used in your request. The CSV header row must be included with the keys of: %s' % requiredCsvHeaders)
        else:
            self.__parser.add_argument('-i', '--input-csv', dest = 'input_csv', help = 'Absolute path to input CSV, used in combination with --input-template to customise your template to a specific usecase. The CSV header row must be included. Header row values must be defined in dot notation format of the template key that they are to override in the template, for example transmitter latitude will be named as "transmitter.lat".')

        self.__parser.add_argument('-k', '--api-key', dest = 'api_key', required = True, help = 'Your API key to the CloudRF API service.')
        self.__parser.add_argument('-u', '--base-url', dest = 'base_url', default = 'https://api.cloudrf.com/', help = 'The base URL for the CloudRF API service.')
        self.__parser.add_argument('--no-strict-ssl', dest = 'strict_ssl', action="store_false", default = True, help = 'Do not verify the SSL certificate to the CloudRF API service.')
        self.__parser.add_argument('-srq', '--save-raw-request', dest = 'save_raw_request', default = False, action = 'store_true', help = 'Save the raw request made to the CloudRF API service. This is saved to the --output-directory value.')
        self.__parser.add_argument('-r', '--save-raw-response', dest = 'save_raw_response', default = False, action = 'store_true', help = 'Save the raw response from the CloudRF API service. This is saved to the --output-directory value.')
        self.__parser.add_argument('-o', '--output-directory', dest = 'output_directory', default = outputPath, help = 'Absolute directory path of where outputs are saved.')

        outputFileChoices = ['all'] + self.allowedOutputTypes if len(self.allowedOutputTypes) > 1 else self.allowedOutputTypes
        self.__parser.add_argument('-s', '--output-file-type', dest = 'output_file_type', choices = outputFileChoices, help = 'Type of file to be downloaded.', default = self.allowedOutputTypes[0])
        self.__parser.add_argument('-v', '--verbose', action="store_true", default = False, help = 'Output more information on screen. This is often useful when debugging.')

        self.__arguments = self.__parser.parse_args()

    def __calculate(self, jsonData):
        now = datetime.datetime.now()
        requestName = now.strftime('%Y%m%d%H%M%S_' + now.strftime('%f')[:3])
        saveBasePath = str(self.__arguments.output_directory).rstrip('/') + '/' + requestName

        fixedJsonData = self.__fixPotentiallyBrokenRequestJson(jsonData)

        self.__verboseLog('Running %s calculation: %s' % (self.requestType, requestName))

        try:
            if self.__arguments.save_raw_request:
                saveJsonRequestPath = saveBasePath + '.request.json'
                with open(saveJsonRequestPath, 'w') as rawRequestFile:
                    rawRequestFile.write(json.dumps(fixedJsonData, indent = 4))
                print('Raw request saved at %s' % saveJsonRequestPath)

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
                pngPath3857 = saveBasePath + '.3857.png'
                self.__streamUrlToFile(responseJson['PNG_Mercator'], pngPath3857)
                self.__verboseLog('3857 projected PNG saved to %s' % pngPath3857)
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
        elif self.requestType == 'multisite':
            if fileType == 'png':
                # PNG links exist already in the response JSON so we can just grab them from there
                pngPath4326 = saveBasePath + '.4326.png'
                self.__streamUrlToFile(responseJson['PNG_WGS84'], pngPath4326)
                self.__verboseLog('4326 projected PNG saved to %s' % pngPath4326)
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
        with open(savePath, 'wb') as outputFile:
            shutil.copyfileobj(response.raw, outputFile)
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
        if not os.path.exists(self.__arguments.input_template):
            sys.exit('Your input template JSON file (%s) could not be found. Please check your path. Please note that this should be in absolute path format.' % self.__arguments.input_template)
        else:
            self.__verboseLog('Input template JSON file (%s) found with file permissions: %s' % (self.__arguments.input_template, oct(stat.S_IMODE(os.lstat(self.__arguments.input_template).st_mode))))

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
            testFilePath = str(self.__arguments.output_directory).rstrip('/') + '/tmp'
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
        allowedRequestTypes = ['area', 'path', 'points', 'multisite']

        if self.requestType and self.requestType in allowedRequestTypes:
            self.__verboseLog('Valid request type of %s being used.' % self.requestType)
        else:
            sys.exit('Unsupported request type of "%s" being used. Allowed request types are: %s' % (self.requestType, allowedRequestTypes))

    def __verboseLog(self, message):
        try:
            if self.__arguments.verbose:
                print(message)
        except:
            pass

if __name__ == '__main__':
    sys.exit('This is a core file and should not be executed directly. Please see %s for more details.' % CloudRF.URL_GITHUB)