#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import setuptools

setuptools.setup(
	name                 = __import__('mp3sum').__name__,
	description          = __import__('mp3sum').__description__,
	url                  = __import__('mp3sum').__url__,
	version              = __import__('mp3sum').__version__,
	author               = __import__('mp3sum').__author__,
	author_email         = __import__('mp3sum').__author_email__,
	license              = 'MIT',
	keywords             = 'audio mp3 crc checksum integrity musiccrc lame',
	packages             = [__import__('mp3sum').__name__],
	include_package_data = True,
	entry_points         = {
		'console_scripts': [
			'%s = %s.__main__:main' % (
				__import__('mp3sum').__name__,
				__import__('mp3sum').__name__,
			)
		],
	},
)

