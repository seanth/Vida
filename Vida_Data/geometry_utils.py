"""This file is part of Vida.
--------------------------
Copyright 2009, Sean T. Hammond

Vida is experimental in nature and is made available as a research courtesy "AS IS," but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 

You should have received a copy of academic software agreement along with Vida. If not, see <http://iorek.ice-nine.org/seant/Vida/license.txt>.
"""

import math

#Import Psyco if possible
try:
	import psyco
	psyco.log()
	psyco.full()
except ImportError:
	pass

def checkOverlap(x, y, r, xx, yy, rr):
	return circleOverlap(x,y,r,xx,yy,rr)
	
def python_circle_circle_overlap(x,y,r,xx,yy,rr):
	theDistance =distBetweenPoints(x, y, xx, yy)
	###now look at the distance in relation to the radii
	if theDistance>(r+rr):
		###no overlap
		return 0
	elif theDistance<(math.fabs(r-rr)):
		###complete overlap
		return 1
	else:
		###partial overlap
		return 2
		
#####look and see if there is a special C version
try:
	import circtest
	circleOverlap = circtest.circle_circle_overlap
	print "*********Will use gib's code**************"
except ImportError:
	circleOverlap = python_circle_circle_overlap
	print "*********Will use straight python*********"
	pass

def placePointsInGrid(numbPoints, lengthSquareSide):
	###assumes the area is a square
	distance= lengthSquareSide/(1.0+math.sqrt(numbPoints))
	return distance

def distBetweenPoints(x0, y0, x1, y1):
	dx=x0-x1
	dy=y0-y1
	theDistance=math.hypot(dx,dy)
	return theDistance

def areaCircle(radius):
	#area=math.pi*math.pow(radius, 2)
	area=3.14*radius*radius
	return area

def radiusCircle(area):
	#radius=math.sqrt(area/math.pi)
	radius=math.sqrt(area/3.14)
	return radius

def areaTriangle(distToRadical, lengthRadicalLine):
	area=2.0*0.5* distToRadical* lengthRadicalLine
	return area

def areaRectangle(rectSides):
	dx=math.fabs(rectSides[1]-rectSides[0])
	dy=math.fabs(rectSides[3]-rectSides[2])
	area=dx*dy
	return area

def areaSector(radius, radians):
	area=0.5*math.pow(radius, 2)*radians
	return area

def boundCircle(x, y, r):
	###return the [xMin, xMax, yMin, yMax] of a box bounding a circle
	xMin=x-r
	xMax=x+r
	yMin=y-r
	yMax=y+r
	return [xMin, xMax, yMin, yMax]

#def checkOverlap(x, y, r, xx, yy, rr): 
#	if useCforCheckingOverlap==False:
#		theDistance =distBetweenPoints(x, y, xx, yy)
#		###now look at the distance in relation to the radii
#		if theDistance>(r+rr):
#			###no overlap
#			return 0
#		elif theDistance<(math.fabs(r-rr)):
#			###complete overlap
#			return 1
#		else:
#			###partial overlap
#			return 2
#	else:
#		theReturn=circtest.circle_circle_overlap(x,y,r,xx,yy,rr)
#		return theReturn

def checkOverlapSquare(x, y, r, xx, yy, size):
	#x,y,r are the plant
	#xx, yy, size are the square
	halfSize=size/2.0
	if x<=xx+halfSize and x>=xx-halfSize:
		return 1

def pointInsideCircle(circX, circY, circR, pointX, pointY):
	###accepts the x,y and r of a circle and an x,y point
	###return whether the x,y point is in the circle
	theDistance=distBetweenPoints(circX, circY, pointX, pointY)
	if theDistance<=circR:
		return 1
	else:
		return 0
		
def pointInsideSquare(squareX, squareY, squareSize,pointX, pointY):
		##returns 1 if out of bounds
		##returns 0 if in bounds
		maxSquareX=squareX+(squareSize/2.0)
		minSquareX=squareX-(squareSize/2.0)
		maxSquareY=squareY+(squareSize/2.0)
		minSquareY=squareY-(squareSize/2.0)		
		if pointX<=maxSquareX and pointX>=minSquareX and pointY<=maxSquareY and pointY>=minSquareY:
			return 1
		else:
			return 0

		

