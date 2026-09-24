"""This file is part of Vida.
    --------------------------
    Copyright 2023, Sean T. Hammond

    Vida is experimental in nature and is made available as a research courtesy "AS IS," but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

    You should have received a copy of academic software agreement along with Vida. If not, see <https://github.com/seanth/Vida/blob/master/LICENSE.txt>.
"""

###Events are things that happen at a set cycle of a simulation. They are read
###from an event file (the -e option). See "Scripting events" in
###Readme_Files/Vida HOWTO.txt for how to write one.
###
###There is one function here for each kind of event. At the start of each
###cycle, Vida.py calls the right function for each event in the event file.
###Each function gets the dictionary of settings written under the event, e.g.
###for
###    10:
###       - Garden:
###         - lightIntensity: 0.5
###the Garden event at cycle 10 gets {'lightIntensity': 0.5}

import os
import random

import geometry_utils
import vworldr as worldBasics
import vplacement


def gardenEvent(theGarden, theDict, debug):
    ###change settings of the whole world, e.g. lightIntensity or waterLevel
    if debug==1: print("debug: A garden related event has been triggered.")
    for theGardenAttr in theDict.keys():
        setattr(theGarden, theGardenAttr, theDict[theGardenAttr])


def zoneEvent(theGarden, zoneType, theDict, debug):
    ###zoneType is "Killzone" or "Safezone"
    ###A Killzone kills the targeted plants and/or seeds inside it.
    ###A Safezone kills everything outside it (and, inside it, whichever of
    ###plants or seeds is NOT the target).
    if debug==1: print("debug: generation of a zone event has been triggered.")
    #the atrributes in a killzone are: X & Ythe SHAPE(circle or square) is centered on, the SIZE of the shape, and what is the TARGET
    #(plants or seeds). You can also define a SPECIES_NAME to target
    zoneX=float(theDict['x'])
    zoneY=float(theDict['y'])
    zoneSize=float(theDict['size'])
    zoneShape=theDict['shape']
    zoneTarget=theDict['target']
    if 'species_name' in theDict:
        zoneSpecies=theDict['species_name']
        #student requested addition to accept list of species. 2023-0323
        zoneSpecies=zoneSpecies.split(",")
    else:
        zoneSpecies = 'all'
    ###############
    #Adding in ability to have chance of what happens in a zone
    #STH 2026-0908
    #Percent is a percent chance the event will happen to the targeted thing
    if 'percent' in theDict:
        zonePercent=theDict['percent']
        if zonePercent>1.0:
            zonePercent=1.0
    else:
        zonePercent=1.0
    ###########
    #Adding in ability to be able to target plants based on an attribute the plant has
    #STH 2026-0909
    zoneSelAttribute, zoneSelLogic, zoneSelValue = readZoneSelection(theDict)

    if zoneShape not in ['circle','square']:
        print("\n***WARNING: improper zone shape defined. Defaulting to square.***")
        zoneShape='square'
    if zoneTarget not in ['all','plants','seeds']:
        print("\n***WARNING: improper zone target defined. Defaulting to all.***")
        zoneTarget='all'

    killThese=[]
    for theObject in theGarden.soil:
        theResult=whereInZone(theObject, zoneShape, zoneX, zoneY, zoneSize)
        if theResult>0 and zoneType=='Killzone':
            #student requested addition to accept list of species. 0323-2023
            if (zoneSpecies == 'all') or (theObject.nameSpecies in zoneSpecies):
                if zoneTarget=='all' or (theObject.isSeed and zoneTarget=='seeds') or (not theObject.isSeed and zoneTarget=='plants'):
                    #Adding in ability to have chance of what happens in a zone
                    #STH 2026-0908
                    theChance=random.random()
                    if theChance<=zonePercent:
                        #this means the object is a target
                        if zoneSelAttribute != "none":
                            #check whether the provided attribute is present on the object(plant/seed)
                            if not hasattr(theObject, zoneSelAttribute):
                                print("***WARNING: attribute does not exist on targeted species")
                                print("***Ignoring selection criteria")
                                #from here on, the rest of the targets are killed without the check
                                zoneSelAttribute = "none"
                            elif selectionMatches(getattr(theObject, zoneSelAttribute), zoneSelLogic, zoneSelValue):
                                killThese.append(theObject)
                        else:
                            killThese.append(theObject)
        elif zoneType=='Safezone':
            if theResult==0:
                killThese.append(theObject)
            elif theResult>0:
                if (theObject.isSeed and zoneTarget=='plants') or (not theObject.isSeed and zoneTarget=='seeds'):
                    killThese.append(theObject)

    for theObject in killThese:
        theObject.causeOfDeath="killzone"
        theGarden.kill(theObject)


