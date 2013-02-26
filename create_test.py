#!/usr/bin/env python3

from png import PNG, chunks, filter

WIDTH = HEIGHT = 50

data = WIDTH * HEIGHT * bytes([255, 0, 0])

p = PNG()
p.chunks.append(chunks.IHDR(width=WIDTH, height=HEIGHT))
p.chunks.append(chunks.IDAT(uncompressed_data=filter.encode(data, WIDTH*3)))
p.chunks.append(chunks.IEND())

with open("/tmp/test.png", "wb") as f:
	f.write(p.dump())
