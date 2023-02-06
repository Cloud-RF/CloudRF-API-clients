#!/usr/bin/env python3

import pathlib

from core.CloudRF import CloudRF

if __name__ == '__main__':
    
    CloudRF(
        REQUEST_TYPE = 'mesh',
        DESCRIPTION = '''
            CloudRF Mesh API

            Mesh merges multiple area calculations into a single super layer.
        ''',
        ALLOWED_OUTPUT_TYPES = ['kmz', 'png'],
        CURRENT_PATH = pathlib.Path(__file__).parent.resolve()
    )
