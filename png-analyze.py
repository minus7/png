#!/usr/bin/env python3

PROG_NAME = "PNG Chunk Analyzer"

PNG_HEADER = b"\x89PNG\r\n\x1a\n"

import struct
import string
import zlib
import logging
logging.basicConfig(format="[%(asctime)s] %(levelname)s: %(message)s", level=logging.DEBUG)
L = logging.getLogger("PNG")

class Chunk(object):
	"""Represents a PNG Chunk

	A chunk consists of an unsigned 32-bit length field (network order),
	followed by a 4-byte chunk name, followed by the data and a CRC32 of
	the name field and data.
	The name must be in A-Za-z
	"""
	def __init__(self, data=None, name=None, verify_crc=True, ignore_errors=False):
		self.ignore_errors = ignore_errors
		self.length = 0
		self.crc = 0
		if name:
			self.name = name
			self.data = data
		else:
			self.parse(data)

	def parse(self, data):
		if len(data) < 12:
			msg = "Chunk-data too small"
			L.error(msg)
			if not self.ignore_errors: raise ValueError(msg)

		# chunk header & data
		(self.length, raw_name) = struct.unpack("!I4s", data[0:8])
		self.data = data[8:-4]
		self.verify_length()
		self.name = raw_name.decode("ascii")
		self.verify_name()

		# chunk crc
		self.crc = struct.unpack("!I", data[8+self.length:8+self.length+4])[0]
		self.verify_crc()

	def verify_length(self):
		if len(self.data) != self.length:
			msg = "Data length ({}) does not match length in chunk header ({})".format(len(self.data), self.length)
			L.warning(msg)
			if not self.ignore_errors: raise ValueError(msg)
			return False
		return True

	def verify_name(self):
		for c in self.name:
			if c not in string.ascii_letters:
				msg = "Invalid character in chunk name: {}".format(repr(self.name))
				L.warning(msg)
				if not self.ignore_errors: raise ValueError(msg)
				return False
			return True

	def verify_crc(self):
		calculated_crc = zlib.crc32(self.name.encode("ascii") + self.data)
		if self.crc != calculated_crc:
			msg = "CRC mismatch: {:08X} (header), {:08X} (calculated)".format(self.crc, calculated_crc)
			L.warning(msg)
			if not self.ignore_errors: raise ValueError(msg)
			return False
		return True

	def update_length(self):
		self.length = len(self.data)

	def update_crc(self):
		self.crc = zlib.crc32(self.name.encode("ascii") + self.data)

	def build(self, auto_crc=True, auto_length=True):
		if auto_length: self.update_length()
		if auto_crc: self.update_crc()
		self.verify_name()
		return struct.pack("!I", self.length) + self.name.encode("ascii") + self.data + struct.pack("!I", self.crc)

	def ancillary(set=None):
		"""Set and get ancillary=True/critical=False bit"""
		if set is True:
			self.name[0] = self.name[0].lower()
		elif set is False:
			self.name[0] = self.name[0].upper()
		return self.name[0].islower()

	def private(set=None):
		"""Set and get private=True/public=False bit"""
		if set is True:
			self.name[1] = self.name[1].lower()
		elif set is False:
			self.name[1] = self.name[1].upper()
		return self.name[1].islower()

	def reserved(set=None):
		"""Set and get reserved_valid=True/invalid=False bit"""
		if set is True:
			self.name[2] = self.name[2].upper()
		elif set is False:
			self.name[2] = self.name[2].lower()
		return self.name[2].isupper()

	def safe_to_copy(set=None):
		"""Set and get save_to_copy=True/unsafe=False bit"""
		if set is True:
			self.name[3] = self.name[3].lower()
		elif set is False:
			self.name[3] = self.name[3].upper()
		return self.name[3].islower()

	def __repr__(self):
		return "<Chunk '{name}' length={length} crc={crc:08X}>".format(**self.__dict__)


class PNG(object):
	def __init__(self, data, ignore_errors=False):
		self.ignore_errors = ignore_errors
		self.data = data
		self.length = len(data)
		if data[0:8] != PNG_HEADER:
			msg = "No Valid PNG header"
			L.error(msg)
			if not self.ignore_errors: raise ValueError(msg)
		self.chunks = []
		self.parse()

	def parse(self):
		chunk_start = 8
		while chunk_start < self.length:
			chunk_end = chunk_start + struct.unpack("!I", self.data[chunk_start:chunk_start+4])[0] + 12
			L.debug("Processing chunk data {}-{}".format(chunk_start, chunk_end))
			chunk = Chunk(self.data[chunk_start:chunk_end], ignore_errors=self.ignore_errors)
			self.chunks.append(chunk)
			chunk_start = chunk_end

	def build(self):
		data = PNG_HEADER
		for chunk in self.chunks:
			data += chunk.build()
		return data

	def __repr__(self):
		return "<PNG length={length} chunks={}>".format(len(self.chunks), **self.__dict__)


if __name__ == "__main__":
	import argparse
	p = argparse.ArgumentParser(prog=PROG_NAME, description="Analyzes and edits PNG Chunks")
	p.add_argument("-i", "--ignore-errors", action="store_true", help="Ignore Length, Name and CRC errors")
	p.add_argument("file", metavar="FILE", type=argparse.FileType("rb"), help="Input file")
	args = p.parse_args()

	png = PNG(args.file.read(), ignore_errors=args.ignore_errors)

	print(png)
	for chunk in png.chunks:
		print("  ", chunk)
