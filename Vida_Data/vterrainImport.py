from PIL import Image

def getPixelValue(x,y):
    #what pixel do you want to look at
    ###IMPORTANT: to convert from simulation coords to image coords need to add avlues
    ###If image is 100x100 and sim is 100x100, it's world size/2 to get what you add on
    ###This needs to be expanded more to adjust for different world sizes and 
    ###different image sizes
    ###STH & EKT 05 Feb 2020
    theX = x+50
    theY = y+50

    #where is the file, and what is it named?
    inputFile = "Vida_Data/smoltest.tif"

    ###NOTE: The problem with this is that it opens the file every time it needs to check for elevation
    ###It'd be better to open the file and save it in memory once. Do that in Vida.py around line 327
    #open the file
    theImage = Image.open(inputFile)

    #how big is the file in width and height (pixels)
    theWidth, theHeight = theImage.size
    #print "The width is: %i" % (theWidth)
    #print "The height is: %i" % (theHeight)



    #actually look at the pixel you want
    thePixelValue = theImage.getpixel((theX,theY)) 
    #print "The pixel value: %i" % thePixelValue

    #our scale
    #in meters
    minValue = 0.0 #0 pixel value 
    maxValue = 10.0 #255 pixel value

    #use 255 here because we want to link the max greyscale value (255) to the maxValue (meters)
    theSlope = maxValue/255.0
    #print "The slope of the line: is %f" % theSlope

    theElevation = theSlope*thePixelValue
    #print "The elevation is: %f meters" % theElevation

    return theElevation

    # #our scale
    # #in meters
    # minValue = 0.0 #0 pixel value 
    # maxValue = 10.0 #255 pixel value

    # #print minValue
    # #print maxValue

    # #use 255 here because we want to link the max greyscale value (255) to the maxValue (meters)
    # theSlope = maxValue/255.0
    # print "THe slope of the line: is %f" % theSlope

    # theElevation = theSlope*thePixel
    # print "The elevation is: %f meters" % theElevation

    # #for fun, write the data to a csv file
    # outputFileName = "test.csv"
    # outputFile = open(outputFileName, 'w')
    # print >> outputFile, "%s, %s, %s" % ("x", "y", "z")


    # for x in xrange(theWidth):
    #     for y in xrange(theHeight):
    #         thePixel = theImage.getpixel((x,y))
    #         theElevation = theSlope*thePixel
    #         print "X,Y,Z: %i, %i, %f" % (x, y, theElevation)
    #         print >> outputFile, "%i, %i, %f" % (x, y, theElevation)

    # outputFile.close()