def readZoneSelection(theDict):
    ###A zone can target only the plants or seeds whose attribute passes a test, e.g.
    ###    selection:
    ###     - attribute: massStem
    ###       logic: '>'
    ###       value: 2.4e-05
    ###Returns the attribute, logic and value. The attribute is "none" if
    ###there is no selection, or it can't be used.
    zoneSelAttribute = "none"
    zoneSelLogic = None
    zoneSelValue = None
    if "selection" in theDict:
        theSelectionDict=theDict['selection'][0]
        #make sure the selection array has all three needed elements
        #(each one checked: ("attribute" and "logic" and "value") is just
        #"value", so only that one used to be checked)
        if not ("attribute" in theSelectionDict and "logic" in theSelectionDict and "value" in theSelectionDict):
            print("\n***WARNING: Selection array needs exactly three elements: attribute, logic, and value")
            print("\n***Ignoring selection criteria")
            zoneSelAttribute = "none"
        else:
            zoneSelAttribute = theSelectionDict['attribute']
            zoneSelLogic = theSelectionDict['logic']
            zoneSelValue = theSelectionDict['value']
            if zoneSelLogic not in ['<', '=', '==', '>']:
                print("\n***WARNING: logic element must be <, =, ==, or >")
                print("***Ignoring selection criteria")
                zoneSelAttribute = "none"
            if (zoneSelLogic in ['<', '>']) and (isinstance(zoneSelValue, (str))):
                print("\n***WARNING: can't use '<' or '>' on a value element that is a string")
                print("***Ignoring selection criteria")
                zoneSelAttribute = "none"
    return zoneSelAttribute, zoneSelLogic, zoneSelValue


def selectionMatches(theValue, zoneSelLogic, zoneSelValue):
    ###does an object's attribute value pass the selection test?
    if zoneSelLogic in ['=', '==']:
        return theValue == zoneSelValue
    if zoneSelLogic == '<':
        return theValue < zoneSelValue
    if zoneSelLogic == '>':
        return theValue > zoneSelValue
    return False


def whereInZone(theObject, zoneShape, zoneX, zoneY, zoneSize):
    ###0 if the object is outside the zone, more than 0 if it is inside.
    ###A circle zone uses size as its radius and counts an object whose seed or
    ###stem touches the circle as inside. A square zone uses size as the length
    ###of a side and only looks at the object's centre.
    if zoneShape=='circle':
        if theObject.isSeed:
            r=theObject.radiusSeed
        else:
            r=theObject.radiusStem
        return geometry_utils.checkOverlap(theObject.x, theObject.y, r, zoneX, zoneY, zoneSize)
    else:
        return geometry_utils.pointInsideSquare(zoneX, zoneY, zoneSize, theObject.x, theObject.y)


def seedEvent(theGarden, theDict, seedPlacement, sList, addPopulationSize, useDefaultYml, ymlList, speciesClass, debug):
    ###add seeds to the world
    ###seedPlacement, sList and addPopulationSize are how the last seeding was
    ###done. A Seed event only changes the ones it gives values for, and the
    ###others carry on from the last time, so they are passed in and the new
    ###values are returned.
    ###speciesClass is the class used to make a species (Species1 in Vida.py)
    if debug==1: print("debug: A seeding related event has been triggered.")
    for infoItem in theDict.keys():
        if infoItem=="number" and not seedPlacement=="fromFile": addPopulationSize=theDict[infoItem]
        if infoItem=="species_file":
            sList=theDict[infoItem]
            if sList=="random": sList=[]
        if infoItem=="placement": seedPlacement=theDict[infoItem]
        if seedPlacement=="hexagon": seedPlacement="hex" #just make sure it is consistant
        if os.path.isfile(seedPlacement):
            if debug == 1: print("debug: Confirming placement file exists....")
            sList=vplacement.readPlacementFile(seedPlacement)
            addPopulationSize=len(sList)
            seedPlacement="fromFile"
            if debug ==1: print("debug: Will place seeds from a file")
            ###if a simulation is being reloaded from a pickle, that sim might not have saved
            ###data on a new species being introduced. Load the new species and add it to the platonic list
            ###so it can be added to theGarden
            for j in sList:
                jj=j[0]
                #Only load species that have a file in Species/. Anything else
                #(such as 'random') is left for placeSeed, which warns and uses
                #a random species instead.
                speciesIsMissing = (not jj in theGarden.platonicSeeds) and os.path.isfile("Species/"+jj)
                if speciesIsMissing==True:
                    if debug == 1: print("debug: Desired species missing from loaded simulation")
                    if debug == 1: print("debug: Adding species %s" % (jj))
                    loadSpecies(theGarden, jj, speciesClass)

    if addPopulationSize==None:
        raise ValueError("A Seed event needs a 'number' of seeds, or a placement file")

    if not seedPlacement=="fromFile" and not sList==[]:
        newList=[]
        for j in range(addPopulationSize):
            newList.append(sList)
        ###if a simulation is being reloaded from a pickle, that sim might not have saved
        ###data on a new species being introduced. Load the new species and add it to the platonic list
        ###so it can be added to theGarden
        sList=newList
        newList=list(set(sList))
        for j in newList:
            if not j in theGarden.platonicSeeds:
                loadSpecies(theGarden, j, speciesClass)

    theGarden.placeSeed(seedPlacement, sList, addPopulationSize, useDefaultYml, ymlList)
    ################
    #if there is a terrain file and water level then the initial placement of seeds
    #should be checked to see if any of them are below water
    #STH 0328-2021
    if(theGarden.terrainImage != []):
        theGarden.checkSubmergedMortality()
    ################
    sList= [] #reset the sList to what it was when we started
    return seedPlacement, sList, addPopulationSize


