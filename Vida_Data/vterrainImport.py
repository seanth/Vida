"""This file is part of Vida.
    --------------------------
    Copyright 2023, Sean T. Hammond
    
    Vida is experimental in nature and is made available as a research courtesy "AS IS," but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 
    
    You should have received a copy of academic software agreement along with Vida. If not, see <https://github.com/seanth/Vida/blob/master/LICENSE.txt>.
"""

from PIL import Image

import os
import glob
import sys

import rioxarray as rxr #pip install rioxarray #https://pypi.org/project/rioxarray/
import numpy #pip install numpy #https://pypi.org/project/numpy/

def getPixelValue(x,y,theImage):
    #what pixel do you want to look at
    ###IMPORTANT: to convert from simulation coords to image coords need to add avlues
    ###If image is 100x100 and sim is 100x100, it's world size/2 to get what you add on
    ###This needs to be expanded more to adjust for different world sizes and 
    ###different image sizes
    ###STH & EKT 05 Feb 2020
    #theX = x+50.0
    #theY = y+50.0
    theX = x
    theY = y

    theX = int(round(theX,0))
    if theX>=theImage[1][0]:theX=theImage[1][0]-1
    theY = int(round(theY,0))
    if theY>=theImage[1][1]:theY=theImage[1][1]-1

    #convert the stored image data into something usable
    #format of theImage is [mode, size tuple, image as bytes] STH 0212-2020
    #it is possible that an x or y value will be sent that is out of index for the image.
    #if that happens, assign it a default value
    try:
        thePixelValue = Image.frombytes(theImage[0], theImage[1], theImage[2]).getpixel((theX,theY)) 
    except IndexError:
        thePixelValue = 255
    except ValueError:
        thePixelValue = 255

    return thePixelValue

def elevationFromPixel(thePixelValue, theElevDelta=-1):
    #our scale in meters
    minValue = 0.0 #0 pixel value 
    if theElevDelta == -1:
        maxValue = 50.0 #255 pixel value
    else:
        maxValue = theElevDelta

    #use 255 here because we want to link the max greyscale value (255) to the maxValue (meters)
    theSlope = maxValue/255.0
    if type(thePixelValue) == tuple:
        #(14,14,14)
        thePixelValue = thePixelValue[0]

    theElevation = theSlope*thePixelValue
    return theElevation


def importDEMtoPILImage(theFile):
    #theFile = "mydem.dem"
    readData = rxr.open_rasterio(theFile)

    ##this gets the elevation values
    theArray = readData.values[0]
    # theImage=Image.fromarray(theArray)
    # theImage.save("tester.tiff")
    # return theImage
    fillValue = readData._FillValue
    theArray[theArray == fillValue] = numpy.nan
    absMax = numpy.nanmax(theArray)
    absMin = numpy.nanmin(theArray)
    #theArray = (theArray+7).astype('uint8')
    #theArray = (theArray+abs(absMin))
    theArray = ((theArray - absMin) * (1/(absMax - absMin) * 255)).astype('uint8')

    theImage=Image.fromarray(theArray)
    theImage.save("tester.tiff")

    return theImage,absMin,absMax

    # ##check and see if the array is a square
    # dimX = theArray.shape[0]
    # dimY = theArray.shape[1]
    # print("The array is %i x %i" % (dimX, dimY))
    # if dimX != dimY:
    #     print("The array is not a square")
    #     minDimension = min(dimX,dimY)
    #     #minDimension = 26 #for testing only
    #     print("Resizing the array")
    #     theArray = numpy.resize(theArray, (minDimension,minDimension))
    # dimX = theArray.shape[0]
    # dimY = theArray.shape[1]
    # print("The array is %i x %i" % (dimX, dimY))


    # ###The file will have a default value it uses to fill in null values
    # fillValue = readData._FillValue


    # ###############
    # ###Do I actually need to flatten it first?
    # flatArray = theArray.flatten()

    # ####Replace all the 'no data' values
    # ###First replace them with 'nan'
    # ###Go through and mind actual min ignoring nan
    # ###Then replace all nan with actual min values
    # flatArray[flatArray == fillValue] = numpy.nan
    # actualMin = numpy.nanmin(flatArray)
    # flatArray = numpy.nan_to_num(flatArray, nan=actualMin)

    # ###Now normalize the array. min 0, max 255 (like greyscale pixels)
    # flatArray = ((flatArray - flatArray.min()) * (1/(flatArray.max() - flatArray.min()) * 255)).astype('uint8')

    # ##set the array back to the original matrix shape
    # theArray = numpy.reshape(flatArray, (dimX,dimY))

    # ##cleanup
    # readData = None
    # tmp = None
    # flatArray = None

    # return theArray


