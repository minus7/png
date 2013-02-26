import logging
L = logging.getLogger("PNG.filter")

filter_names = {
	0: "None",
	1: "Sub",
	2: "Up",
	3: "Average",
	4: "Paeth",
}

def decode(data, scanline_bytes):
	line_start = 0
	while line_start < len(data):
		filter_type = data[line_start]
		L.debug("Filter for line {} is {} ({})".format(
			line_start//scanline_bytes,
			filter_names.get(filter_type, "unknown"),
			filter_type)
		)
		line_start += scanline_bytes+1

def encode(data, scanline_bytes):
	out = b""
	lines = 0
	while len(out) - lines < len(data):
		out += b"\x00" + data[lines*scanline_bytes:lines*scanline_bytes + scanline_bytes]
		lines += 1
	return out
