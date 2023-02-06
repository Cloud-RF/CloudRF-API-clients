#!/usr/bin/env python3

import pathlib

from core.CloudRF import CloudRF

if __name__ == '__main__':
    
    CloudRF(
        REQUEST_TYPE = 'multisite',
        DESCRIPTION = '''
            CloudRF Multisite API

            Multisite creates multiple area multipoint calculations in a single request.
            It uses multiple transmitter locations to produce one response which factors in each transmitter.
        ''',
        ALLOWED_OUTPUT_TYPES = ['png'],
        CURRENT_PATH = pathlib.Path(__file__).parent.resolve()
    )
