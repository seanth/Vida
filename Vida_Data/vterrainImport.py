"""This file is part of Vida.
    --------------------------
    Copyright 2022, Sean T. Hammond
    
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

