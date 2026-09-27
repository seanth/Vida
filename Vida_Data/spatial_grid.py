"""This file is part of Vida.
    --------------------------
    Copyright 2023, Sean T. Hammond

    Vida is experimental in nature and is made available as a research courtesy "AS IS," but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

    You should have received a copy of academic software agreement along with Vida. If not, see <https://github.com/seanth/Vida/blob/master/LICENSE.txt>.
"""

###A spatial grid finds the plants and seeds near a point quickly.
###
###The world is divided into square cells, like a sheet of graph paper, and
###each object is filed under the cell its centre is in. To find everything
###within some distance of a point, only the cells that distance reaches need
###to be looked at, rather than every object in the world. With thousands of
###objects that is the difference between thousands of checks and a handful.

import math


class SpatialGrid(object):
    def __init__(self, objects, cellSize):
        ###objects is a list of things with x and y (e.g. theGarden.soil)
        self.cellSize = cellSize
        self.cells = {}
        #each cell holds (position in the objects list, object), so that
        #nearby objects can be given back in the same order as that list
        self.nextPosition = 0
        for anObject in objects:
            self.add(anObject)

    def add(self, anObject):
        ###add an object, as if it was added to the end of the list
        theCell = self.cellFor(anObject)
        if theCell not in self.cells:
            self.cells[theCell] = []
        self.cells[theCell].append((self.nextPosition, anObject))
        self.nextPosition = self.nextPosition + 1

    def remove(self, anObject):
        ###take an object out (the rest keep their order)
        theCell = self.cellFor(anObject)
        entries = self.cells[theCell]
        for i in range(len(entries)):
            if entries[i][1] is anObject:
                del entries[i]
                return

    def cellFor(self, anObject):
        ###the cell an object is filed under
        if math.isfinite(anObject.x) and math.isfinite(anObject.y):
            return self.cellOf(anObject.x, anObject.y)
        else:
            #not a real position (nan or infinite): treat it as near everything
            return "anywhere"

    def cellOf(self, x, y):
        ###the column and row of the cell a point is in
        return (math.floor(x / self.cellSize), math.floor(y / self.cellSize))

    def near(self, x, y, distance, firstN=None):
        ###Every object whose centre is within distance of x,y, in the same
        ###order as the list the grid was made from. It can also include a few
        ###that are a little further away (in the same cells), so check each
        ###one properly afterwards.
        ###If firstN is given, only objects among the first firstN in the list
        ###are included.
        found = []
        if not (math.isfinite(x) and math.isfinite(y) and math.isfinite(distance)):
            #not a real position or distance: everything counts as near
            for theCell in self.cells:
                found.extend(self.cells[theCell])
        else:
            firstColumn, firstRow = self.cellOf(x - distance, y - distance)
            lastColumn, lastRow = self.cellOf(x + distance, y + distance)
            for column in range(firstColumn, lastColumn + 1):
                for row in range(firstRow, lastRow + 1):
                    if (column, row) in self.cells:
                        found.extend(self.cells[(column, row)])
            if "anywhere" in self.cells:
                found.extend(self.cells["anywhere"])
        #sorting (position, object) pairs puts them back in list order.
        #Positions are all different, so the objects themselves are never compared.
        found.sort()
        nearObjects = []
        for position, anObject in found:
            if firstN==None or position<firstN:
                nearObjects.append(anObject)
        return nearObjects
