#!/usr/bin/env python3

import pathlib

from core.CloudRF import CloudRF

if __name__ == '__main__':
    
    CloudRF(
        REQUEST_TYPE = 'points',
        DESCRIPTION = '''
            CloudRF Points API

            Points calculates multiple point-to-point links in one call.
            It uses points to test many transmitters to one receiver and is commonly used for route analysis or calculating signal at known locations.
        ''',
        ALLOWED_OUTPUT_TYPES = ['kmz'],
        CURRENT_PATH = pathlib.Path(__file__).parent.resolve()
    )
