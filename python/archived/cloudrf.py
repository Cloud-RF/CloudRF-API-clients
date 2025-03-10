"""Demonstrates all CloudRF APIs.

To build an application, you may use these CloudRFNetwork, CloudRFArea, CloudRFPath, CloudRFMesh and CloudRFInterference classes.
"""
import datetime
import json
import pystache
import re
import requests
import time
from pathlib import Path


class CloudRFAPI:
    """CloudRF API base class

    Class used to execute the main API request and process the response
    Only the endpoint and response processing differenciates separate APIs.
    """

    archive_endpoint = '/archive'
    # archive_endpoint = '/API/archive/data'  # v1

    def __init__(self, key, base_url=None, strict_ssl=True, save_response=False):
        super().__init__()

        self.renderer = pystache.Renderer()

        self.key = key

        if base_url is not None:
            self.base_url = base_url

        self.strict_ssl = strict_ssl
        self.save_response = save_response

        self.downloaded_files = []
        self.response = None

        # We raise an exception if endpoind does not end with /
        if self.endpoint[-1] != '/':
            raise Exception(f'endpoint {self.endpoint} does not end with /')

        # By default files are downloaded to the current working directory
        self.download_dir = Path.cwd()

        self.api_url = f'{self.base_url}{self.endpoint}'

    def set_download_dir(self, download_dir):
        # Making sure the directory exists
        Path(download_dir).mkdir(parents=True, exist_ok=True)

        self.download_dir = download_dir

    def get_filename(self):
        """Method to be overloaded

        By default no files are saved in API calls.
        """
        self.file = None

    def request(self, args):
        """Main request method

        Send web API request with retries, and optionaly saves response to file.
        """

        self.downloaded_files = []

        ext = 'json'

        error_count = 0

        while True:
            # merging 2 dictionaries to combine base arguments with API specific arguments
            self.req = requests.post(self.api_url, headers={'key': self.key}, data=args, verify=self.strict_ssl)

            # SLEIPNIR HTML output is raw HTML, anything else is JSON.
            if self.req.text[:6] == '<html>':
                self.response = self.req.text
                ext = 'html'
                break
            else:
                try:
                    self.response = json.loads(self.req.text)
                    if 'error' not in self.response:
                        error_count = 0
                        break
                except Exception as e:
                    print(f'exception: {e}')
                    print(self.req.text)

            error_count += 1

            # we sleep 1s if 2 attempts did not succeed
            if error_count >= 2:
                time.sleep(1)

            # we retry 5 times max
            if error_count >= 3:
                break

        if self.save_response:
            now = datetime.datetime.now()
            dtm_s = now.strftime('%Y%m%d%H%M%S_' + now.strftime('%f')[:3])
            filepath = Path(self.download_dir) / f'{dtm_s}-{self.api_id}.{ext}'

            new_json = {'CLOUDRF_URL': self.api_url, 'CLOUDRF_ARGS': args,
                        'HTML' if isinstance(self.response, str) else 'JSON': self.response}

            print(f'saving {str(filepath)}')
            with open(filepath, 'w') as outfile:
                json.dump(new_json, outfile, indent=4, sort_keys=False)

            self.downloaded_files.append(filepath)

        if error_count >= 3:
            raise Exception(f'API Error:{self.response["error"]}')

    def download_from_archive(self, fmt):
        print(self.response['kmz'])
        if "sid=" in self.response['kmz']:
          sid = self.response['kmz'].split('sid=')[1].split('&')[0]
          args = {'sid': sid, 'fmt': fmt}
        else:
          file = self.response['kmz'].split('/')[-2]
        req = requests.get(f'{self.base_url}{self.archive_endpoint}/{file}/{fmt}', headers={'key': self.key, 'content-type': 'text'},
                         verify=self.strict_ssl)
        print(f'downloading from {req.url}')
        #print(f'response from {req.headers}')

        filename = None
        if 'content-disposition' in req.headers:
            d = req.headers['content-disposition']
            filename = re.findall("filename=(.+)", d)[0].strip('"')

        if filename is None:
            print('filename not in response, using url arguments')
            filename = f'{file}.{fmt}'

        filepath = Path(self.download_dir) / filename

        print(f'saving {str(filepath)}')
        with open(filepath, 'wb') as fp:
            fp.write(req.content)

        self.downloaded_files.append(filepath)

        return filepath

    def download_direct(self, url, prefix=''):
        print(f'url {url}')
        req = requests.get(url, verify=True)
        # print(f'downloading from {req.url}')

        # if filename is available as part of the request we use it
        # otherwise we use the one from the url
        if 'content-disposition' in req.headers:
            d = req.headers['content-disposition']
            filename = re.findall("filename=(.+)", d)[0].strip('"')
        else:
            filename = url.split('/')[-1]

        if prefix != '':
            prefix += '_'

        filepath = Path(self.download_dir) / f'{prefix}{filename}'
        print(f'saving {str(filepath)}')
        with open(filepath, 'wb') as fp:
            fp.write(req.content)

        self.downloaded_files.append(filepath)

        return filepath

    def get_cov_map_url(self):
        return f'{self.base_url}/API/archive/calc?id={self.response["sid"]}'

    def save_cov_map_url(self):
        url = self.get_cov_map_url()

        filepath = Path(self.download_dir) / f'{self.response["id"]}_{self.response["sid"]}.url'
        print(f'saving {str(filepath)}')
        with open(filepath, 'w') as fp:
            fp.write('[InternetShortcut]\n')
            fp.write(f'URL={url}\n')

    def save_cov_map_html(self):
        sid = self.response["sid"]
        filepath = Path(self.download_dir) / f'{self.response["id"]}_{sid}.html'

        req = requests.get(f'{self.base_url}/API/archive/embed.php?sid={sid}', verify=self.strict_ssl)

        print(f'saving {str(filepath)}')
        with open(filepath, 'wb') as fp:
            fp.write(req.content)

        self.downloaded_files.append(filepath)


