"""This file is part of Vida.
    --------------------------
    Copyright 2023, Sean T. Hammond
    
    Vida is experimental in nature and is made available as a research courtesy "AS IS," but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 
    
    You should have received a copy of academic software agreement along with Vida. If not, see <https://github.com/seanth/Vida/blob/master/LICENSE.txt>.
"""

from PIL import Image

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

    #situations where objects with negative coordinates get looped around
    theX = int(round(theX,0))
    if theX<0: theX=0
    if theX>=theImage[1][0]:theX=theImage[1][0]-1

    theY = int(round(theY,0))
    if theY<0: theY=0
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

def getPixelRange(theGarden):
    #the darkest and brightest pixel values in the (resized) terrain image.
    #Gardens saved before this was added don't have the attribute, so fall
    #back to the full 0-255 range, which reproduces the old behaviour
    #STH 2026-0923
    return getattr(theGarden, "terrainPixelRange", (0, 255))

def elevationFromPixel(thePixelValue, theElevDelta=-1, pixelRange=(0, 255)):
    #our scale in meters
    if theElevDelta == -1:
        maxValue = 50.0 #brightest pixel value
    else:
        maxValue = theElevDelta

    if type(thePixelValue) == tuple:
        #(14,14,14)
        thePixelValue = thePixelValue[0]

    #the darkest pixel in the image is elevation 0 (imin) and the brightest
    #pixel is maxValue ((imax-imin)*terrainScale). Previously pixel 0 and
    #pixel 255 were used, so images that did not use the full 0-255 range
    #had their terrain squashed toward the top or bottom
    #STH 2026-0923
    lowPixel = pixelRange[0]
    highPixel = pixelRange[1]
    if highPixel <= lowPixel:
        #a flat image
        return 0.0

    theFraction = (thePixelValue - lowPixel) / float(highPixel - lowPixel)
    #clamp. getPixelValue() returns 255 for out-of-range coordinates, which
    #can be brighter than the brightest pixel in the image
    if theFraction < 0.0:
        theFraction = 0.0
    if theFraction > 1.0:
        theFraction = 1.0

    theElevation = maxValue*theFraction
    return theElevation

