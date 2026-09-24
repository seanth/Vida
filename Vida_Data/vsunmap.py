"""This file is part of Vida.
    --------------------------
    Copyright 2023, Sean T. Hammond

    Vida is experimental in nature and is made available as a research courtesy "AS IS," but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

    You should have received a copy of academic software agreement along with Vida. If not, see <https://github.com/seanth/Vida/blob/master/LICENSE.txt>.
"""

###The "sunmap" way of working out how much light reaches each plant
###(shadingModel: sunmap in Vida.ini, or -shade sunmap).
###
###Sunlight comes straight down. The ground is divided into small squares
###(cells), and each cell remembers how much of the sunlight is left by the
###time it gets down to the height we have reached: 1.0 is full sun, 0.02
###means only 2% got through.
###
###Plants are dealt with from the tallest to the shortest:
###  1. a plant's light is the average of the cells under its canopy;
###  2. then those cells are dimmed by the plant's canopyTransmittance, for
###     everything shorter underneath it.
###So only taller plants shade shorter ones, light that goes through two
###canopies is dimmed by both, and no random numbers are used.
###
###Heights are the top of the stem plus the height of the ground, so a short
###tree on a hill can shade a taller one in the valley below.
###Plants of exactly the same height don't shade each other: all of them read
###the map before any of them dims it.
###Seeds that need light to germinate get their light the same way, from the
###ground they lie on, but never shade anything.
###
###The time this takes grows with the area of the canopies, not with the
###number of pairs of plants, and the answer does not depend on the order of
###the plants in theGarden.soil.

import math

import numpy

import geometry_utils

#the most cells along each side of the map, so that a big world doesn't use
#a huge amount of memory (3000 x 3000 cells is about 70 MB). If a world
#needs more than this, the cells are made bigger.
MAX_CELLS = 3000


def needsLight(thing):
    ###plants, and seeds that need light to germinate (the same things the
    ###classic shading works out light for)
    return thing.isSeed==0 or (thing.isSeed and thing.minimumLightForGermination>0.0)


def topOf(thing):
    ###how high up a plant's canopy is: the top of its stem plus the height of
    ###the ground. A seed is on the ground. (A seed still has absHeightStem
    ###from the plant it came from, so that can't be used for seeds.)
    elevation=getattr(thing, "elevation", 0.0)
    if thing.isSeed:
        return elevation
    return thing.heightStem+elevation


def isOnTheMap(thing):
    return math.isfinite(thing.x) and math.isfinite(thing.y) and math.isfinite(thing.r)


