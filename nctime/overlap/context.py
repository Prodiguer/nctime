#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Processing context used in this module.

"""
from multiprocessing import cpu_count, Value, Lock
from multiprocessing.managers import SyncManager

from ESGConfigParser import SectionParser

from nctime.utils.collector import Collector
from nctime.utils.constants import *
from nctime.utils.misc import COLORS, get_project, Print
from nctime.utils.time import TimeInit


class ProcessingContext(object):
    """
    Encapsulates the processing context/information for main process.

    :param ArgumentParser args: Parsed command-line arguments
    :returns: The processing context
    :rtype: *ProcessingContext*

    """

    def __init__(self, args):
        self.directory = args.directory
        self.config_dir = args.i
        self.resolve = args.resolve
        self.full_only = args.full_only
        self.project = args.project
        self.tunits_default = None
        self.processes = args.max_processes if args.max_processes <= cpu_count() else cpu_count()
        self.use_pool = (self.processes != 1)
        self.overlaps = 0
        self.broken = 0
        self.lock = Lock()
        self.nbfiles = 0
        self.nbnodes = 0
        self.nbdsets = 0
        self.nbskip = 0
        self.nberrors = 0
        self.file_filter = []
        if args.include_file:
            self.file_filter.extend([(f, True) for f in args.include_file])
        else:
            # Default includes netCDF only
            self.file_filter.append(('^.*\.nc$', True))
        if args.exclude_file:
            # Default exclude hidden files
            self.file_filter.extend([(f, False) for f in args.exclude_file])
        else:
            self.file_filter.append(('^\..*$', False))
        self.dir_filter = args.ignore_dir
        # Initialize print management
        self.echo = Print(log=args.log, debug=args.debug, cmd=args.cmd, all=args.all)

    def __enter__(self):
        # Init process manager
        if self.use_pool:
            manager = SyncManager()
            manager.start()
            self.progress = manager.Value('i', 0)
        else:
            self.progress = Value('i', 0)
        # Init data collector
        self.sources = Collector(sources=self.directory)
        # Init file filter
        for regex, inclusive in self.file_filter:
            self.sources.FileFilter.add(regex=regex, inclusive=inclusive)
        # Exclude fixed frequency in any case
        self.sources.FileFilter.add(regex='(_fx_|_fixed_|_fx.|_fixed.|_.fx_)', inclusive=False)
        # Init dir filter
        self.sources.PathFilter.add(regex=self.dir_filter, inclusive=False)
        # Set driving time properties
        self.tinit = TimeInit(ref=self.sources.first(), tunits_default=self.tunits_default)
        self.ref_calendar = self.tinit.calendar
        # Get project id
        if not self.project:
            self.project = get_project(self.sources.first())
        # Get default time units if exists (i.e., CORDEX case)
        if self.project in DEFAULT_TIME_UNITS.keys():
            self.tunits_default = DEFAULT_TIME_UNITS[self.project]
        # Init configuration parser
        self.cfg = SectionParser(section='project:{}'.format(self.project), directory=self.config_dir)
        self.pattern = self.cfg.translate('filename_format')
        return self

    def __exit__(self, exc_type, exc_val, traceback):
        # Decline outputs depending on the scan results
        msg = COLORS.HEADER + '\nNumber of files scanned: {}'.format(self.nbfiles) + COLORS.ENDC
        if self.nbskip:
            msg += COLORS.FAIL
        else:
            msg += COLORS.OKGREEN
        msg += '\nNumber of file(s) skipped: {}'.format(self.nbskip) + COLORS.ENDC
        msg += COLORS.OKBLUE + '\nNumber of node(s): {}'.format(self.nbnodes) + COLORS.ENDC
        msg += COLORS.HEADER + '\nNumber of dataset(s): {}'.format(self.nbdsets) + COLORS.ENDC
        if self.overlaps:
            msg += COLORS.FAIL
        else:
            msg += COLORS.OKGREEN
        msg += '\nNumber of datasets with overlap(s): {}'.format(self.overlaps) + COLORS.ENDC
        if self.broken:
            msg += COLORS.FAIL
        else:
            msg += COLORS.OKGREEN
        msg += '\nNumber of datasets with broken time series: {}'.format(self.broken) + COLORS.ENDC
        # Print summary
        self.echo.summary(msg)
        # Print log path if exists
        self.echo.info(COLORS.HEADER + '\nSee log: {}'.format(self.echo._logfile) + COLORS.ENDC)