def distToRadical(r0, r1, distance):
	###Send it radius of circle 1, radius circle 2, distance between the two circles
	###returns a list in format:[distance from circle 1 to radical, distance from circle 2 to radical] 
	d0=(math.pow(r0,2)-math.pow(r1,2)+math.pow(distance, 2))/(2*distance)
	d1=(math.pow(r1,2)-math.pow(r0,2)+math.pow(distance, 2))/(2*distance)
	radicalDistances=[]
	radicalDistances.append(d0)
	radicalDistances.append(d1)
	return radicalDistances

def lengthRadicalLine(r0, distToRadical):
	halfRadicalLine=math.pow((math.pow(r0,2)-math.pow(distToRadical,2)),0.5)
	return halfRadicalLine*2

def radiansSector(distance, radius):
	radians=math.acos(distance/radius)*2.0
	return radians



def areaThumbnail(areaSector, areaTriangle):
	area=areaSector-areaTriangle
	return area

def areaOverlappingCircles(x, y, r, xx, yy, rr):
				###get the distance between the two plants
				#if debug2==1:print "          Plant one radius x y: %f, %f, %f" % (r, x,  y)
				#if debug2==1:print "          Plant two radius x y: %f, %f, %f" % (rr, xx, yy)
				theDistance =distBetweenPoints(x, y, xx, yy)
				#if debug2==1:print "               Distance is: %f" % (theDistance)
				###now look at the distance in relation to the radii
				if theDistance>(r+rr):
					###no overlap
					#if debug2==1:print "               No overlap"
					areaOverlap=0.0
				elif theDistance<(math.fabs(r-rr)):
					###one plant is completely covered
					#if debug2==1:print "          %s(%f) completely covered by %s(%f)." % ("circle 1", r, "circle 2", rr)
					#areaOverlap=math.pi*math.pow(r,2.0)
					areaOverlap=3.14*r*r
				else:
					###there is partial overlap
					#if debug2==1:print "          %s(%f) partly covered by %s(%f)." % ("circle 1", r, "circle 2", rr)
					theDistanceToRadical= distToRadical(r, rr, theDistance)
					circleOneDistToRadical= theDistanceToRadical[0]
					circleTwoDistToRadical= theDistanceToRadical[1]
					#if debug2==1:print "          plant one distance to radical: %f" % (circleOneDistToRadical)
					#if debug2==1:print "          plant two distance to radical: %f" % (circleTwoDistToRadical)
					theLengthRadicalLine=lengthRadicalLine(r, circleOneDistToRadical)
					#if debug2==1:print "          length radical line: %f" % (theLengthRadicalLine)
					radiansCircleOneSector= radiansSector(circleOneDistToRadical, r)
					radiansCircleTwoSector= radiansSector(circleTwoDistToRadical, rr)
					#if debug2==1:print "     radians for circle one: %f" % (radiansCircleOneSector)
					#if debug2==1:print "     radians for circle two: %f" % (radiansCircleTwoSector)
					areaCircleOneSector=areaSector(r, radiansCircleOneSector)
					areaCircleTwoSector=areaSector(rr, radiansCircleTwoSector)
					#if debug2==1:print "     area for plant one sector: %f" % (areaCircleOneSector)
					#if debug2==1:print "     area for plant two sector: %f" % (areaCircleTwoSector)
					areaCircleOneTriangle=areaTriangle(circleOneDistToRadical, theLengthRadicalLine/2.0)
					areaCircleTwoTriangle=areaTriangle(circleTwoDistToRadical, theLengthRadicalLine/2.0)
					#if debug2==1:print "     area for plant one triangle: %f" % (areaCircleOneTriangle)
					#if debug2==1:print "     area for plant two triangle: %f" % (areaCircleTwoTriangle)
					areaCircleOneThumbnail=areaThumbnail(areaCircleOneSector, areaCircleOneTriangle)
					areaCircleTwoThumbnail=areaThumbnail(areaCircleTwoSector, areaCircleTwoTriangle)
					#if debug2==1:print "     area for circle one thumbnail: %f" % (areaCircleOneThumbnail)
					#if debug2==1:print "     area for circle two thumbnail: %f" % (areaCircleTwoThumbnail)
					areaOverlap= areaCircleOneThumbnail+ areaCircleTwoThumbnail
					#if debug2==1:print "     area of thumbnail: %f" % (areaOverlap)
				return areaOverlap