class SunlightMap(object):
    def __init__(self, things, cellSize):
        ###A map big enough for every canopy in things, all in full sun.
        ###cellSize is the width of a cell in meters.
        left=0.0
        right=0.0
        bottom=0.0
        top=0.0
        first=True
        for thing in things:
            if isOnTheMap(thing):
                if first or thing.x-thing.r<left: left=thing.x-thing.r
                if first or thing.x+thing.r>right: right=thing.x+thing.r
                if first or thing.y-thing.r<bottom: bottom=thing.y-thing.r
                if first or thing.y+thing.r>top: top=thing.y+thing.r
                first=False
        width=max(right-left, cellSize)
        height=max(top-bottom, cellSize)
        if max(width, height)/cellSize>MAX_CELLS:
            cellSize=max(width, height)/MAX_CELLS
        self.cellSize=cellSize
        self.left=left
        self.bottom=bottom
        self.columns=int(math.ceil(width/cellSize))+1
        self.rows=int(math.ceil(height/cellSize))+1
        #light[row][column]; row 0 is at the bottom (lowest y)
        self.light=numpy.ones((self.rows, self.columns))

    def cellsUnder(self, x, y, r):
        ###The cells under a canopy of radius r centred on x,y: the rows and
        ###columns of the block of the map around it, and which cells in that
        ###block have their centre inside the canopy (None means all of them).
        ###A canopy smaller than half a cell, or too small to cover the centre
        ###of any cell, gets the one cell its centre is in.
        if r<self.cellSize/2.0:
            return self.cellAt(x, y)
        firstColumn=max(0, int(math.floor((x-r-self.left)/self.cellSize)))
        lastColumn=min(self.columns-1, int(math.floor((x+r-self.left)/self.cellSize)))
        firstRow=max(0, int(math.floor((y-r-self.bottom)/self.cellSize)))
        lastRow=min(self.rows-1, int(math.floor((y+r-self.bottom)/self.cellSize)))
        #where the centres of the cells in the block are
        centreX=self.left+(numpy.arange(firstColumn, lastColumn+1)+0.5)*self.cellSize
        centreY=self.bottom+(numpy.arange(firstRow, lastRow+1)+0.5)*self.cellSize
        #distance squared from x,y to each centre, as a block of rows x columns
        distanceSquared=(centreY[:, numpy.newaxis]-y)**2+(centreX[numpy.newaxis, :]-x)**2
        inside=distanceSquared<=r*r
        if not inside.any():
            return self.cellAt(x, y)
        return slice(firstRow, lastRow+1), slice(firstColumn, lastColumn+1), inside

    def cellAt(self, x, y):
        ###the one cell that x,y is in, in the same form as cellsUnder
        column=min(self.columns-1, max(0, int(math.floor((x-self.left)/self.cellSize))))
        row=min(self.rows-1, max(0, int(math.floor((y-self.bottom)/self.cellSize))))
        return slice(row, row+1), slice(column, column+1), None

    def averageLight(self, cells):
        ###the average light reaching some cells (from cellsUnder)
        rows, columns, inside=cells
        if inside is None:
            return float(self.light[rows, columns].mean())
        return float(self.light[rows, columns][inside].mean())

    def dimCells(self, cells, transmittance):
        ###a canopy over these cells lets through only this fraction of the
        ###light that reaches it
        rows, columns, inside=cells
        if inside is None:
            self.light[rows, columns]=self.light[rows, columns]*transmittance
        else:
            block=self.light[rows, columns]
            block[inside]=block[inside]*transmittance

    def lightUnder(self, x, y, r):
        ###the average light reaching the cells under a canopy
        return self.averageLight(self.cellsUnder(x, y, r))

    def dim(self, x, y, r, transmittance):
        self.dimCells(self.cellsUnder(x, y, r), transmittance)


def determineShade(theGarden, cellSize=0.05):
    ###Works out, for every plant (and every seed that needs light), the same
    ###things the classic determineShade does: colourLeaf[2] is the fraction
    ###of full sun it gets and areaCovered is the area of its canopy that is
    ###in shade. Both include the light intensity of its region.
    ###
    ###overlapList is left empty. (The classic shading fills it with the
    ###overlapping plants, and removeOverlaps then only checks those for
    ###touching stems. Empty means removeOverlaps checks everything nearby.)
    things=[]
    for thing in theGarden.soil:
        if needsLight(thing):
            things.append(thing)
    if len(things)==0:
        return
    theMap=SunlightMap(things, cellSize)
    things=sorted(things, key=topOf, reverse=True)
    #go through the plants in groups of the same height, tallest group first
    start=0
    while start<len(things):
        end=start+1
        while end<len(things) and topOf(things[end])==topOf(things[start]):
            end=end+1
        group=things[start:end]
        #everyone in the group reads the light before anyone in it dims it
        cellsOf=[]
        for thing in group:
            if isOnTheMap(thing):
                cells=theMap.cellsUnder(thing.x, thing.y, thing.r)
                fractionReaching=theMap.averageLight(cells)
            else:
                cells=None
                fractionReaching=1.0
            cellsOf.append(cells)
            setLight(theGarden, thing, fractionReaching)
        for i in range(len(group)):
            if group[i].isSeed==0 and cellsOf[i]!=None:
                theMap.dimCells(cellsOf[i], group[i].canopyTransmittance)
        start=end


def setLight(theGarden, thing, fractionReaching):
    ###record the light a plant gets, as the classic shading does
    if len(thing.subregion)>0:
        theRegion=thing.subregion[-1]
    else:
        theRegion=theGarden
    fractionExposed=fractionReaching*theRegion.lightIntensity
    thePlantAreaTotal=geometry_utils.areaCircle(thing.r)
    thePlantAreaExposed=thePlantAreaTotal*fractionExposed
    thing.overlapList=[]
    thing.areaCovered=thePlantAreaTotal-thePlantAreaExposed
    thing.colourLeaf[2]=fractionExposed
