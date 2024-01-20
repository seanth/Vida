#import sys
import os
import struct
#import argparse
#import osgeo.gdal
#import osgeo.osr
#from gdalconst import GDT_Int16, GDT_Float32
#import numpy as np


ifilename = "LakeTahoe.grid"
# check if input file available
if not os.path.isfile(ifilename):
    print("input file not found")
    sys.exit(3)
ifile = open(ifilename, "rb")   # open binary input file
idataset = ifile.read()         # read all data
print(idataset)
(cols, rows) = struct.unpack("2i", idataset[:8])
print(cols)
#(xul, ylr, xlr, yul) = struct.unpack("4f", idataset[8:24])
#psize = (xlr - xul) / cols  # pixel size