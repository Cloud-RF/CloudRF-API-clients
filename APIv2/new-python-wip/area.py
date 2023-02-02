#!/usr/bin/env python3

import pathlib

from core.CloudRF import CloudRF

if __name__ == '__main__':

    CloudRF(
        REQUEST_TYPE = 'area',
        DESCRIPTION = '''
            CloudRF Area API

            Area coverage performs a circular sweep around a transmitter out to a user defined radius.
            It factors in system parameters, antenna patterns, environmental characteristics and terrain data to show a heatmap in customisable colours and units.
        ''',
        ALLOWED_OUTPUT_TYPES = ['kmz', 'png', 'shp', 'tiff'],
        CURRENT_PATH = pathlib.Path(__file__).parent.resolve()
    )
