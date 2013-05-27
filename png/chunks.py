import struct
import zlib
import string

import logging
L = logging.getLogger("PNG.chunks")

class Chunk(object):
	"""Represents any PNG Chunk

	A chunk consists of an unsigned 31-bit length field (network order),
	followed by a 4-byte chunk name, followed by the data and a CRC32 of
	the name field and data. The name must be in A-Za-z.

	See:
	http://www.libpng.org/pub/png/spec/1.2/PNG-Structure.html#Chunk-layout
	http://www.libpng.org/pub/png/spec/1.2/PNG-Structure.html#Chunk-naming-conventions
	"""
	def __init__(self, name=None, data=None, ignore_errors=False):
		"""
		data is either the complete chunk including header & footer
		or just the payload (or None) if name is set
		"""
		self.ignore_errors = ignore_errors
		self.length = 0
		self.crc = 0
		self.name = name if name else "noNe"
		self.data = data if data else b""

	@classmethod
	def load(cls, data):
		"""Load a chunk including header and footer"""
		inst = cls()
		if len(data) < 12:
			msg = "Chunk-data too small"
			L.error(msg)
			raise ValueError(msg)

		# chunk header & data
		(inst.length, raw_name) = struct.unpack("!I4s", data[0:8])
		inst.data = data[8:-4]
		inst.verify_length()
		inst.name = raw_name.decode("ascii")
		inst.verify_name()

		# chunk crc
		inst.crc = struct.unpack("!I", data[8+inst.length:8+inst.length+4])[0]
		inst.verify_crc()

		return inst

	def dump(self, auto_crc=True, auto_length=True):
		"""Return the chunk including header and footer"""
		if auto_length: self.update_length()
		if auto_crc: self.update_crc()
		self.verify_name()
		return struct.pack("!I", self.length) + self.get_raw_name() + self.data + struct.pack("!I", self.crc)

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
		calculated_crc = self.get_crc()
		if self.crc != calculated_crc:
			msg = "CRC mismatch: {:08X} (header), {:08X} (calculated)".format(self.crc, calculated_crc)
			L.warning(msg)
			if not self.ignore_errors: raise ValueError(msg)
			return False
		return True

	def update_length(self):
		self.length = len(self.data)

	def update_crc(self):
		self.crc = self.get_crc()

	def get_crc(self):
		return zlib.crc32(self.get_raw_name() + self.data)

	def get_raw_name(self):
		return self.name if isinstance(self.name, bytes) else self.name.encode("ascii")

	# name helper methods

	def ancillary(self, set=None):
		"""Set and get ancillary=True/critical=False bit"""
		if set is True:
			self.name[0] = self.name[0].lower()
		elif set is False:
			self.name[0] = self.name[0].upper()
		return self.name[0].islower()

	def private(self, set=None):
		"""Set and get private=True/public=False bit"""
		if set is True:
			self.name[1] = self.name[1].lower()
		elif set is False:
			self.name[1] = self.name[1].upper()
		return self.name[1].islower()

	def reserved(self, set=None):
		"""Set and get reserved_valid=True/invalid=False bit"""
		if set is True:
			self.name[2] = self.name[2].upper()
		elif set is False:
			self.name[2] = self.name[2].lower()
		return self.name[2].isupper()

	def safe_to_copy(self, set=None):
		"""Set and get save_to_copy=True/unsafe=False bit"""
		if set is True:
			self.name[3] = self.name[3].lower()
		elif set is False:
			self.name[3] = self.name[3].upper()
		return self.name[3].islower()

	def __str__(self):
		return "<Chunk '{name}' length={length} crc={crc:08X}>".format(**self.__dict__)