def loadSpecies(theGarden, fileName, speciesClass):
    ###read a species file from Species/ and keep it as a "platonic" seed,
    ###the template that new seeds of that species are copied from
    theSeed=speciesClass()
    fileLoc= "Species/"+fileName
    theSeed.importPrefs(fileLoc)
    theSeed.name="Platonic %s" % fileName
    theGarden.platonicSeeds[fileName]=theSeed


def regionEvent(theGarden, theDict, updatePlants, debug):
    ###make a region (an area with its own light, gravity etc.), or change one
    ###updatePlants says whether plants need to be checked for being inside a
    ###changed region. Once a region has changed it stays True for later
    ###region events, so it is passed in and returned.
    if debug: print("debug: Region event detected...")
    regionAttrs=theDict.keys()
    theRegionName=str(theDict['name'])
    if debug: print("debug: Region %s event detected." % (theRegionName))
    regionNames=[]
    for i in theGarden.theRegions:
        regionNames.append(i.name)
    if theRegionName in regionNames:
        for j in theGarden.theRegions:
            if j.name==theRegionName:
                theRegion=j
                break
        for aAttr in regionAttrs:
            if not getattr(theRegion,aAttr,"does not exist")==theDict[aAttr]:
                if debug: print("debug: Region %s has had a change in one or more attributes." % (theRegionName))
                updatePlants=True
                break
        ##now just read in the values#
        if debug: print("debug: Updating attributes for region %s." % (theRegionName))
        for theRegionAttr in regionAttrs:                                 #
            setattr(theRegion, theRegionAttr, theDict[theRegionAttr])     #
        if updatePlants:
            if debug:print("debug: updating plants with changed region info")
            addPlantsInRegion(theGarden, theRegion)
    else:
        newRegion=worldBasics.garden()
        newRegion.name=theRegionName
        ###these are default values###
        newRegion.x=0.0              #
        newRegion.y=0.0              #
        newRegion.worldSize=1.0      #
        newRegion.shape='square'     #
        ##############################
        ##now just read in the values#
        if debug: print("debug: Making attributes for region")
        for theRegionAttr in regionAttrs:                                 #
            setattr(newRegion, theRegionAttr, theDict[theRegionAttr])     #
        theGarden.theRegions.append(newRegion)
        addPlantsInRegion(theGarden, newRegion)
    return updatePlants


def addPlantsInRegion(theGarden, theRegion):
    ###add the region to the list of regions of every plant and seed inside it
    for aPlant in theGarden.soil:
        if worldBasics.isInsideRegion(theRegion, aPlant.x, aPlant.y):
            if not theRegion in aPlant.subregion:
                aPlant.subregion.append(theRegion)


def speciesEvent(theGarden, theDict, debug):
    ###change settings of a species, for the plants and seeds of that species
    ###already in the world
    if debug: print("debug: Species event detected...")
    theSpeciesName = theDict['name']
    #list() makes a copy that can have 'name' removed from it.
    #In python 3, keys() is a view of the dictionary with no remove()
    speciesAttrs = list(theDict.keys())
    #I'm not sure whether the user should be allowed to change the base species name
    #Why might this be useful? Species evolution/creation of a new subspecies?
    #STH 2019-0930
    if 'name' in speciesAttrs:
        speciesAttrs.remove('name')

    #Do we need to go through and modify all the "platonic seeds" in theGarden?
    #Might need to revisit this part of the code
    #STH 2019-0930
    for theObject in theGarden.soil:
        if theObject.nameSpecies == theSpeciesName:
            for theSpeciesAttr in speciesAttrs:
                if debug: print("       Attempting to set species '%s' property '%s' to %s" % (theObject.nameSpecies, theSpeciesAttr, theDict[theSpeciesAttr]))
                setattr(theObject, theSpeciesAttr, theDict[theSpeciesAttr])
