#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
   :platform: Unix
   :synopsis: Useful functions to use with this package.

"""

import logging
import os
import re
from datetime import datetime

from constants import *


class LogFilter(object):
    """
    Log filter with upper log level to use with the Python
    `logging <https://docs.python.org/2/library/logging.html>`_ module.

    """

    def __init__(self, level):
        self.level = level

    def filter(self, log_record):
        """
        Set the upper log level.

        """
        return log_record.levelno <= self.level


def init_logging(log, verbose=False, level='INFO'):
    """
    Initiates the logging configuration (output, date/message formatting).
    If a directory is submitted the logfile name is unique and formatted as follows:
    ``name-YYYYMMDD-HHMMSS-JOBID.log``If ``None`` the standard output is used.

    :param str log: The logfile directory.
    :param boolean verbose: Verbose mode.
    :param str level: The log level.

    """
    logname = 'esgprep-{}-{}'.format(datetime.now().strftime("%Y%m%d-%H%M%S"), os.getpid())
    formatter = logging.Formatter(fmt='%(levelname)-10s %(asctime)s %(message)s')
    if log:
        if not os.path.isdir(log):
            os.makedirs(log)
        logfile = os.path.join(log, logname)
    else:
        logfile = os.path.join(os.getcwd(), logname)
    logging.getLogger().setLevel(logging.DEBUG)
    if log:
        handler = logging.FileHandler(filename='{}.log'.format(logfile), delay=True)
    else:
        if verbose:
            handler = logging.StreamHandler()
        else:
            handler = logging.NullHandler()
    handler.setLevel(logging.__dict__[level])
    handler.addFilter(LogFilter(logging.WARNING))
    handler.setFormatter(formatter)
    logging.getLogger().addHandler(handler)


def trunc(f, n):
    """
    Truncates a float f to n decimal places before rounding

    :param float f: The number to truncates
    :param int n: Decimal number to place before rounding
    :returns: The corresponding truncated number
    :rtype: *float*

    """
    slen = len('%.*f' % (n, f))
    return float(str(f)[:slen])


def cmd_exists(cmd):
    """
    Checks if a Shell command exists.

    :returns: True if exists.
    :rtype: *boolean*

    """
    return any(
        os.access(os.path.join(path, cmd), os.X_OK)
        for path in os.environ["PATH"].split(os.pathsep)
    )


def match(pattern, string, negative=False):
    """
    Validates a string against a regular expression.
    Only match at the beginning of the string.

    :param str pattern: The regular expression to match
    :param str string: The string to test
    :param boolean negative: True if negative matching (i.e., exclude the regex)
    :returns: True if it matches
    :rtype: *boolean*

    """
    if negative:
        return True if not re.search(pattern, string) else False
    else:
        return True if re.search(pattern, string) else False
