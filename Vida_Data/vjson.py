"""This file is part of Vida.
    --------------------------
    Copyright 2023, Sean T. Hammond

    Vida is experimental in nature and is made available as a research courtesy "AS IS," but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

    You should have received a copy of academic software agreement along with Vida. If not, see <https://github.com/seanth/Vida/blob/master/LICENSE.txt>.
"""

###Saves a simulation for the web viewer (viewer/index.html), with the -j option.
###
###The file is "JSON Lines": each line is one JSON object.
###  The first line describes the world: its size, the species and their
###  colours, and the shape of the ground if a terrain file is used.
###  Each line after that is one cycle: every plant and seed, the regions,
###  the water level, and how many plants and seeds died of what.
###
###To keep the file small, each plant is a list of numbers rather than a
###dictionary with names. The order of the numbers is given by PLANT_FIELDS
###and SEED_FIELDS, which are also written in the first line.

import json
import math

import vterrainImport as terrain_utils

FORMAT_VERSION = 1

PLANT_FIELDS = ["x", "y", "elevation", "stemRadius", "stemHeight", "canopyRadius",
                "species", "light", "mature", "age"]
SEED_FIELDS = ["x", "y", "elevation", "radius", "species"]

#the most cells along each side of the terrain grid (so big terrains stay small)
TERRAIN_CELLS = 100


def number(value, places=4):
    ###a number rounded for the file. JSON can't hold nan or infinity, so
    ###those become null.
    if value is None or not math.isfinite(value):
        return None
    return round(value, places)


class ViewerFile(object):
    def __init__(self, fileName, theGarden, vidaVersion):
        self.theFile = open(fileName, "w")
        #species are numbered in the order they first appear
        self.speciesNumbers = {}
        header = {
            "format": "vida-viewer",
            "version": FORMAT_VERSION,
            "vida": vidaVersion,
            "name": theGarden.name,
            "worldSize": theGarden.theWorldSize,
            "plantFields": PLANT_FIELDS,
            "seedFields": SEED_FIELDS,
            "terrain": describeTerrain(theGarden),
        }
        self.writeLine(header)

    def writeLine(self, data):
        self.theFile.write(json.dumps(data, allow_nan=False) + "\n")

    def speciesNumber(self, thing, newSpecies):
        ###the number of a plant's or seed's species. The first time a species
        ###is seen, its colours are added to newSpecies.
        name = thing.nameSpecies
        if name not in self.speciesNumbers:
            self.speciesNumbers[name] = len(self.speciesNumbers)
            newSpecies.append({
                "number": self.speciesNumbers[name],
                "name": name,
                "colour": colourList(thing.colourSpecies),
                "leafColour": colourList(thing.colourLeaf),
                "stemColour": colourList(thing.colourStem),
                "canopyTransmittance": number(thing.canopyTransmittance),
            })
        return self.speciesNumbers[name]

    def writeCycle(self, theGarden):
        ###write the world as it is now. Call before theGarden.deathNote is cleared.
        newSpecies = []
        plants = []
        seeds = []
        for thing in theGarden.soil:
            species = self.speciesNumber(thing, newSpecies)
            if thing.isSeed:
                seeds.append([number(thing.x), number(thing.y), number(getattr(thing, "elevation", 0.0)),
                              number(thing.radiusSeed, 5), species])
            else:
                if thing.isMature:
                    mature = 1
                else:
                    mature = 0
                plants.append([number(thing.x), number(thing.y), number(getattr(thing, "elevation", 0.0)),
                               number(thing.radiusStem, 5), number(thing.heightStem, 3),
                               number(thing.radiusLeaf, 3), species, number(thing.colourLeaf[2], 3),
                               mature, thing.age])
        deaths = {}
        for thing in theGarden.deathNote:
            cause = thing.causeOfDeath
            if cause not in deaths:
                deaths[cause] = 0
            deaths[cause] = deaths[cause] + 1
        regions = []
        for region in theGarden.theRegions:
            regions.append({
                "name": region.name,
                "shape": region.shape,
                "x": number(region.x),
                "y": number(region.y),
                "size": number(region.size),
                "lightIntensity": number(getattr(region, "lightIntensity", 1.0)),
            })
        waterLevel = theGarden.waterLevel
        if not isinstance(waterLevel, (int, float)):
            waterLevel = None
        self.writeLine({
            "cycle": theGarden.cycleNumber,
            "newSpecies": newSpecies,
            "plants": plants,
            "seeds": seeds,
            "deaths": deaths,
            "regions": regions,
            "waterLevel": number(waterLevel),
            "lightIntensity": number(theGarden.lightIntensity),
        })

    def close(self):
        self.theFile.close()


def colourList(theColour):
    ###a colour as [hue in degrees, saturation 0-1, brightness 0-1]
    return [number(theColour[0], 3), number(theColour[1], 3), number(theColour[2], 3)]


def describeTerrain(theGarden):
    ###The height of the ground on a grid of at most TERRAIN_CELLS x
    ###TERRAIN_CELLS points, or None if there is no terrain.
    ###elevation[row][column] is the height at
    ###    x = -worldSize/2 + column*cellSize,  y = -worldSize/2 + row*cellSize
    ###so row 0 is the lowest y and column 0 the lowest x. It is looked up the
    ###same way Vida finds the height under a seed.
    if theGarden.terrainImage == []:
        return None
    worldSize = theGarden.theWorldSize
    cells = min(TERRAIN_CELLS, int(worldSize))
    if cells < 1:
        cells = 1
    cellSize = worldSize / float(cells)
    elevation = []
    for row in range(cells):
        heights = []
        for column in range(cells):
            #Vida finds the pixel under a point by adding worldSize/2 to x and y
            thePixelValue = terrain_utils.getPixelValue(column * cellSize, row * cellSize, theGarden.terrainImage)
            heights.append(number(terrain_utils.elevationFromPixel(thePixelValue, theGarden.maxElevation), 3))
        elevation.append(heights)
    return {"cells": cells, "cellSize": number(cellSize), "maxElevation": number(theGarden.maxElevation),
            "elevation": elevation}
