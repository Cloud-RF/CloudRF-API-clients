"""Demonstrates Path CloudRF API."""
import argparse
import configparser
import csv
import os
import textwrap
from pathlib import Path
import pprint

from cloudrf import CloudRFAPITemplated


# TODO: Deal with html / url
class CloudRFPath(CloudRFAPITemplated):
    """Path API class"""

    endpoint = '/path/'
    api_id = 'path'
    file_types = ['chart', 'kmz']
    type_map = {'chart': 'Chart image', 'kml': 'Network KML', 'kmz': 'kmz'}

    def download(self, select=None):
        select = self.file_types if select is None else select

        for dtype in select:
            if self.type_map[dtype] in self.response:
                self.download_direct(self.response[self.type_map[dtype]])


class App:
    """Application class

    This class's base class is configured using a cloudrf.ini configuration file.
    At first run, a default configuration file will be created. Change all values as required.
    Alternatively, the CLOUDRF_UID and CLOUDRF_KEY environment variables may be used to override the file configuration.

    This behaviour may be changed by removing the AppAddOn base class
    """

    config_filename = 'cloudrf.ini'

    # Default template, we need all values supplied in CSV source
    template = """
    {
    "site": "{{name}}",
    "network": "{{net}}",
    "transmitter": {
        "lat": {{lat}},
        "lon": {{lon}},
        "alt": {{lat}},
        "frq": {{frq}},
        "txw": {{txw}},
        "bwi": {{bwi}}
    },
    "antenna": {
        "txg": {{txg}},
        "txl": {{txl}},
        "ant": {{ant}},
        "azi": {{azi}},
        "tlt": {{tlt}},
        "hbw": {{hbw}},
        "vbw": {{vbw}},
        "pol": "{{pol}}"
    },
    "receiver": {
        "lat": {{rlat}},
        "lon": {{rlon}},
        "alt": {{ralt}},
        "rxg": {{rxg}},
        "rxs": {{rxs}}
    },
    "model": {
        "pm": {{pm}},
        "pe": {{pe}},
        "cli": {{cli}},
        "ked": {{ked}},
        "rel": {{rel}},
        "ter": {{ter}}
    },
    "environment": {
        "clm": {{clm}},
        "cll": {{cll}},
        "mat": {{mat}}
    },
    "output": {
        "units": "{{units}}",
        "col": "{{col}}",
        "out": {{out}},
        "ber": {{ber}},
        "mod": {{mod}},
        "nf": {{nf}},
        "res": {{res}},
        "rad": {{rad}}
    }
    }"""

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
            CloudRF Path application

            Path Profile studies the link from one site to another in a direct line.
            It factors in system parameters, antenna patterns, environmental characteristics
            and terrain data to produce a JSON report containing enough values to incorporate
            into your analysis or create a chart from.

            This demonstration program utilizes the CloudRF Path API to generate any
            of the possible file outputs offered by the API from {CloudRFPath.file_types}.
            The API arguments are sourced from csv file(s).
            please use -s all to generate ALL outputs available.

            Please refer to API Reference https://api.cloudrf.com/'''),
                                         formatter_class=argparse.RawDescriptionHelpFormatter)

        parser.add_argument('-i', dest='data_files', metavar='data_file', nargs='+', help='data input filename(csv)')
        parser.add_argument('-s', dest='dl_types', nargs='+',
                            choices=CloudRFPath.file_types + ['all'], default=['chart'],
                            help='type of output file to be downloaded')
        parser.add_argument('-o', dest='output_dir', metavar='output_dir',
                            help='output directory where files are downloaded')
        parser.add_argument('-r', dest='save_response', action="store_true", help='save response content (json/html)')
        parser.add_argument('-v', dest='verbose', action="store_true", help='Output more information on screen')
        parser.add_argument('-t', dest='template', help='JSON template to use')

        # for unit testing it is useful to be able to pass arguments.
        if args is None:
            self.args = parser.parse_args()
        else:
            if isinstance(args, str):
                args = args.split(' ')
            self.args = parser.parse_args(args)

        # if all selected then we reset the list to all types.
        if 'all' in self.args.dl_types:
            self.args.dl_types = CloudRFPath.file_types

        if self.args.template is not None:
            with open(self.args.template, mode='r') as json_file:
                self.template = json_file.read()

        self.save_response = self.args.save_response

    def configure(self):
        """Application configuration

        Adds functionality to load key from configuration or environment
        you may find simpler to use the following assignments instead
        self.ikey = "CHANGEME"
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

    def run_path(self):
        """Path coverage analysis"""

        responses = []
        self.api = CloudRFPath(self.key, self.base_url, self.strict_ssl, self.save_response)
        self.api.set_download_dir(self.data_dir)

        print('Drivetest demo via /path API. CSV data should contain columns: rlat,rlon,measured')

        self.row_count = 0
        distinctPoints = []
        for f in self.args.data_files:
            with open(f, 'r') as fp:
                self.csv_data = csv.DictReader(fp)

                self.csv_rows = [row for row in self.csv_data]
                self.row_count += len(self.csv_rows)
                print("Latitude\tLongitude\tReceived\tModelled\tDifference\tDistance")
                for row in self.csv_rows:
                    if self.args.verbose:
                        print(f'data: {row}')
                    if str(round(float(row["rlat"]),3))+str(round(float(row["rlon"]),3)) not in distinctPoints:
                      distinctPoints.append(str(round(float(row["rlat"]),3))+str(round(float(row["rlon"]),3)))
                      self.api.request(row, self.template)
                      
                      delta = round(float(self.api.response["Transmitters"][0]["Signal power at receiver dBm"]) - float(row["measured"]))
                      distance = round(float(self.api.response["Transmitters"][0]["Distance to receiver km"]) * 1e3) # metres
                      
                      print("RxLat: %.5f RxLon: %.5f Measured: %.1fdBm Modelled: %.1fdBm Difference: %ddB Distance: %dm" %  \
                        (float(row["rlat"]),float(row["rlon"]),float(row["measured"]),self.api.response["Transmitters"][0]["Signal power at receiver dBm"],delta, distance))

                    else:
                      #print("Duplicate point: %s, %s.." % (row["rlat"],row["rlon"]))
                      pass

            print('Done.', flush=True)
        return responses


if __name__ == '__main__':
    pp = pprint.PrettyPrinter(depth=6)
    app = App()
    pp.pprint(app.run_path())