class CloudRFAPITemplated(CloudRFAPI):

    def mesh(self, nid, mesh):
        self.req = requests.get(f'{self.base_url}/mesh?network={nid}&name={mesh}', headers={'key': self.key}, verify=self.strict_ssl)
        self.response = json.loads(self.req.content)
        print(self.response)
        if not "error" in self.response:
          self.download_from_archive("kmz")



    def request(self, args, template=None):
        """Main request method

        Send web API request with retries, and optionaly saves response to file.
        """

        self.downloaded_files = []

        ext = 'json'

        error_count = 0
        rendered = self.renderer.render(template, args)
        data_json = json.loads(rendered)

        if 'points' in args:
            print(f'adding points from {args["points"]}')
            new_array = []
            for e in eval(args['points']):
                if len(e) == 3:
                    new_array.append({'lat':e[0], 'lon':e[1], 'alt':e[2]})
                elif len(e) == 2:  # point altitude is optional, if not supplied 'transmitter alt' is used.
                    new_array.append({'lat':e[0], 'lon':e[1], 'alt':data_json['transmitter']['alt']})

            data_json['points'] = new_array

        data_str = json.dumps(data_json)

        while True:
            # merging 2 dictionaries to combine base arguments with API specific arguments
            self.req = requests.post(self.api_url, headers={'key': self.key}, data=data_str, verify=self.strict_ssl)

            # SLEIPNIR HTML output is raw HTML, anything else is JSON.
            if self.req.text[:6] == '<html>':
                self.response = self.req.text
                ext = 'html'
                break
            else:
                try:
                    self.response = json.loads(self.req.text)
                    if 'error' not in self.response:
                        error_count = 0
                        break
                except Exception as e:
                    print(f'exception: {e}')
                    print(self.req.text)

            error_count += 1

            # we sleep 1s if 2 attempts did not succeed
            if error_count >= 2:
                time.sleep(1)

            # we retry 5 times max
            if error_count >= 3:
                break

        if self.save_response:
            now = datetime.datetime.now()
            dtm_s = now.strftime('%Y%m%d%H%M%S_' + now.strftime('%f')[:3])
            filepath = Path(self.download_dir) / f'{dtm_s}-{self.api_id}.{ext}'

            new_json = {'CLOUDRF_URL': self.api_url, 'CLOUDRF_ARGS': json.loads(data_str),
                        'HTML' if isinstance(self.response, str) else 'JSON': self.response}

            print(f'saving {str(filepath)}')
            with open(filepath, 'w') as outfile:
                json.dump(new_json, outfile, indent=4, sort_keys=False)

            self.downloaded_files.append(filepath)

        if error_count >= 3:
            raise Exception(f'API Error:{self.response["error"]}')
