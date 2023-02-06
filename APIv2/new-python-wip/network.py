#!/usr/bin/env python3

import pathlib

from core.CloudRF import CloudRF

if __name__ == '__main__':
    
    CloudRF(
        REQUEST_TYPE = 'network',
        DESCRIPTION = '''
            CloudRF Network API

            Network allows to find the best site for a given location based upon a common network name.
        ''',
        ALLOWED_OUTPUT_TYPES = ['png', 'txt'],
        CURRENT_PATH = pathlib.Path(__file__).parent.resolve()
    )
