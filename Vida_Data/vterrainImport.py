from PIL import Image

def getPixelValue(x,y,theImage):
    #what pixel do you want to look at
    ###IMPORTANT: to convert from simulation coords to image coords need to add avlues
    ###If image is 100x100 and sim is 100x100, it's world size/2 to get what you add on
    ###This needs to be expanded more to adjust for different world sizes and 
    ###different image sizes
    ###STH & EKT 05 Feb 2020
    theX = x+50
    theY = y+50

    #convert the stored image data into something usable
    #format of theImage is [mode, size tuple, image as bytes] STH 0212-2020
    thePixelValue = Image.frombytes(theImage[0], theImage[1], theImage[2]).getpixel((theX,theY)) 
    #print thePixelValue

    ###NOTE: The problem with this is that it opens the file every time it needs to check for elevation
    ###It'd be better to open the file and save it in memory once. Do that in Vida.py around line 327
    #open the file
    #theImage = Image.open(inputFile)

    #how big is the file in width and height (pixels)
    #theWidth, theHeight = theImage.size
    #print "The width is: %i" % (theWidth)
    #print "The height is: %i" % (theHeight)

    #actually look at the pixel you want
    #thePixelValue = theGarden.terrainImage.getpixel((theX,theY))  
    ##a loaded image (loaded in vida.py) does not use the getPixel() method
    ##see https://pillow.readthedocs.io/en/4.0.x/reference/PixelAccess.html#pixelaccess
    #STH 0212-2020
    #thePixelValue = theImage[theX,theY]
    #print thePixelValue

    return thePixelValue

def elevationFromPixel(thePixelValue):
    #our scale in meters
    minValue = 0.0 #0 pixel value 
    maxValue = 10.0 #255 pixel value

    #use 255 here because we want to link the max greyscale value (255) to the maxValue (meters)
    theSlope = maxValue/255.0
    theElevation = theSlope*thePixelValue

    return theElevation

