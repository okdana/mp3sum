# -*- coding: utf-8 -*-

"""
MP3 integrity-verification and related functions.
"""

import os
import sys
import struct

from distutils.version import LooseVersion

from mp3sum import util

ERROR_NOT_MP3        = -1
ERROR_OK             = 0
ERROR_UNSUPPORTED    = 2
ERROR_TAG_MISMATCH   = 4
ERROR_MUSIC_MISMATCH = 8

MPEG_FRAME_SYNC = 0xffe00000
MPEG_VERSION_1  = 0x180000
MPEG_LAYER_3    = 0x20000
MPEG_NO_CRC     = 0x10000
MPEG_PADDING    = 0x200

ID3V2_MAGIC         = b'ID3'
ID3V2_REVISION_MAX  = 0xfe
ID3V2_FLAG_EXTENDED = 0x40

INFO_CBR_MAGIC = b'Info'
INFO_VBR_MAGIC = b'Xing'

LAME_VERSION_MAGIC = b'LAME'

class Result(Exception):
  def __init__(self, result, path):
    self.result = result
    self.path   = path
    Exception.__init__(self, '%s yielded result: %i' % (path, result))

def is_mp3(path):
  """
  Determines whether a file looks like an MP3.

  @param str path
    The path to the file to check.

  @return bool
    True if the file seems like an MP3, False if not.
  """
  if path.startswith('._'):
    return False
  if path.lower().endswith('.mp3'):
    return os.path.isfile(path)
  return False

def find_frame(buffer):
  """
  Finds the next MP3 frame header.

  @param bytearray buffer
    Bytes from an MP3 file.

  @return int
    The index in the buffer where the frame was found, or -1 if not found.
  """
  try:
    synchs = [buffer.find(b'\xFF\xFA'), buffer.find(b'\xFF\xFB')]
    return min(x for x in synchs if x > -1)
  except ValueError:
    return -1

