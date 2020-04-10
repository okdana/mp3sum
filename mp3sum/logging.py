# -*- coding: utf-8 -*-

"""
Log/output handling.
"""

from __future__ import print_function

import sys
import colors

CRITICAL = 50
ERROR    = 40
WARNING  = 30
INFO     = 20
DEBUG    = 10

_levels = [
  CRITICAL,
  ERROR,
  WARNING,
  INFO,
  DEBUG,
]

_levels_to_names = {
  CRITICAL: 'CRITICAL',
  ERROR:    'ERROR',
  WARNING:  'WARNING',
  INFO:     'INFO',
  DEBUG:    'DEBUG',
}

_names_to_levels = {
  'CRITICAL': CRITICAL,
  'ERROR':    ERROR,
  'WARNING':  WARNING,
  'INFO':     INFO,
  'DEBUG':    DEBUG,
}

class Logger(object):
  level  = WARNING
  colour = True
  prefix = None

  def __init__(self, level = None, colour = True, prefix = None):
    self.colour = colour
    self.prefix = prefix if prefix else __import__('mp3sum').__name__

    self.set_level(level if level is not None else self.WARNING)

  def set_level(self, level):
    self.level = self.normalise_level(level)
    return self

  def normalise_level(self, level):
    if str(level) == level:
      if level not in _names_to_levels:
        raise ValueError('Unknown level %s' % level)
      level = _name_to_levels[level]

    if level > _levels[0]:
      level = _levels[0]
    if level < _levels[-1]:
      level = _levels[-1]

    if level not in _levels:
      raise ValueError('Unknown level %i' % level)

    return level

  def puts(
    self,
    message,
    level  = None,
    fg     = None,
    bg     = None,
    style  = None,
    prefix = False,
    end    = "\n",
    file   = sys.stdout
  ):
    if level is not None and self.normalise_level(level) < self.level:
      return self

    if prefix:
      message = '%s: %s' % (self.prefix, message)
    if self.colour:
      message = colors.color(message, fg = fg, bg = bg, style = style)

    print(message, end = end, file = file)

    return self

  def critical(
    self,
    message,
    fg     = None,
    bg     = None,
    style  = None,
    prefix = False,
    end    = "\n",
    file   = sys.stdout
  ):
    return self.puts(
      message,
      level  = CRITICAL,
      fg     = fg,
      bg     = bg,
      style  = style,
      prefix = prefix,
      end    = end,
      file   = file
    )

  def error(
    self,
    message,
    fg     = None,
    bg     = None,
    style  = None,
    prefix = False,
    end    = "\n",
    file   = sys.stdout
  ):
    return self.puts(
      message,
      level  = ERROR,
      fg     = fg,
      bg     = bg,
      style  = style,
      prefix = prefix,
      end    = end,
      file   = file
    )

  def warning(
    self,
    message,
    fg     = None,
    bg     = None,
    style  = None,
    prefix = False,
    end    = "\n",
    file   = sys.stdout
  ):
    return self.puts(
      message,
      level  = WARNING,
      fg     = fg,
      bg     = bg,
      style  = style,
      prefix = prefix,
      end    = end,
      file   = file
    )

  def warn(
    self,
    message,
    fg     = None,
    bg     = None,
    style  = None,
    prefix = False,
    end    = "\n",
    file   = sys.stdout
  ):
    return self.puts(
      message,
      level  = WARNING,
      fg     = fg,
      bg     = bg,
      style  = style,
      prefix = prefix,
      end    = end,
      file   = file
    )

  def info(
    self,
    message,
    fg     = None,
    bg     = None,
    style  = None,
    prefix = False,
    end    = "\n",
    file   = sys.stdout
  ):
    return self.puts(
      message,
      level  = INFO,
      fg     = fg,
      bg     = bg,
      style  = style,
      prefix = prefix,
      end    = end,
      file   = file
    )

  def debug(
    self,
    message,
    fg     = None,
    bg     = None,
    style  = None,
    prefix = False,
    end    = "\n",
    file   = sys.stdout
  ):
    return self.puts(
      message,
      level  = DEBUG,
      fg     = fg,
      bg     = bg,
      style  = style,
      prefix = prefix,
      end    = end,
      file   = file
    )
