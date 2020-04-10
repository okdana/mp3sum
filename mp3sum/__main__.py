# -*- coding: utf-8 -*-

"""
Script entry point.
"""

import os
import sys
import signal
import time
import multiprocessing

# Support direct calls to __main__.py
if __package__ is None and not hasattr(sys, 'frozen'):
  path = os.path.realpath(os.path.abspath(__file__))
  sys.path.insert(0, os.path.dirname(os.path.dirname(path)))

from mp3sum import arguments
from mp3sum import logging
from mp3sum import verifier

def main(argv=None):
  """
  Main script routine.
  """
  result_seen = 0
  result_pass = 0
  result_skip = 0
  result_fail = 0

  ret     = 0
  argv    = sys.argv[1:] if argv is None else argv
  parser  = arguments.init_args()
  options = arguments.parse_args(argv, parser)
  logger  = logging.Logger(options.log_level, colour = options.colour)
  paths   = []

  if options.path is None or len(options.path) == 0:
    parser.print_usage(sys.stderr)
    logger.warn('error: path not supplied', prefix = True, file = sys.stderr)
    return 1

  for path in options.path:
    # Path is non-existent
    if not os.path.exists(path):
      logger.warn('file not found: %s' % path, prefix = True, file = sys.stderr)
      ret |= 1
    # Path is a directory
    elif os.path.isdir(path):
      # Recursive — walk all files recursively
      if options.recursive:
        for root, sub_dirs, sub_files in os.walk(path):
          sub_files.sort()
          for sub_file in sub_files:
            sf = os.path.join(root, sub_file)
            if verifier.is_mp3(sf):
              paths.append(sf)
      # Non-recursive — get files in immediate directory
      else:
        sub_files = os.listdir(path)
        sub_files.sort()
        for sub_file in sub_files:
          sf = os.path.join(path, sub_file)
          if os.path.isfile(sf) and verifier.is_mp3(sf):
            paths.append(sf)
    # Path is a file
    else:
      paths.append(path)

  pool    = multiprocessing.Pool(options.workers)
  results = []

  logger.info('Running with %d worker thread(s)' % options.workers)
  logger.debug('')

  try:
    for path in paths:
      pool.apply_async(
        verifier.verify_mp3,
        args     = [path, logger, options],
        callback = lambda x: results.append(x)
      )

    pool.close()
    pool.join()
  except (KeyboardInterrupt, SystemExit):
    logger.error('Interrupted by user.', file = sys.stderr)

  for result in results:
    if result == verifier.ERROR_NOT_MP3:
      continue
    elif result == verifier.ERROR_OK:
      result_pass += 1
    elif result == verifier.ERROR_UNSUPPORTED:
      result_skip += 1
    elif result == verifier.ERROR_TAG_MISMATCH:
      result_fail += 1
    elif result == verifier.ERROR_MUSIC_MISMATCH:
      result_fail += 1
    else:
      raise NotImplementedError('Unsupported result %i' % result)

    result_seen += 1
    ret         |= result

  logger.error('%d file(s) checked:' % result_seen, end = ' ')
  logger.error('%d' % result_pass, fg = 'green', end = ' ')
  logger.error('pass', end = ', ')
  logger.error('%d' % result_skip, fg = 'yellow', end = ' ')
  logger.error('unsupported', end = ', ')
  logger.error('%d' % result_fail, fg = 'red', end = ' ')
  logger.error('fail')

  return 0 if ret == verifier.ERROR_OK else ret

if __name__ == '__main__':
  sys.exit(main() or 0)
