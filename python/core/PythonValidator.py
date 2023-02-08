#!/usr/bin/env python3

import sys

class PythonValidator:
    def version():
        requiredMajor = 3
        minimumMinor = 8

        if sys.version_info.major != requiredMajor or sys.version_info.minor < minimumMinor:
            sys.exit('Your Python version (%s) does not meet the minimum required version of %s' % (
                    str(sys.version_info.major) + '.' + str(sys.version_info.minor), 
                    str(requiredMajor) + '.' + str(minimumMinor)
                )
            )
