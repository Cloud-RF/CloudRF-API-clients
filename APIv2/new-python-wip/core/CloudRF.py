#!/usr/bin/env python3

# This file is not meant to be called directly. It should be imported.
if __name__ != '__main__':
    import argparse
    import sys
    import textwrap
    import urllib3

    from .ArgparseCustomFormatter import ArgparseCustomFormatter
    from .PythonValidator import PythonValidator

class CloudRF:
    allowedOutputTypes = []
    description = 'CloudRF'
    calledFromPath = None

    URL_GITHUB = 'https://github.com/Cloud-RF/CloudRF-API-clients'

    def __init__(self, ALLOWED_OUTPUT_TYPES, DESCRIPTION, CURRENT_PATH):
        PythonValidator.version()

        self.allowedOutputTypes = ALLOWED_OUTPUT_TYPES
        self.description = DESCRIPTION
        # Where was the script called from?
        self.calledFromPath = CURRENT_PATH

        self.__argparseInitialiser()

        # If we are in verbose mode then just output everything
        if self.__arguments.verbose:
            self.__parser.print_help()
            print()

        if not self.__arguments.strict_ssl:
            self.__verboseLog('Strict SSL disabled.')
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        self.__validateApiKey()

    def __argparseInitialiser(self):
        self.__parser = argparse.ArgumentParser(
            description = textwrap.dedent(self.description),
            formatter_class = ArgparseCustomFormatter,
            epilog = 'For more details about this script please consult the GitHub documentation at %s.' % self.URL_GITHUB
        )

        outputPath = str(self.calledFromPath).rstrip('/') + '/output'

        self.__parser.add_argument('-t', '--input-template', dest = 'input_template', required = True, help = 'Absolute path to input JSON template used as part of the calculation.')
        self.__parser.add_argument('-i', '--input-csv', dest = 'input_csv', help = 'Absolute path to input CSV, used in combination with --input-template to customise your template to a specific usecase. The CSV header row must be included. Header row values must be defined in dot notation format of the template key that they are to override in the template, for example transmitter latitude will be named as "transmitter.lat".')
        self.__parser.add_argument('-k', '--api-key', dest = 'api_key', required = True, help = 'Your API key to the CloudRF API service.')
        self.__parser.add_argument('-u', '--base-url', dest = 'base_url', default = 'https://api.cloudrf.com/', help = 'The base URL for the CloudRF API service.')
        self.__parser.add_argument('--no-strict-ssl', dest = 'strict_ssl', action="store_false", default = True, help = 'Do not verify the SSL certificate to the CloudRF API service.')
        self.__parser.add_argument('-r', '--save-raw-response', dest = 'save_raw_response', default = False, action = 'store_true', help = 'Save the raw response from the CloudRF API service. This is saved to the --output-directory value.')
        self.__parser.add_argument('-o', '--output-directory', dest = 'output_directory', default = outputPath, help = 'Absolute directory path of where outputs are saved.')
        self.__parser.add_argument('-s', '--output-file-type', dest = 'output_file_type', choices = ['all'] + self.allowedOutputTypes, help = 'Type of file to be downloaded.', default = 'kmz')
        self.__parser.add_argument('-v', '--verbose', action="store_true", default = False, help = 'Output more information on screen. This is often useful when debugging.')

        self.__arguments = self.__parser.parse_args()

    def __validateApiKey(self):
        parts = str(self.__arguments.api_key).split('-')
        externalPrompt = 'Please make sure that you are using the correct key from https://cloudrf.com/my-account'

        if len(parts) != 2:
            sys.exit('Your API key appears to be in the incorrect format. %s' % externalPrompt)

        if not parts[0].isnumeric():
            sys.exit('Your API key UID component (part before "-") appears to be incorrect. %s' % externalPrompt)

        if len(parts[1]) != 40:
            sys.exit('Your API key token component (part after "-") appears to be incorrect. %s' % externalPrompt)

    def __verboseLog(self, message):
        if self.__arguments.verbose:
            print(message)

if __name__ == '__main__':
    print('This is a core file and should not be executed natively. Please see %s for more details.' % CloudRF.URL_GITHUB)