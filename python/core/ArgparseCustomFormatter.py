#!/usr/bin/env python3

import argparse

# This is used with argparse in the formatter_class argument to customise multiple formattings into one
class ArgparseCustomFormatter(
        # Don't do any line wrapping on descriptions
        argparse.RawDescriptionHelpFormatter, 
        # Include default values when running --help
        argparse.ArgumentDefaultsHelpFormatter
    ):
    pass