def verify_mp3(path, logger, options):
  """
  Verifies the integrity of an MP3 file.

  @param str path
    The path to the (possible) MP3 file to be verified.

  @param Logger logger
    A Logger instance for printing messages.

  @return int
    One of this module's error constants.
  """
  try:
    tag_crc       = None
    tag_crc_now   = None
    music_crc     = None
    music_crc_now = None

    try:
      if options.absolute:
        display_path = os.path.abspath(path)
      elif options.basename:
        display_path = os.path.basename(path)
      else:
        display_path = path
    except:
      display_path = path

    logger.debug('%s:' % display_path)

    handle = open(path, 'rb')
    chunk  = 1024
    buffer = handle.read(chunk)

    # If we don't have a straight MP3 header, look for an ID3v2 tag to skip
    while True:
      frame = find_frame(buffer)

      if frame == 0:
        break

      try:
        id3v2            = struct.unpack('> 3s x b b i', buffer[0:10])
        id3v2_identifier = id3v2[0]
        id3v2_revision   = id3v2[1]
        id3v2_flags      = id3v2[2]
        id3v2_length     = util.unpad_integer(id3v2[3])

      # This is probably not an MP3 file at all
      except struct.error as e:
        logger.debug('No MP3 or ID3v2 signature near offset %s' % (
          util.format_offset(handle.tell() - chunk)
        ))
        raise Result(ERROR_UNSUPPORTED, display_path)

      # ID3v2 tags have an identifier of 'ID3' followed by a major
      # version number and then a revision number < 0xFF
      if id3v2_identifier != ID3V2_MAGIC or id3v2_revision > ID3V2_REVISION_MAX:
        logger.debug('Bad ID3v2 signature at offset %s' % (
          util.format_offset(handle.tell() - chunk)
        ))
        raise Result(ERROR_UNSUPPORTED, display_path)

      logger.debug('Found ID3v2 signature at offset %s' % (
        util.format_offset(handle.tell() - chunk)
      ))
      logger.debug('Found ID3v2 tag length of %i bytes' % id3v2_length)

      # Extended header is enabled when bit 0100000 is set
      if id3v2_flags & ID3V2_FLAG_EXTENDED:
        logger.debug('Found ID3v2 extended header')

      # Seek past the reported tag length and see if we can find our
      # frame header
      handle.seek(id3v2_length + 10 - chunk, 1)
      buffer = handle.read(chunk)

      # Another ID3v2 frame (sigh)
      if buffer.find(ID3V2_MAGIC) == 0:
        continue

      frame = find_frame(buffer)

      if frame < 0:
        logger.debug('Missing MP3 frame header near offset %s' % (
          util.format_offset(handle.tell() - chunk)
        ))
        raise Result(ERROR_UNSUPPORTED, display_path)

    logger.debug('Found MP3 frame header at offset %s' % (
      util.format_offset(handle.tell() - chunk + frame)
    ))

    try:
      segment = buffer[frame:frame + 190 + 2]
      info    = struct.unpack(
        #  pre
        #  |   Xing/Info
        #  |   |  info data
        #  |   |  |    LAME version
        #  |   |  |    |  LAME data
        #  |   |  |    |  |   music CRC
        #  |   |  |    |  |   |  tag CRC
        #  |   |  |    |  |   |  |
        '> 36s 4s 116s 9s 23s H  H',
        segment
      )
      info_tag  = info[1]

      # Check for 'Xing'/'Info'
      if info_tag != INFO_VBR_MAGIC and info_tag != INFO_CBR_MAGIC:
        segment = buffer[frame:frame + 175 + 2]
        info    = struct.unpack(
          '> 21s 4s 116s 9s 23s H  H',
          segment
        )

      info_tag  = info[1]
      lame_tag  = info[3]
      music_crc = info[5]
      tag_crc   = info[6]

      logger.debug('Unpacked %i bytes between offsets %s and %s' % (
        len(segment),
        util.format_offset(handle.tell() - chunk + frame),
        util.format_offset(handle.tell() - chunk + frame + len(segment))
      ))

    except struct.error as e:
      logger.debug('Failed to unpack header near offset %s: %s' % (
        util.format_offset(handle.tell() - chunk + frame), e
      ))
      raise Result(ERROR_UNSUPPORTED, display_path)

    # Check for 'Xing'/'Info'
    if info_tag != INFO_VBR_MAGIC and info_tag != INFO_CBR_MAGIC:
      logger.debug('Unexpected Xing/Info tag data %s' % info_tag)
      tag_crc   = 0
      music_crc = 0
      raise Result(ERROR_UNSUPPORTED, display_path)

    logger.debug('Found Xing/Info tag %s' % info_tag)

    # Check for 'LAME'
    if not lame_tag.startswith(LAME_VERSION_MAGIC):
      logger.debug('Bad LAME tag %s; trying anyway' % lame_tag)
    # Check version number
    else:
      try:
        lame_version = LooseVersion(lame_tag[4:9].decode('utf-8'))
        lame_version < LooseVersion('3.90') # Catch incompatible versions
      except:
        lame_version = None

      # If our cast to float failed, it's probably because some stupid
      # scene group messed with the version string
      if lame_version is None:
        logger.debug('Bad LAME tag %s; trying anyway' % lame_tag)
      # LAME versions <3.90 don't do MusicCRC
      elif lame_version < LooseVersion('3.90'):
        logger.debug('Insufficient LAME version %s' % lame_tag)
        raise Result(ERROR_UNSUPPORTED, display_path)
      else:
        logger.debug('Found LAME tag %s' % lame_tag)

    # If one of our CRCs is all zeroes, it's probably busted
    if tag_crc == 0 or music_crc == 0:
      logger.debug('Bad CRC values %s, %s' % (tag_crc, music_crc))
      raise Result(ERROR_UNSUPPORTED, display_path)

    logger.debug('Found tag CRC: %04X (%i), music CRC: %04X (%i)' % (
      tag_crc, tag_crc, music_crc, music_crc
    ))

    # Compute tag CRC
    tag_crc_now = util.crc16(buffer[frame:frame + len(segment) - 2])

    if tag_crc_now != tag_crc:
      logger.debug('Tag CRC mismatch: computed %04X, expected %04X' % (
        tag_crc_now, tag_crc
      ))
      raise Result(ERROR_TAG_MISMATCH, display_path)

    logger.debug('Computed tag CRC: %04X' % tag_crc_now)

    # Find next MPEG frame so we can compute the music CRC
    handle.seek(handle.tell() - chunk + frame + len(segment))
    buffer = handle.read(chunk)

    next_frame        = find_frame(buffer)
    next_frame_offset = handle.tell() - chunk + next_frame

    if next_frame < 0:
      logger.debug('Music CRC computation failed — missing next frame')
      raise Result(ERROR_MUSIC_MISMATCH, display_path)

    logger.debug('Found next frame (%s) at offset %s' % (
      buffer[next_frame:next_frame + 4],
      util.format_offset(next_frame_offset)
    ))

    #raise Result(ERROR_UNSUPPORTED, display_path)

    # Now we have to work on the tags at the end. An MP3 file is generally
    # laid out like this:
    #
    # [ID3v2][header/info][audio][Lyrics3v2][APEv2][ID3v1]
    #
    # Let's assume that all of that junk on the end will fit into the last
    # 512 KiB of the file...
    try:
      end_chunk_size = 512 * 1024
      handle.seek(end_chunk_size * -1, 2)
      buffer         = handle.read()
    # If the above fails, the file is probably too short, so let's just go
    # back to the beginning and read the entire thing
    except IOError:
      end_chunk_size = 0
      handle.seek(0, 0)
      buffer         = handle.read()

    # Try to obtain the index of the Lyrics3v2 tag
    try:
      lyrics3v2_offset = buffer.index(b'LYRICSBEGIN')
      if end_chunk_size > 0:
        lyrics3v2_offset = handle.tell() - end_chunk_size + lyrics3v2_offset
      logger.debug('Found Lyrics3v2 tag at offset %s' % (
        util.format_offset(lyrics3v2_offset)
      ))
    except ValueError:
      lyrics3v2_offset = None

    # Try to obtain the index of the APE tag
    try:
      apev2_offset = buffer.index(b'APETAGEX')
      if end_chunk_size > 0:
        apev2_offset = handle.tell() - end_chunk_size + apev2_offset
      logger.debug('Found APEv2 tag at offset %s' % (
        util.format_offset(apev2_offset)
      ))
    except ValueError:
      apev2_offset = None

    # Try to obtain the index of the ID3v1 tag — for this one we'll get the
    # last 259 bytes of the file (256 bytes + length of 'TAG' header)
    try:
      handle.seek(-259, 2)
      buffer = handle.read()
    except OSError:
      handle.seek(-131, 0)
      buffer = handle.read()

    # We're going to test to see if this is either 128 OR 256 bytes from
    # EOF — apparently sometimes the ID3 tag can get duplicated (this
    # appeared during testing), so i suppose we should allow it. If it
    # doesn't appear at one of these points, it's probably not an ID3v1 tag
    # 256 bytes
    if buffer[3:6] == b'TAG' and buffer[0:8] != b'APETAGEX':
      if not end_chunk_size:
        handle.seek(0, 2)
      id3v1_offset = handle.tell() - 256
    # 128 bytes
    elif len(buffer) > 131 and buffer[131:134] == b'TAG' and buffer[128:136] != b'APETAGEX':
      if not end_chunk_size:
        handle.seek(0, 2)
      id3v1_offset = handle.tell() - 128
    # Not present
    else:
      id3v1_offset = None

    if id3v1_offset:
      logger.debug('Found ID3v1 tag at offset %s' % (
        util.format_offset(id3v1_offset)
      ))

    # Get the lowest offset and use that as the end of our audio stream
    try:
      audio_end_offset = filter(None, [lyrics3v2_offset, apev2_offset, id3v1_offset])
      audio_end_offset = min(audio_end_offset)
    # If there's no lowest offset, there's nothing at the end to worry about
    except (ValueError, TypeError):
      audio_end_offset = None

    logger.debug('Found audio stream end at offset %s' % (
      util.format_offset(audio_end_offset) if audio_end_offset else 'EOF'
    ))
    logger.debug('Found audio stream length of %s bytes' % (
      (audio_end_offset - next_frame_offset) if audio_end_offset else 'EOF'
    ))

    # Try to pull the audio stream
    handle.seek(next_frame_offset, 0)

    try:
      if audio_end_offset:
        buffer = handle.read(audio_end_offset - next_frame_offset)
      else:
        buffer = handle.read()
    except IOError:
      logger.debug('Failed to parse audio stream')
      raise Result(ERROR_MUSIC_MISMATCH, display_path)

    music_crc_now = util.crc16(buffer)

    if music_crc != music_crc_now:
      logger.debug('Music CRC mismatch: computed %04X, expected %04X' % (
        music_crc_now, music_crc
      ))
      raise Result(ERROR_MUSIC_MISMATCH, display_path)

    logger.debug('Computed music CRC: %04X' % music_crc_now)

    raise Result(ERROR_OK, display_path)

  # SIGINT handling
  except (KeyboardInterrupt, SystemExit):
    return ERROR_NOT_MP3

  # Handle result printing
  except Result as e:
    tag_crc       = '%04X' % (tag_crc       if tag_crc       else 0)
    tag_crc_now   = '%04X' % (tag_crc_now   if tag_crc_now   else 0)
    music_crc     = '%04X' % (music_crc     if music_crc     else 0)
    music_crc_now = '%04X' % (music_crc_now if music_crc_now else 0)

    final_result  = '%s:%s %s:%s' % (
      tag_crc_now, tag_crc,
      music_crc_now, music_crc
    )

    if options.show_pass and e.result == ERROR_OK:
      logger.warn('P %s' % final_result, fg = 'green', end = ' ')
      logger.warn(display_path)
    if options.show_skip and e.result == ERROR_UNSUPPORTED:
      logger.warn('U %s' % final_result, fg = 'yellow', end = ' ')
      logger.warn(display_path)
    if options.show_fail and e.result == ERROR_TAG_MISMATCH:
      logger.warn('F %s' % final_result, fg = 'red', end = ' ')
      logger.warn(display_path)
    if options.show_fail and e.result == ERROR_MUSIC_MISMATCH:
      logger.warn('F %s' % final_result, fg = 'red', end = ' ')
      logger.warn(display_path)

    logger.debug('')
    return e.result
