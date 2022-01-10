"""Demonstrate Network CloudRF API."""
import argparse
import configparser
import csv
import os
import textwrap
from pathlib import Path
import pprint

from cloudrf import CloudRFAPI


class CloudRFNetwork(CloudRFAPI):
    """Network API class"""

    endpoint = '/network/'
    api_id = 'network'

    file_types = ['chart', 'kml']
    type_map = {'chart': 'Chart image', 'kml': 'Network KML'}

    def download(self, select=None):
        select = self.file_types if select is None else select

        for server in self.response:
            for dtype in select:
                if self.type_map[dtype] in server:
                    self.download_direct(server[self.type_map[dtype]])


class App:
    """Application class

    This class's base class is configured using a cloudrf.ini configuration file.
    At first run, a default configuration file will be created. Change all values as required.
    Alternatively, the CLOUDRF_UID and CLOUDRF_KEY environment variables may be used to override the file configuration.

    This behaviour may be changed by removing the AppAddOn base class
    """

    config_filename = 'cloudrf.ini'

    def __init__(self, args=None):

        print('CloudRF API demo')

        self.parse_args(args)
        print(f'Reading data from {self.args.data_files}')
        print(f'Will download {self.args.dl_types}')

        self.configure()

        if self.args.output_dir is not None:
            self.data_dir = self.args.output_dir

        if self.data_dir is None:
            self.data_dir = Path.cwd() / 'data'
        print(f'All files generated to {self.data_dir}')

    def parse_args(self, args):
        parser = argparse.ArgumentParser(description=textwrap.dedent(f'''
            CloudRF Network application

            Query your networks to find the best server for a customer.

            This demonstration program utilizes the CloudRF Network API to generate any
            of the possible file outputs offered by the API from {CloudRFNetwork.file_types}.
            The API arguments are sourced from csv file(s).
            please use -s all to generate ALL outputs available.

            Please refer to API Reference https://api.cloudrf.com/'''),
                                         formatter_class=argparse.RawDescriptionHelpFormatter)

        parser.add_argument('-i', dest='data_files', metavar='data_file', nargs='+', help='data input filename(csv)')
        parser.add_argument('-s', dest='dl_types', nargs='+',
                            choices=CloudRFNetwork.file_types + ['all'],
                            help='type of output file to be downloaded', default=['chart'])
        parser.add_argument('-o', dest='output_dir', metavar='output_dir',
                            help='output directory where files are downloaded')
        parser.add_argument('-r', dest='save_response', action="store_true", help='save response content (json/html)')
        parser.add_argument('-v', dest='verbose', action="store_true", help='Output more information on screen')

        # for unit testing it is useful to be able to pass arguments.
        if args is None:
            self.args = parser.parse_args()
        else:
            if isinstance(args, str):
                args = args.split(' ')
            self.args = parser.parse_args(args)

        # if all selected then we reset the list to all types.
        if 'all' in self.args.dl_types:
            self.args.dl_types = CloudRFNetwork.file_types

        self.save_response = self.args.save_response

    def configure(self):
        """Application configuration

        Adds functionality to load key from configuration or environment
        you may find simpler to use the following assignments instead
        self.key = "CHANGEME"
        """
        def str2bool(v):
            if isinstance(v, bool):
                return v
            if v.lower() in ('yes', 'true', 't', 'y', '1'):
                return True
            elif v.lower() in ('no', 'false', 'f', 'n', '0'):
                return False
            else:
                raise Exception(f'Boolean value expected in {v}.')

        self.key = os.environ['CLOUDRF_KEY'] if 'CLOUDRF_KEY' in os.environ else None
        self.strict_ssl = os.environ['CLOUDRF_STRICT_SSL'] if 'CLOUDRF_STRICT_SSL' in os.environ else None
        self.base_url = os.environ['CLOUDRF_BASE_URL'] if 'CLOUDRF_BASE_URL' in os.environ else None
        self.data_dir = os.environ['CLOUDRF_DATA_DIR'] if 'CLOUDRF_DATA_DIR' in os.environ else None

        # is any value is not None we read the config
        if not any([bool(self.key), bool(self.strict_ssl), bool(self.base_url)]):
            config = configparser.ConfigParser()

            # we read the configuration file if it exists
            if Path(self.config_filename).is_file():
                config.read(self.config_filename)

            # if user section does not exist we create it with default value
            if 'user' not in config.sections():
                config.add_section('user')
                config['user']['key'] = '101-IBIZA.DEMO.KEY'
                config.add_section('api')
                config['api']['strict_ssl'] = 'True'
                config['api']['base_url'] = 'https://api.cloudrf.com'
                config.add_section('data')
                config['data']['dir'] = 'data'
                with open('cloudrf.ini', 'w') as fp:
                    config.write(fp)

            if config['user']['key'] == 'CHANGEME':
                raise Exception(f'Please change configuration in {self.config_filename}')

            if self.key is None:
                self.key = config['user']['key']
            if self.strict_ssl is None:
                self.strict_ssl = config['api']['strict_ssl']
            if self.base_url is None:
                self.base_url = config['api']['base_url']
            if self.data_dir is None and config['data']['dir'].strip() != '':
                self.data_dir = config['data']['dir']

        self.strict_ssl = str2bool(self.strict_ssl)

    def run_network(self):
        """Network coverage analysis"""

        responses = []
        self.api = CloudRFNetwork(self.key, self.base_url, self.strict_ssl, self.save_response)
        self.api.set_download_dir(self.data_dir)

        print('Network "best server" API demo')
        print('Querying location for best server(s):')

        self.row_count = 0
        for f in self.args.data_files:
            with open(f, 'r') as fp:
                self.csv_data = csv.DictReader(fp)

                self.csv_rows = [row for row in self.csv_data]
                self.row_count += len(self.csv_rows)

                for row in self.csv_rows:
                    if self.args.verbose:
                        print(f'data: {row}')
                    self.api.request(row)
                    if self.args.verbose:
                        print(f'response: {self.api.response}')
                    self.api.download(select=self.args.dl_types)  # remove select to download all types available
                    responses.append(self.api.response)

            print('Done.', flush=True)
        return responses


if __name__ == '__main__':
    pp = pprint.PrettyPrinter(depth=6)
    app = App()
    pp.pprint(app.run_network())
