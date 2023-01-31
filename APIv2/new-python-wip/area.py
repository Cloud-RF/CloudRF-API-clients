#!/usr/bin/env python3
import argparse
import pathlib
import sys
import textwrap

class PythonValidator:
    def version():
        requiredMajor = 3
        minimumMinor = 9

        if sys.version_info.major != requiredMajor or sys.version_info.minor < minimumMinor:
            sys.exit('Your Python version (%s) does not meet the minimum required version of %s' % (
                    str(sys.version_info.major) + '.' + str(sys.version_info.minor), 
                    str(requiredMajor) + '.' + str(minimumMinor)
                )
            )

# We combine multiple formatter classes into one, this allows us to show default values and have nice styling with --help
class ArgparseCustomFormatter(argparse.RawDescriptionHelpFormatter, argparse.ArgumentDefaultsHelpFormatter):
    pass

if __name__ == '__main__':
    PythonValidator.version()

    parser = argparse.ArgumentParser(
        description = textwrap.dedent(f'''
            CloudRF Area API

            Area coverage performs a circular sweep around a transmitter out to a user defined radius.
            It factors in system parameters, antenna patterns, environmental characteristics and terrain data to show a heatmap in customisable colours and units.
        '''),
        formatter_class = ArgparseCustomFormatter,
        epilog = 'For more details about this script please consult the GitHub documentation at https://github.com/Cloud-RF/CloudRF-API-clients'
    )

    currentScriptPath = pathlib.Path(__file__).parent.resolve()

    parser.add_argument('-t', '--input-template', dest = 'input_template', required = True, help = 'Path to input JSON template used as part of the calculation.')
    parser.add_argument('-i', '--input-csv', dest = 'input_csv', help = 'Path to input CSV, used in combination with --input-template to customise your template to a specific usecase.')
    parser.add_argument('-k', '--api-key', dest = 'api_key', required = True, help = 'Your API key to the CloudRF API service.')
    parser.add_argument('-u', '--base-url', dest = 'base_url', default = 'https://api.cloudrf.com/', help = 'The base URL for the CloudRF API service.')
    parser.add_argument('--no-strict-ssl', dest = 'strict_ssl', action="store_false", default = True, help = 'Do not verify the SSL certificate to the CloudRF API service.')
    parser.add_argument('-o', '--output-directory', dest = 'output_directory', default = currentScriptPath, help = 'Director where outputs are saved.')
    parser.add_argument('-v', '--verbose', action="store_true", default = False, help = 'Output more information on screen. This is often useful when debugging.')

    parser.print_help()

    arguments = parser.parse_args()
    