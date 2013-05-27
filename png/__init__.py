PNG_HEADER = b"\x89PNG\r\n\x1a\n"

import struct
import logging
L = logging.getLogger("PNG.png")

from . import chunks, filter



chunk_map = {
	#None: chunks.Chunk,
	b"IHDR": chunks.IHDR,
	#"PLTE": chunks.PLTE,
	b"IDAT": chunks.IDAT,
	b"IEND": chunks.IEND,
}


class PNG(object):
	def __init__(self, ignore_errors=False):
		self.ignore_errors = ignore_errors
		self.data = b""
		self.length = 0
		self.chunks = []

	@staticmethod
	def load(data, ignore_errors=False):
		inst = PNG(ignore_errors=ignore_errors)
		inst.data = data
		inst.length = len(data)
		if data[0:8] != PNG_HEADER:
			msg = "No Valid PNG header"
			L.error(msg)
			if not ignore_errors: raise ValueError(msg)

		chunk_start = 8
		while chunk_start < inst.length:
			(chunk_length, chunk_name) = struct.unpack("!I4s", data[chunk_start:chunk_start+8])
			chunk_end = chunk_start + chunk_length + 12
			L.debug("Processing {} chunk data {}-{}".format(chunk_name, chunk_start, chunk_end))
			chunk = chunk_map.get(chunk_name, chunks.Chunk).load(data[chunk_start:chunk_end])
			L.debug("New chunk: {}".format(chunk))
			inst.chunks.append(chunk)
			chunk_start = chunk_end

		return inst

	def dump(self):
		data = PNG_HEADER
		for chunk in self.chunks:
			data += chunk.dump()
		return data

	def __str__(self):
		return "<PNG length={length} chunks={}>".format(len(self.chunks), **self.__dict__)
