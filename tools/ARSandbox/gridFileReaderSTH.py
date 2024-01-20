import struct
import sys


def readFloatingPoint(theFileData):
    x = theFileData.read(4)
    theFloat= struct.unpack('f', x)[0]
    return theFloat

def readLittleEndian(fileIn):
    return struct.unpack('<i', fileIn.read(4))[0]

def readGridFile(gridfile):
    theFile = sys.argv[1]
    theFileData = open(gridfile, 'rb')
    # The first 6 values are little-endian 4-byte numbers indicating grid size and geometric bounds
    theDimensions = tuple([readLittleEndian(theFileData) for _ in range(2)])
    print("rows: %i" % theDimensions[0])
    print("columns: %i" % theDimensions[1])
    if theDimensions[0]!=theDimensions[1]: 
        print("***Grid file is not square truncating")
        theMinSize=min(theDimensions)
        print("     grid truncated to %i by %i\n" % (theMinSize, theMinSize))
        print("rows: %i" % theMinSize)
        print("columns: %i\n" % theMinSize)
        rows=theMinSize
        cols=theMinSize
    y = tuple([readFloatingPoint(theFileData) for _ in range(4)])
    leftedge, bottomedge, rightedge, topedge = y
    #print(theDimensions,y)
    fulldata = []
    minElevation=-99999999999  
    # try:
    for r in range(theMinSize):
        rowData = []
        for c in range(theMinSize):
            aDataPoint = readFloatingPoint(theFileData)
            rowData.append(aDataPoint)
            # TODO the error check below doesnt work because bounds are signed and depth is unsigned (and relative?)
            # if min(rowData) < bottomedge or max(rowData) > topedge:
            #    raise Exception("Grid data exceeds grid bounds at row, column:", r, c)
        # if len(rowData) != cols:
        #     raise Exception("Grid data is incomplete at row, column:", r, c)
        fulldata.append(rowData)
    print(min([min(x) for x in fulldata]))
    sys.exit()
    # if len(fulldata) != rows:
    #     raise Exception("Grid data is incomplete at row, column:", r, c)
    # except Exception as e:
    #     print("")
    #     #print(fulldata)
    #     #print(e)
    #     #print(theFileData.read(4).encode('hex'))
    return rows, cols, leftedge, bottomedge, rightedge, topedge, fulldata

if __name__ == "__main__":
    filename = sys.argv[1]
    rows, cols, leftedge, bottomedge, rightedge, topedge, fulldata = readGridFile(filename)
    #print(len(fulldata))