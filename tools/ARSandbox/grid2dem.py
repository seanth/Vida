#!/usr/bin/env python
"""
    Convert SARnbox grid format to GDAL supported format
    (c) Zoltan Siki siki.zoltan@epito.bme.hu
    GPL 2

    Usage:
        python grid2dem.py input.grid [output.dem]
        or
        grid2dem.py input.grid [output.dem]

    Input file is a SARndbox binary grid file.
    Output file name is optional, default is the name of the input file.
    default output format is GTiff (if no output file given).

    Supported output data formats:
        Name                              Extension
        GTiff (GeoTiff single band)       tif
        USGSDEM (USGS DEM)                dem (integer values only)
        AAIGrid (ESRI ASCII GRID)         asc

    Notes:
    GDAL driver cannot direcly create USGSDEM file, only create copy available
    so a GTiff is created first, than a copy created
    GDAL USGSDEM driver supports int16 values only, so values are converted to int
    SRS for GTiff must be set for copycreate, we use UTM (false)
"""

import sys
import os
import struct
import argparse
import osgeo.gdal
import osgeo.osr
from gdalconst import GDT_Int16, GDT_Float32
import numpy as np

# GDAL extensions to driver name
gd_driver = {".tif": "GTiff",
             ".dem": "USGSDEM",
             ".asc": "AAIGrid"}
# Output data type
gd_of = {".tif": GDT_Float32,
         ".dem": GDT_Int16,
         ".asc": GDT_Float32}
# check create/copycreate
cc = []
for i in gd_driver:
    form = gd_driver[i]
    driver = osgeo.gdal.GetDriverByName(form)
    metadata = driver.GetMetadata()
    if osgeo.gdal.DCAP_CREATE in metadata and \
        metadata[osgeo.gdal.DCAP_CREATE] == 'YES':
        continue
    if osgeo.gdal.DCAP_CREATECOPY in metadata and \
        metadata[osgeo.gdal.DCAP_CREATECOPY] == 'YES':
        cc.append(i)
# check command line parameters
parser = argparse.ArgumentParser()
parser.add_argument("ifilename", type=str, help="input grid file")
parser.add_argument("ofilename", nargs="?", type=str, \
    help="output DEM file, optional", default="")
args = parser.parse_args()

if os.path.splitext(args.ifilename)[1] != ".grid":
    print("input file must be a .grid file")
    sys.exit(2)
# generate output file name if not given on the command line
if len(args.ofilename) == 0:
    args.ofilename = os.path.splitext(args.ifilename)[0] + ".tif"
# check output file type (extension)
oext = os.path.splitext(args.ofilename)[1]
if oext not in gd_driver:
    print("Unsupported output format")
    sys.exit(2)
if oext in cc:
    tmpext = ".tif"
    tmpfilename = os.path.splitext(args.ifilename)[0] + tmpext
else:
    tmpext = oext
    tmpfilename = args.ofilename
# check if input file available
if not os.path.isfile(args.ifilename):
    print("input file not found")
    sys.exit(3)
ifile = open(args.ifilename, "rb")   # open binary input file
idataset = ifile.read()         # read all data
(cols, rows) = struct.unpack("2i", idataset[:8])
(xul, ylr, xlr, yul) = struct.unpack("4f", idataset[8:24])
psize = (xlr - xul) / cols  # pixel size
if gd_of[oext] == GDT_Int16:
    # truncate data to int for gdal USGSDEM driver
    data = [int(d) for d in struct.unpack("f" * (rows * cols), idataset[24:])]
    gd_type = gd_of[oext]
    np_type = np.int16
else:
    data = struct.unpack("f" * (rows * cols), idataset[24:])    # elevations
    gd_type = gd_of[oext]
    np_type = np.float32
# create output (temperary geotiff in case of dem/asc)
driver = osgeo.gdal.GetDriverByName(gd_driver[tmpext])
if driver is None:
    print("Cannot get GDAL driver")
    sys.exit(4)
odataset = driver.Create(tmpfilename, cols, rows, 1, gd_type)
if odataset is None:
    print("Cannot create output GDAL dataset")
    sys.exit(4)
odataset.SetGeoTransform((xul, psize, 0, yul, 0, -psize))
if oext in cc:
    # set spatial reference system to (false) UTM
    srs = osgeo.osr.SpatialReference()
    srs.SetUTM(11, 1)
    srs.SetWellKnownGeogCS('NAD27')
    odataset.SetProjection(srs.ExportToWkt())
odataset.GetRasterBand(1).WriteArray(np.array(data, \
    dtype=np_type).reshape((rows, cols)))
odataset.FlushCache()
odataset = None
if oext in cc:
    # make a copy of tif to dem/asc
    src_ds = osgeo.gdal.Open(tmpfilename)
    driver = osgeo.gdal.GetDriverByName(gd_driver[oext])
    if driver is None:
        print("Cannot get %s driver" % gd_driver[oext])
        sys.exit(4)
    dst_ds = driver.CreateCopy(args.ofilename, src_ds, 0)
    src_ds = None
    dst_ds = None
    # remove temperary geotif file
    os.remove(tmpfilename)