#####moved from Vida.py
#####STH 2024-0124
def importTerrainFromFile(terrainFile, absMax, absMin, terrainScale, theGarden):
    ####################################
    ###terrain files can either be DEM files or TIFF images
    imageSuffixList = ['.tiff','.tif']
    otherSuffixList = ['.dem']
    fileSuffixList = imageSuffixList + otherSuffixList
    if terrainFile!=None:
        #only print at startup, not during event file insertion
        if theGarden.cycleNumber<1: print("***Checking for terrain file...***") 
        if os.path.isfile(terrainFile) == True:
            theFileSuffix = os.path.splitext(terrainFile)[1]
            if (theFileSuffix in fileSuffixList):
                theTerrainFile = terrainFile
                tiffFound = True
                #only print at startup, not during event file insertion
                if theGarden.cycleNumber<1: print("      terrain file found") 
            else:
                #only print at startup, not during event file insertion
                if theGarden.cycleNumber<1: print("      Terrain file not found. Skipping terrain import") 
                tiffFound = False 
                return theGarden
        #reworked checking for file types in a directory
        #STH 23 Sept 2020
        #needs to be extended to also grab .dem files STH 2024-0123
        elif os.path.isdir(terrainFile) == True:
            print("***Checking directory for tif terrain image...***")
            tmpPath = os.path.join(terrainFile,'*.tif') #assumes file suffix is 'tif'
            matchFiles = glob.glob(tmpPath)
            #print matchFiles
            if not matchFiles:
                #no matching files found
                tiffFound = False
            else:
                theTerrainFile = matchFiles[0] #no matter what, grab the first item in the list
                if len(matchFiles)==1:
                    print("      Tif file found")
                else:
                    print("      Multiple tif files found. Using:")
                    print("       %s" % os.path.basename(theTerrainFile))
                theFileSuffix = os.path.splitext(theTerrainFile)[1]
                tiffFound = True
        else:
            #only print at startup, not during event file insertion
            if theGarden.cycleNumber<1: print("      Terrain file not found. Skipping terrain import")
            tiffFound = False 
            return theGarden

        if tiffFound == True:
            #########################################################################
            from PIL import Image, ImageOps
            #if type(eventFile)==file:
            if theGarden.cycleNumber<1: print("***Loading terrain file:\n     %s***" % (theTerrainFile))
            #theImage = Image.open(terrainFile)

            if theFileSuffix in otherSuffixList:
                #opens up the dem and coverts the array as a PIL image object
                tmp,absMin,absMax=importDEMtoPILImage(theTerrainFile)
            if theFileSuffix in imageSuffixList:
                tmp=Image.open(theTerrainFile)

            tmp=ImageOps.flip(tmp)

            #format of terrainImage is [mode, size tuple, image as bytes] STH 0212-2020
            #make sure the list is the correct length
            if len(theGarden.terrainImage)<3:
                theGarden.terrainImage=[0]*3

            #store the image mode
            theGarden.terrainImage[0]=tmp.mode

            #the imported image might not be a square. 
            #If it is not a square, trim it
            #STH 2021-06-28
            if tmp.size[0]!=tmp.size[1]:
                if tmp.size[0]<tmp.size[1]:
                    smallestDim = tmp.size[0]
                else:
                    smallestDim = tmp.size[1]
                if theGarden.cycleNumber<1: 
                    print("***WARNING: imported image is not square.")
                    print("      Size is: %s x %s" % (tmp.size[0], tmp.size[1]))
                    print("      Truncating image to %ix%i..." % (smallestDim, smallestDim))
                tmp=tmp.crop((0, 0, smallestDim, smallestDim))

            #if the imported image is not the same size as the world size, change it
            #this assumes the image is a square
            #STH 2021-0628

            if tmp.size[1] != theGarden.theWorldSize:
                if theGarden.cycleNumber<1:  
                    print("***WARNING: imported image is not the same size as the world space.")
                    print("      Size is: %s x %s" % (tmp.size[0], tmp.size[1]))
                    print("      Resizing image to %ix%i..." % (theGarden.theWorldSize, theGarden.theWorldSize))
            tmp=tmp.resize((theGarden.theWorldSize,theGarden.theWorldSize))
            
            #store the image size
            theGarden.terrainImage[1]=tmp.size
            
            #store the image as bytes
            theGarden.terrainImage[2]=tmp.tobytes()
            tmp.close()
            tmp=None
            #########################################################################
            if os.path.isdir(terrainFile) == True:
                #Now look for a .xlsx file 
                #.xlsx files have headers of six lines, followed by tabular data
                #ET addition 9-15-2020
                print("***Checking directory for xlsx terrain data...***")
                tmpPath = os.path.join(terrainFile,'*.xlsx') #assumes file suffix is 'xlsx'
                matchFiles = glob.glob(tmpPath)
                if matchFiles:
                    #9/28/2020 ET-test of default absMax and absMin values from vida.ini                                
                    theExcelFile = matchFiles[0] #no matter what, grab the first item in the list
                    if len(matchFiles)==1:
                        print("      xlsx file found")
                    else:
                        print("      Multiple xlsx files found. Using:")
                        print("       %s" % os.path.basename(theExcelFile))

                    import pandas
                    fileData = pandas.read_excel(theExcelFile, header=None)
                    #each row in the header will have a single value
                    #but we're not entirely sure exactly what cell the value will be in
                    #STH 2023-0302
                    #this too a while to figure out, so I'm explaining to future me:
                    #I'm getting the row (index starts 0), and then excluding the
                    #first value on the row. Then getting the max value in that 
                    #remaining row. STH 2023-0302
                    theNCols = fileData.iloc[1][1:].max()
                    theNRows = fileData.iloc[2][1:].max()
                    theCellSize = fileData.iloc[5][1:].max()
                    print("        ncols: %s" % theNCols)
                    print("        nrows: %s" % theNRows)
                    print("        cellsize: %s" % theCellSize)
                    
                    #use the smaller axis to calculate the scaling based on
                    #number of cells and cellsize
                    if theNCols<theNRows:
                        theScaledDistance = theCellSize*theNCols
                    else:
                        theScaledDistance = theCellSize*theNRows
                    terrainScale=theWorldSize/theScaledDistance

                    #sometimes there columns of NaN beyond the defined column max
                    fileData = fileData.drop(theNCols, axis=1)

                    #trim off those first few rows
                    fileData = fileData.tail(-7)

                    #make sure all the values are numbers
                    fileData = fileData.astype(float)

                    allMaxForEachColumn = fileData.max()
                    absMax = allMaxForEachColumn.max()

                    allMinForEachColumn = fileData.min()
                    absMin = allMinForEachColumn.min()

                else:
                    print("***xlsx terrain data terrain data not found. Using default values***")

            theMaxElevation = absMax-absMin
            theMaxElevation = theMaxElevation*terrainScale
            theGarden.maxElevation = theMaxElevation    
            if theGarden.cycleNumber<1: 
                print("      absMax: %s" % absMax)
                print("      absMin: %s" % absMin)
                print("      terrainScale: %s" % terrainScale)
                print("      scaled max: %s" % (theMaxElevation))
            return theGarden
    ####################################

