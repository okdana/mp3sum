# -*- coding: utf-8 -*-

"""
Utility functions.
"""

import crcmod.predefined

"""
Computes the CRC-16 check-sum of a string.
"""
crc16 = crcmod.predefined.mkCrcFun('crc-16')

def unpad_integer(integer, bits=7):
	"""
	Decodes a bit-padded integer such as the one used for ID3v2 tag sizes.

	@param bytearray integer
	  The integer to unpad in its 'raw' byte-array form.

	@param int bits
	  (optional) The number of non-padded bits to the integer. The default is
	  7 (as used by ID3v2).

	@return int
	  The unpadded integer.
	"""
	mask   = (1 << (bits)) - 1
	bytes  = []
	result = 0

	while integer:
		bytes.append(integer & mask)
		integer = integer >> 8
	for shift, byte in zip(range(0, len(bytes) * bits, bits), bytes):
		result += byte << shift

	return result

def format_offset(offset):
	"""
	Formats an integer file offset.

	@param int offset
	  The integer offset to format.

	@return str
	  The formatted offset.
	"""
	if offset is None or offset < 0:
		return 'None'
	return "0x%08x (%i)" % (offset, offset)