class IHDR(Chunk):
	"""IHDR Chunk
	width, height, bit_depth, color_type, compression_method,
	filter_method, interlace_method contain the data extracted
	from the chunk. Modify those and use and build() to recreate
	the chunk. Valid values for bit_depth depend on the color_type
	and can be looked up in color_types or in the PNG specification

	See:
	http://www.libpng.org/pub/png/spec/1.2/PNG-Chunks.html#C.IHDR
	"""
	# color types with name & allowed bit depths
	COLOR_TYPE_GRAY  = 0
	COLOR_TYPE_RGB   = 2
	COLOR_TYPE_PLTE  = 3
	COLOR_TYPE_GRAYA = 4
	COLOR_TYPE_RGBA  = 6
	color_types = {
		COLOR_TYPE_GRAY:	("Grayscale", (1,2,4,8,16)),
		COLOR_TYPE_RGB:		("RGB", (8,16)),
		COLOR_TYPE_PLTE:	("Palette", (1,2,4,8)),
		COLOR_TYPE_GRAYA:	("Greyscale+Alpha", (8,16)),
		COLOR_TYPE_RGBA:	("RGBA", (8,16)),
	}

	def __init__(self, width=0, height=0, bit_depth=8, color_type=2, \
	             compression_method=0, filter_method=0, interlace_method=0, \
	             ignore_errors=False):
		self.width = width
		self.height = height
		self.bit_depth = bit_depth
		self.color_type = color_type
		self.compression_method = compression_method
		self.filter_method = filter_method
		self.interlace_method = interlace_method
		super().__init__("IHDR", ignore_errors=ignore_errors)

	@classmethod
	def load(cls, data):
		inst = super().load(data)
		fields = struct.unpack("!IIBBBBB", inst.data)
		inst.width = fields[0]
		inst.height = fields[1]
		inst.bit_depth = fields[2] # per channel
		inst.color_type = fields[3] # see specs
		inst.compression_method = fields[4] # always 0(=deflate/inflate)
		inst.filter_method = fields[5] # always 0(=adaptive filtering with 5 methods)
		inst.interlace_method = fields[6] # 0(=no interlace) or 1(=Adam7 interlace)
		return inst

	def dump(self):
		self.data = struct.pack("!IIBBBBB", \
			self.width, self.height, self.bit_depth, self.color_type, \
			self.compression_method, self.filter_method, self.interlace_method)
		return super().dump()

	def __str__(self):
		return "<Chunk:IHDR geometry={width}x{height} bit_depth={bit_depth} color_type={}>" \
			.format(self.color_types[self.color_type][0], **self.__dict__)


class IDAT(Chunk):
	"""IDAT Chunk
	The main pixel data storage, contains mad science.
	This implementation only supports (de)compressing and does
	not handle anything further of the PNG specification.

	See:
	http://www.libpng.org/pub/png/spec/1.2/PNG-Chunks.html#C.IDAT
	"""

	def __init__(self, data=None, uncompressed_data=None, ignore_errors=False):
		super().__init__("IDAT", data, ignore_errors=ignore_errors)
		if uncompressed_data:
			self.compress(uncompressed_data)

	def compress(self, data, level=9):
		self.data = zlib.compress(data, level)

	def decompress(self):
		return zlib.decompress(self.data)

	def __str__(self):
		return "<Chunk:IDAT length={length} crc={crc:08X}>".format(**self.__dict__)


class IEND(Chunk):
	"""IEND Chunk
	Marks the end of the PNG stream.

	See:
	http://www.libpng.org/pub/png/spec/1.2/PNG-Chunks.html#C.IEND
	"""

	def __init__(self, ignore_errors=False):
		super().__init__("IEND", ignore_errors=ignore_errors)

	def dump(self):
		if len(self.data) != 0:
			msg = "IEND has data which is not allowed"
			L.error(msg)
			if not self.ignore_errors: raise ValueError(msg)
		if self.length != 0:
			msg = "IEND data lenght is not 0 which is not allowed"
			L.error(msg)
			if not self.ignore_errors: raise ValueError(msg)
		return super().dump()

	def __str__(self):
		return "<Chunk:IEND>".format(**self.__dict__)
