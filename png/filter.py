import math, io
import logging
L = logging.getLogger("PNG.filter")

filter_names = {
	0: "None",
	1: "Sub",
	2: "Up",
	3: "Average",
	4: "Paeth",
}

def decode(data, width, bpp):
	line_start = 0
	scanline_bytes = math.ceil(width*bpp/8)
	bytes_per_pixel = math.ceil(bpp/8)
	outbuf = io.BytesIO()
	prev_line_data = b"\x00"*scanline_bytes
	while line_start < len(data):
		filter_type = data[line_start]
		L.debug("Filter for line {} is {} ({})".format(
			line_start//scanline_bytes,
			filter_names.get(filter_type, "unknown"),
			filter_type)
		)

		outlinebuf = io.BytesIO()
		line_data = data[line_start+1:line_start+1+scanline_bytes]

		# Filters
		if filter_type == 0: # None
			outlinebuf.write(line_data)
		elif filter_type == 1: # Sub
			for start in range(len(line_data)):
				if start < bytes_per_pixel:
					outlinebuf.write(bytes([line_data[start]]))
				else:
					outlinebuf.write(bytes([line_start[start] + line_data[start - bytes_per_pixel]]))
		elif filter_type == 2: # Up
			for start in range(len(line_data)):
				outlinebuf.write(bytes([line_data[start] + prev_line_data[start]]))
		elif filter_type == 3: # Average
			for start in range(len(line_data)):
				if start < bytes_per_pixel:
					outlinebuf.write(bytes([line_data[start] + prev_line_data[start]]))
				else:
					outlinebuf.write(bytes([line_start[start] + (line_data[start - bytes_per_pixel] + prev_line_data[start])//2]))
		elif filter_type == 4: # Paeth
			def paeth(a, b, c):
				p = a+b-c
				pa = abs(p - a)
				pb = abs(p - b)
				pc = abs(p - c)
				if pa <= pb and pa <= pc: return a
				if pb <= pc: return b
				return c
			for start in range(len(line_data)):
				if start < bytes_per_pixel:
					outlinebuf.write(bytes([(line_data[start] + paeth(0, prev_line_data[start], 0))&0xff]))
				else:
					outlinebuf.write(bytes([(line_data[start] + paeth(line_data[start - bytes_per_pixel], prev_line_data[start], prev_line_data[start - bytes_per_pixel]))&0xff]))
		outlinebuf.seek(0)
		prev_line_data = outlinebuf.read()
		outbuf.write(prev_line_data)
		line_start += scanline_bytes+1
	outbuf.seek(0)
	return outbuf.read()

def encode(data, scanline_bytes, force_filter=None):
	out = b""
	lines = 0
	while len(out) - lines < len(data):
		out += b"\x00" + data[lines*scanline_bytes:lines*scanline_bytes + scanline_bytes]
		lines += 1
	return out
