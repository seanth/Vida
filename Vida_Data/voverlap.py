"""This file is part of Vida.
    --------------------------
    Copyright 2026, Sean T. Hammond

    Vida is experimental in nature and is made available as a research courtesy "AS IS," but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

    You should have received a copy of academic software agreement along with Vida. If not, see <https://github.com/seanth/Vida/blob/master/LICENSE.txt>.
"""

###Finding which canopies overlap, for the classic shading (determineShade in
###vworldr.py), all at once with numpy instead of one plant at a time.
###
###determineShade asks, for each plant in turn, "which of the objects before
###this place in the soil overlap me?", and used to answer by looking up the
###plant's neighbours in a spatial grid and checking each one with
###geometry_utils.checkOverlap. That was a third of the running time in a big
###world. Here the whole soil is put in a table (numpy arrays of x, y and
###radius, in soil order) and every plant's question is answered together:
###
###  1. Each object is filed under a square cell of the same spatial grid, and
###     each plant's neighbours are the objects in the cells its reach
###     touches, just as spatial_grid.near finds them.
###  2. For every (plant, neighbour) pair, whether the circles overlap is
###     worked out for all pairs at once. numpy's sums can differ from
###     math.hypot's in the last digit, so a pair only counts as overlapping
###     (or not) here when it is clear by a safe margin; the few pairs right
###     on the edge are checked with geometry_utils.checkOverlap itself.
###  3. The answers come back in soil order, as before.
###
###So the answers are exactly those the old loop gave. If anything in the
###soil has a position or radius that isn't a real number (nan or infinite),
###this gives up (returns None) and determineShade uses the old loop, which
###handles those the way it always did.

import math

import numpy

import geometry_utils

###how close to the edge (as a fraction of the squared distance) a pair has
###to be to get checked with checkOverlap itself; far wider than the few
###last-digit differences between numpy and math.hypot
MARGIN=1e-9


def cellNumbers(values, cellSize):
    ###the column (or row) of the grid cell each value is in, as spatial_grid.cellOf does
    return numpy.floor(values/cellSize).astype(numpy.int64)


def findEarlierOverlaps(soil, plantPlaces, reaches, cellSize):
    ###For each plant (the one at soil place plantPlaces[k], the k-th plant
    ###asked about), the places in the soil of the objects that overlap it
    ###among the first k objects of the soil, in soil order.
    ###reaches[k] is how far from the plant to look (as determineShade's
    ###reach); cellSize is the size of the grid's cells.
    ###Gives back a list of lists of places, or None (see above).
    count=len(soil)
    plants=len(plantPlaces)
    if plants==0:
        return []
    x=numpy.empty(count)
    y=numpy.empty(count)
    r=numpy.empty(count)
    place=0
    for anObject in soil:
        x[place]=anObject.x
        y[place]=anObject.y
        r[place]=anObject.r
        place=place+1
    reachArray=numpy.array(reaches, dtype=float)
    if not (numpy.isfinite(x).all() and numpy.isfinite(y).all() and numpy.isfinite(r).all()
            and numpy.isfinite(reachArray).all() and math.isfinite(cellSize)):
        return None
    plantArray=numpy.array(plantPlaces, dtype=numpy.int64)

    ###1. file every object under its cell, sorted by cell (and, within a
    ###cell, by soil place), so a cell's objects are one run of the sorted list
    column=cellNumbers(x, cellSize)
    row=cellNumbers(y, cellSize)
    lowestColumn=column.min()-4
    lowestRow=row.min()-4
    rows=row.max()-lowestRow+5
    cellKey=(column-lowestColumn)*rows+(row-lowestRow)
    byCell=numpy.argsort(cellKey, kind="stable")
    sortedKeys=cellKey[byCell]

    ###the cells each plant's reach touches, as spatial_grid.near works them out
    px=x[plantArray]
    py=y[plantArray]
    firstColumn=cellNumbers(px-reachArray, cellSize)
    lastColumn=cellNumbers(px+reachArray, cellSize)
    firstRow=cellNumbers(py-reachArray, cellSize)
    lastRow=cellNumbers(py+reachArray, cellSize)
    widest=int(max((lastColumn-firstColumn).max(), (lastRow-firstRow).max()))+1

    ###every (plant, neighbour) pair, cell by cell
    pairPlants=[]
    pairObjects=[]
    plantNumbers=numpy.arange(plants)
    for across in range(widest):
        for up in range(widest):
            theColumn=firstColumn+across
            theRow=firstRow+up
            inReach=(theColumn<=lastColumn)&(theRow<=lastRow)
            ###(and inside the range the cell numbers were worked out for)
            inReach=inReach&(theColumn>=lowestColumn)&(theRow>=lowestRow)&(theRow<lowestRow+rows)
            key=(theColumn-lowestColumn)*rows+(theRow-lowestRow)
            start=numpy.searchsorted(sortedKeys, key, side="left")
            end=numpy.searchsorted(sortedKeys, key, side="right")
            ###(a key outside the grid's range finds nothing, since no object has it)
            counts=numpy.where(inReach, end-start, 0)
            total=int(counts.sum())
            if total==0:
                continue
            owners=numpy.repeat(plantNumbers, counts)
            ###for each pair, which object in its plant's cell: start, start+1, ...
            firstOfEach=numpy.cumsum(counts)-counts
            offsets=numpy.arange(total)-numpy.repeat(firstOfEach, counts)
            pairPlants.append(owners)
            pairObjects.append(byCell[numpy.repeat(start, counts)+offsets])
    if not pairPlants:
        return [[] for k in range(plants)]
    owners=numpy.concatenate(pairPlants)
    objects=numpy.concatenate(pairObjects)

    ###only objects before the k-th place in the soil, and not the plant itself
    keep=(objects<owners)&(objects!=plantArray[owners])
    owners=owners[keep]
    objects=objects[keep]

    ###2. do the circles overlap? (checkOverlap: they don't if the distance
    ###between the centres is more than the two radii added together)
    dx=x[plantArray[owners]]-x[objects]
    dy=y[plantArray[owners]]-y[objects]
    squaredDistance=dx*dx+dy*dy
    radii=r[plantArray[owners]]+r[objects]
    squaredRadii=radii*radii
    clearlyOverlap=squaredDistance<squaredRadii*(1.0-MARGIN)
    clearlyApart=squaredDistance>squaredRadii*(1.0+MARGIN)
    onTheEdge=~(clearlyOverlap|clearlyApart)|(radii<0.0)
    overlap=clearlyOverlap&~onTheEdge
    for pair in numpy.nonzero(onTheEdge)[0].tolist():
        plant=soil[int(plantPlaces[owners[pair]])]
        other=soil[int(objects[pair])]
        overlap[pair]=geometry_utils.checkOverlap(plant.x, plant.y, plant.r, other.x, other.y, other.r)>0
    owners=owners[overlap]
    objects=objects[overlap]

    ###3. in soil order, plant by plant
    order=numpy.lexsort((objects, owners))
    owners=owners[order]
    objects=objects[order]
    splits=numpy.searchsorted(owners, plantNumbers[1:], side="left")
    answers=[]
    for places in numpy.split(objects, splits):
        answers.append(places.tolist())
    return answers
