#!/usr/bin/env python3

import pathlib

from core.CloudRF import CloudRF

if __name__ == '__main__':
    
    CloudRF(
        REQUEST_TYPE = 'interference',
        DESCRIPTION = '''
            CloudRF Interference API

            Interference will use a common network name to merge and analyse sites within that network to show the best site at a given location.
        ''',
        ALLOWED_OUTPUT_TYPES = ['png'],
        CURRENT_PATH = pathlib.Path(__file__).parent.resolve()
    )
