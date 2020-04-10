# -*- coding: utf-8 -*-

"""
Command-line argument and configuration handling.
"""

import sys
import argparse
import multiprocessing

from mp3sum import logging

def init_args():
  """
  Initialises argument parser.

  @return argparse.ArgumentParser
  """
  p = argparse.ArgumentParser(
    prog            = __import__('mp3sum').__name__,
    description     = __import__('mp3sum').__description__.rstrip('.') + '.',
    usage           = '%(prog)s [options] path ...',
    add_help        = True,
    formatter_class = lambda prog: argparse.HelpFormatter(
      # This increases the max width of the arguments column
      prog, max_help_position = 38
    )
  )
  p.set_defaults(
    absolute  = False,
    basename  = False,
    batch     = False,
    colour    = None,
    log_level = None,
    recursive = False,
    show_fail = None,
    show_pass = True,
    show_skip = None,
    verbosity = [0],
    workers   = None
  )
  p.add_argument('-V', '--version',
    action  = 'version',
    version = '%s version %s' % (
      __import__('mp3sum').__name__,
      __import__('mp3sum').__version__,
    )
  )
  p.add_argument('-q', '--quiet',
    dest   = 'verbosity',
    action = 'append_const',
    const  = -1,
    help   = 'decrease verbosity (cumulative)'
  )
  p.add_argument('-v', '--verbose',
    dest   = 'verbosity',
    action = 'append_const',
    const  = 1,
    help   = 'increase verbosity (cumulative)'
  )
  p.add_argument('--absolute',
    action = 'store_true',
    help   = 'show absolute file paths in output'
  )
  p.add_argument('--basename',
    action = 'store_true',
    help   = 'show file base names in output'
  )
  p.add_argument('-b', '--batch',
    dest   = 'batch',
    action = 'store_true',
    help   = 'configure output for batch scripting'
  )
  p.add_argument('--colour',
    dest   = 'colour',
    action = 'store_true',
    help   = 'always show colour in output'
  )
  p.add_argument('--color', '--colours', '--colors',
    dest   = 'colour',
    action = 'store_true',
    help   = argparse.SUPPRESS
  )
  p.add_argument('--no-colour',
    dest   = 'colour',
    action = 'store_false',
    help   = 'never show colour in output'
  )
  p.add_argument('--no-color', '--no-colours', '--no-colors',
    dest   = 'colour',
    action = 'store_false',
    help   = argparse.SUPPRESS
  )
  p.add_argument('--nocolor', '--nocolours', '--nocolors',
    dest   = 'colour',
    action = 'store_false',
    help   = argparse.SUPPRESS
  )
  p.add_argument('-f', '--only-fail',
    dest   = 'show_fail',
    action = 'store_true',
    help   = 'limit output to failing results'
  )
  p.add_argument('--onlyfail', '--fail',
    dest   = 'show_fail',
    action = 'store_true',
    help   = argparse.SUPPRESS
  )
  p.add_argument('--log', '--log-level', '--loglevel',
    dest   = 'log_level',
    help   = argparse.SUPPRESS
  )
  p.add_argument('-r', '--recursive',
    dest   = 'recursive',
    action = 'store_true',
    help   = 'recurse into sub-directories'
  )
  p.add_argument('-R', '--recurse',
    dest   = 'recursive',
    action = 'store_true',
    help   = argparse.SUPPRESS
  )
  p.add_argument('-u', '--only-unsupported',
    dest   = 'show_skip',
    action = 'store_true',
    help   = 'limit output to unsupported results'
  )
  p.add_argument('--onlyunsupported', '--only-skip', '--onlyskip',
    dest   = 'show_skip',
    action = 'store_true',
    help   = argparse.SUPPRESS
  )
  p.add_argument('--workers',
    dest    = 'workers',
    type    = int,
    help    = 'set number of worker threads',
    metavar = 'num'
  )
  p.add_argument('path',
    nargs   = '*',
    help    = 'file(s) or folder(s) to verify',
    metavar = 'path ...'
  )

  return p

def parse_args(args, parser):
  """
  Parses command-line arguments.

  @param list args
    The arguments to parse.

  @param argparse.ArgumentParser parser
    An ArgumentParser instance.

  @return list
    The parsed and normalised arguments.
  """
  options = parser.parse_args(args)

  options.verbosity    = sum(options.verbosity)

  if options.batch:
    options.colour    = False
    options.verbosity = 0

  if options.verbosity <= -2:
    options.log_level = logging.CRITICAL
  if options.verbosity == -1:
    options.log_level = logging.ERROR
  if options.verbosity == 0:
    options.log_level = logging.WARNING
  if options.verbosity == 1:
    options.log_level = logging.INFO
  if options.verbosity >= 2:
    options.log_level = logging.DEBUG

  if options.colour is None:
    options.colour = sys.stdout.isatty()

  if options.show_fail is not None or options.show_skip is not None:
    options.show_pass = False
  else:
    options.show_pass = True
    options.show_skip = True
    options.show_fail = True

  # Force a single worker if we're verbose; the output will be garbled
  # if we don't
  if options.verbosity >= 2:
    options.workers = 1
  # Otherwise, try to auto-detect worker threads
  elif options.workers == None:
    try:
      options.workers = multiprocessing.cpu_count()
    except:
      options.workers = 1

  return options
