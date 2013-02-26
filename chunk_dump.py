#!/usr/bin/env python3

PROG_NAME = "PNG Chunk Dump"

from png import PNG
import argparse

import logging

p = argparse.ArgumentParser(prog=PROG_NAME, description="Analyzes and edits PNG Chunks")
p.add_argument("-i", "--ignore-errors", action="store_true", help="Ignore Length, Name and CRC errors")
p.add_argument("-v", "--verbose", action="store_const", default=logging.INFO, const=logging.DEBUG, help="be more verbose")
p.add_argument("file", metavar="FILE", type=argparse.FileType("rb"), help="Input file")
args = p.parse_args()

logging.basicConfig(format="[%(asctime)s] %(levelname)s: %(message)s", level=args.verbose)

png = PNG.load(args.file.read(), ignore_errors=args.ignore_errors)

print(png)
for chunk in png.chunks:
	print(">", chunk)
