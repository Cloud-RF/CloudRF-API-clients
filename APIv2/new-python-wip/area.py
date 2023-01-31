#!/usr/bin/env python3
import argparse
import json
import os
import pathlib
import stat
import sys
import textwrap

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

def verboseLog(message):
    if arguments.verbose:
        print(message)

# We combine multiple formatter classes into one, this allows us to show default values and have nice styling with --help
class ArgparseCustomFormatter(argparse.RawDescriptionHelpFormatter, argparse.ArgumentDefaultsHelpFormatter):
    pass

if __name__ == '__main__':
    PythonValidator.version()

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
    parser.add_argument('-o', '--output-directory', dest = 'output_directory', default = currentScriptPath, help = 'Director where outputs are saved.')
    parser.add_argument('-v', '--verbose', action="store_true", default = False, help = 'Output more information on screen. This is often useful when debugging.')

    arguments = parser.parse_args()

    if arguments.verbose:
        parser.print_help()
        print()

    checkPermissions()
    jsonTemplate = checkValidJsonTemplate()

