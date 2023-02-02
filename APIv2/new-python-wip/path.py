#!/usr/bin/env python3

import pathlib

from core.CloudRF import CloudRF

if __name__ == '__main__':
    
    CloudRF(
        REQUEST_TYPE = 'path',
        DESCRIPTION = '''
            CloudRF Path API

            Path profile studies the link from one site to another in a direct line.
            It factors in system parameters, antenna patterns, environmental characteristics and terrain data to produce a JSON report containing enough values to incorporate into your analysis or create a chart from.
        ''',
        ALLOWED_OUTPUT_TYPES = ['kmz', 'png'],
        CURRENT_PATH = pathlib.Path(__file__).parent.resolve()
    )
