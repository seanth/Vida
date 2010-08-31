#!/usr/bin/env python
"""This file is part of Vida.
--------------------------
Copyright 2009, Sean T. Hammond

Vida is experimental in nature and is made available as a research courtesy "AS IS," but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 

You should have received a copy of academic software agreement along with Vida. If not, see <http://iorek.ice-nine.org/seant/Vida/license.txt>.
"""

import random
import math
import os
import os.path
import glob
import sys
#import pp #08.10.12
#print sys.path

runningInNodeBox=False
if __name__=="__builtin__":
	##probably running in NodeBox
	sys.path.append("/Library/Frameworks/Python.framework/Versions/2.4/lib/python2.4/site-packages")
	runningInNodeBox=True

import copy
import time
import pickle
###append the path to basic data files
sys.path.append("Vida_Data")
import vworldr as worldBasics
import vplantr as defaultSpecies
import vgraphics as outputGraphics
import list_utils as list_utils
import geometry_utils as geometry_utils

import progressBarClass
###append the path to where species are
sys.path.append("Species")

###import default settings
import vdefaults as thePrefs
simulationName= thePrefs.simulationName
theWorldSize= thePrefs.theWorldSize
startPopulationSize=thePrefs.startPopulationSize
maxPopulation=thePrefs.maxPopulation
maxCycles=thePrefs.maxCycles
outputDirectory=thePrefs.outputDirectory
webDirectory=thePrefs.webDirectory
produceGraphics=thePrefs.produceGraphics
produceDXFGraphics=thePrefs.produceDXFGraphics
produceVideo=thePrefs.produceVideo
framesPerSecond=thePrefs.framesPerSecond
webOutput=thePrefs.webOutput
percentTimeStamp=thePrefs.percentTimeStamp
theView=thePrefs.theView
resumeSim=thePrefs.resumeSim
reloadSpeciesData=thePrefs.reloadSpeciesData
archive=thePrefs.archive
saveData=thePrefs.saveData
deleteCfdgFiles=thePrefs.deleteCfdgFiles
deletePngFiles=thePrefs.deletePngFiles
showProgressBar= thePrefs.showProgressBar
debug=thePrefs.debug
debug2=thePrefs.debug2
timesToRepeat=thePrefs.timesToRepeat
sList=[]
seedPlacement="random"
produceStats=0
simulationFile=""
eventFile="events.yml"

###code sample from myself and gib
#import pp
#server = pp.Server()
#if (server.get_ncpus() == 1):
#    server.destory()

class Species1(defaultSpecies.genericPlant):
	###The routine in defaultSpecies.genericPlant reads in default values from .yml file
	def __init__(self):
		##super(type, obj) -> bound super object; requires isinstance(obj, type)
		super(Species1, self).__init__()


def saveSimulationPoint(theDirectory, theFileName, theGarden):
	#turn this off until I can understand why it isn't working
	if not runningInNodeBox:
		simulationStateFile =open(theDirectory + theFileName, 'wb')
		pickle.dump(theGarden, simulationStateFile)
		simulationStateFile.close()
		#print "simulation state saved to file"

def saveDataPoint (theDirectory, theFileName, theGarden):
	basicHeaders="Cycle #, Plant Name, Species, Mother Plant Name, X Location, Y Location, is a seed, is mature, cycles until germination, Age, Mass of Stem, Mass of Canopy, # of Seeds, Mass of all Seeds, Mass Stem+Mass Canopy, Mass Total, Diameter Stem, Radius Canopy, Height Stem, Maximum Thickness of a Leaf, Height of Plant, Yearly Growth Stem (kg), Yearly Growth Canopy (kg), Yearly Growth Stem+Canopy (kg), Yearly Growth Stem diameter (m), Yearly Growth Stem Height (m), Average Growth Stem (kg), Average Growth Canopy (kg), Average Growth Stem+Canopy (kg), Average Growth Stem diameter (m), Average Growth Stem Height (m), Cause of Death \n"
	photosynthesisHeaders="leaf is a hemisphere?, area canopy available for photosynthesis, area canopy covered, fraction canopy 100% shaded, canopy transmittance, canopy transmittance impacts photosynthesis?, faction of canopy that needs to be 0% shaded for survival"

	reproductionHeaders="make seeds?, age to start making seeds, height to start making seeds, fraction of mass used for seeds, Maximum Seed Mass, Where seeds grow, Seed dispersal method, fraction of seeds which fail to germinate, delay in germination, fraction of maximum seed mass needed to germinate, fraction of seed mass converted to plant mass"

	allometryHeaders="B1 in Ms=B1*(Mt^a1), a1 in Ms=B1*(Mt^a1), B2 in Mlyoung=B2*(Ms^a2), a2 in Mlyoung=B2*(Ms^a2), B3 in Mlmature=B3*(Ms^a3), a3 in Mlmature=B3*(Ms^a3), B4 in Ds=B4*(Ms^a4), a4 in Ds=B4*(Ms^a4), B5 in Hs=[B5*(Ds^a5)]-B6, a5 in [B5*(Ds^a5)]-B6, B6 in Hs=[B5*(Ds^a5)]-B6, B7 in Mg=[B7*(Ml^a7)]/ area canopy 100% uncovered,  a7 in Mg=[B7*(Ml^a7)]/ area canopy 100% uncovered, B8 in Mpt=B8*(Al^a8), a8 in Mpt=B8*(Al^a8)"


	#theHeader="Plant Name, Mother Plant, Species, X Location, Y Location, Mass Stem, Mass Leaf, # Seeds, Mass all Seeds, Radius Stem, Radius Leaf, Height Plant, Cause of Death \n"
	theHeader= basicHeaders
	thePlantList=[]
	theSeedList=[]
	theCorpseList=[]
	thePlantList.append(theHeader)
	theSeedList.append(theHeader)
	theCorpseList.append(theHeader)
	for plant in theGarden.soil:
		if plant.age>0:
			theData="%i,%s,%s,%s,%f,%f,%s,%s,%i,%i,%f,%f,%i,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%s \n" % (theGarden.cycleNumber,plant.name,plant.nameSpecies,plant.motherPlant,plant.x,plant.y,plant.isSeed,plant.isMature,plant.countToGerm,plant.age,plant.massStem,plant.massLeaf,len(plant.seedList),plant.massSeedsTotal,plant.massStem+plant.massLeaf,plant.massTotal,plant.radiusStem*2,plant.radiusLeaf,plant.heightStem,plant.heightLeafMax,plant.z,plant.GMs,plant.GMl,plant.GMs+plant.GMl,2.0*plant.GRs,plant.GHs,plant.massStem/plant.age,plant.massLeaf/plant.age,(plant.massStem+plant.massLeaf)/plant.age,(plant.radiusStem*2)/plant.age,plant.heightStem/plant.age,"na")
		else:
			theData="%i,%s,%s,%s,%f,%f,%s,%s,%i,%i,%f,%f,%i,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%s \n" % (theGarden.cycleNumber,plant.name,plant.nameSpecies,plant.motherPlant,plant.x,plant.y,plant.isSeed,plant.isMature,plant.countToGerm,plant.age,plant.massStem,plant.massLeaf,len(plant.seedList),plant.massSeedsTotal,plant.massStem+plant.massLeaf,plant.massTotal,plant.radiusStem*2,plant.radiusLeaf,plant.heightStem,plant.heightLeafMax,plant.z,plant.GMs,plant.GMl,plant.GMs+plant.GMl,2.0*plant.GRs,plant.GHs,0,0,0,0,0,"na")			
		if plant.isSeed:
			theSeedList.append(theData)
		else:
			thePlantList.append(theData)			
	for plant in theGarden.deathNote:
		if plant.age>0:
			theData="%i,%s,%s,%s,%f,%f,%s,%s,%i,%i,%f,%f,%i,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%s \n" % (theGarden.cycleNumber,plant.name,plant.nameSpecies,plant.motherPlant,plant.x,plant.y,plant.isSeed,plant.isMature,plant.countToGerm,plant.age,plant.massStem,plant.massLeaf,len(plant.seedList),plant.massSeedsTotal,plant.massStem+plant.massLeaf,plant.massTotal,plant.radiusStem*2,plant.radiusLeaf,plant.heightStem,plant.heightLeafMax,plant.z,plant.GMs,plant.GMl,plant.GMs+plant.GMl,2.0*plant.GRs,plant.GHs,plant.massStem/plant.age,plant.massLeaf/plant.age,(plant.massStem+plant.massLeaf)/plant.age,(plant.radiusStem*2)/plant.age,plant.heightStem/plant.age,plant.causeOfDeath)
		else:
			theData="%i,%s,%s,%s,%f,%f,%s,%s,%i,%i,%f,%f,%i,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%s \n" % (theGarden.cycleNumber,plant.name,plant.nameSpecies,plant.motherPlant,plant.x,plant.y,plant.isSeed,plant.isMature,plant.countToGerm,plant.age,plant.massStem,plant.massLeaf,len(plant.seedList),plant.massSeedsTotal,plant.massStem+plant.massLeaf,plant.massTotal,plant.radiusStem*2,plant.radiusLeaf,plant.heightStem,plant.heightLeafMax,plant.z,plant.GMs,plant.GMl,plant.GMs+plant.GMl,2.0*plant.GRs,plant.GHs,0,0,0,0,0,plant.causeOfDeath)
		theCorpseList.append(theData)
	if len(thePlantList)>1:
		saveDataFile =open(theDirectory+"Plants/"+ theFileName, 'wb')
		saveDataFile.writelines(thePlantList)
		saveDataFile.close()
	if len(theSeedList)>1:
		saveDataFile =open(theDirectory+"Seeds/"+ theFileName, 'wb')
		saveDataFile.writelines(theSeedList)
		saveDataFile.close()
	if len(theCorpseList)>1:
		saveDataFile =open(theDirectory+"Corpses/"+ theFileName, 'wb')
		saveDataFile.writelines(theCorpseList)
		saveDataFile.close()
	thePlantList=[]
	theSeedList=[]
	theCorpseList=[]
	#print "simulation data saved to file

	

def makeDirectory(theDirectory):
	if not os.path.exists(theDirectory):
		os.mkdir(theDirectory)
	else:
		###all this adds an increasing numberic suffix to the folders so
		###one doesn't overwrite things
		while os.path.exists(theDirectory):
			basicPath=os.path.split(theDirectory)[0]
			i=0
			for n in basicPath:
				i=i-1
				if n=="/": break
				if not basicPath[i].isdigit():break
			theSuffix=""
			if i<-1:
				theSuffix=int(basicPath[i+1:])+1
				basicPath=basicPath[0:i+1]
			else:
				theSuffix=1
			basicPath=basicPath+str(theSuffix)
			theDirectory=basicPath+"/"
		os.mkdir(theDirectory)
	return theDirectory
		
def correctType(theItem):
	returnValue="na"
	if theItem.isdigit():
			returnValue=int(theItem)
	else:
		try:
			returnValue=float(theItem)
		except ValueError:
			try:
				returnValue=str(theItem)
			except ValueError:	
				returnValue="na"
	return returnValue
	
def checkSeedPlacementList(seedPlacementList):
	#remove blank lines that are just \n
	i=0
	for aLine in seedPlacementList:
		if aLine=="\n":seedPlacementList[i]=""
		i=i+1
	i=0
	for aLine in seedPlacementList:
		if not aLine=="":
			aLine=aLine.rstrip("\n")
			aLine=aLine.split(",")
			for j in range(len(aLine)):
				if not j==0: aLine[j]=aLine[j].strip()
			theLength=len(aLine)
			if theLength>5: del aLine[5:theLength] #if it is too long, just chop it
			#if too short, make it longer
			if theLength<5:
				toAdd=5-theLength
				for k in range(toAdd):
					aLine.append("0.0")
			aLine= map(correctType, aLine)
			seedPlacementList[i]=aLine
		i=i+1
	i=0
	printErrorMessage=0
	for aLine in seedPlacementList:
		if aLine=="":
			del seedPlacementList[i]
			i=i+1
		elif not type(aLine[0])==str or not type(aLine[1])==float or not type(aLine[2])==float or not type(aLine[3])==int or not type(aLine[4])==float:
			printErrorMessage=1
			del seedPlacementList[i]
			i=i+1
	if printErrorMessage:
		print "***Improper seeding file format..."
		print "     Questionable lines will be ignored."
	return seedPlacementList
			

def correctSList(sList):
	startPopulationSize=thePrefs.startPopulationSize
	###this is probably a list###
	sList=sList[1:-1]
	sList=sList.split(",")
	sList=map(correctType, sList)
	i=0
	showSAlert1=0
	showSAlert2=0
	showSAlert3=0
	for x in sList:
		if i==0 and type(x)==int:
			#the first item is a number. This is not correct
			#insert the default species here
			showSAlert1=1
			showSAlert2=1
			sList.insert(0, "_random_")
		if i+1==len(sList) and type(sList[i])==str:
			#the last item in the list is a string
			#put a int after it
			showSAlert1=1
			showSAlert3=1
			sList.insert(i+1, thePrefs.startPopulationSize)
		elif type(sList[i])==str and type(sList[i+1])==str:
			#this is probably a two species names next to one another
			#insert a int between them
			showSAlert1=1
			showSAlert3=1
			sList.insert(i+1, thePrefs.startPopulationSize)
		elif type(sList[i])==int and type(sList[i-1])==int:
			showSAlert1=1
			showSAlert2=1
			sList.insert(i, "_random_")
		i=i+1
	if showSAlert1: print "***Improper seeding [list] format..."
	if showSAlert2: print "     Inserting random species..."
	if showSAlert3: print "     Inserting default starting population size..."
	if showSAlert1: print "        input set to: %s." % (sList)
	return sList
	
def main():
	#why do only these need to be reminded they are global?
	global simulationFile
	global theWorldSize
	global startPopulationSize
	global seedPlacement
	global sList
	
	#Import Psyco if possible
	try:
		import psyco
		psyco.log()
		psyco.full()
	except ImportError:
		pass
		
	CFDGtext=""
	
	####################################
	###experiments in importing events
	import yaml
	if os.path.exists(eventFile):
		print "***Loading event file: %s***" % (eventFile)
		theFile=open(eventFile)
		eventData=yaml.load(theFile)
		theFile.close
		eventTimes=eventData.keys()
	else:
		eventTimes=[]
	#####################################
	
	if debug==1: print "***debug is on***"

	theGarden= worldBasics.garden()
	theGarden.platonicSeeds={}
	theGarden.theRegions=[]

	
	####

	#########Check for multiple species. If none, use default
	fileList=os.listdir("Species")
	ymlList=[]
	pythonList=[]
	useDefaultYml=True
	print "***Checking for species...***"
	for file in fileList:
		theExtension=os.path.splitext(file)[1]
		if theExtension==".yml":
			#add this file to the list of yaml files
			ymlList.append(file)
			useDefaultYml=False
		elif theExtension==".py":
			#this might be override info for a species
			#add this file to the list of species python files
			#this isn't implemented
			pythonList.append(file)
	fileList=[]
	##########

	if resumeSim==1 and not simulationFile=="":
		simulationFile=open(simulationFile, 'r')
		theGarden=pickle.load(simulationFile)
		simulationFile.close()
		theWorldSize=theGarden.theWorldSize
		print "***Resuming Simulation: %s as %s***" % (theGarden.name, simulationName)
		theGarden.name=simulationName
		startPopulationSize=theGarden.numbPlants
		##this should reload species data.
		###Important if you want to compare runs
		if reloadSpeciesData==1:
			###fileLoc will be different for each species eventually
			fileLoc="Vida_Data/Default_species.txt"
			for item in theGarden.soil:
				item.importPrefs(fileLoc)
	else:
		theGarden.makePlatonicSeedDict(ymlList, Species1)
		print "***Species loaded.***"
		theGarden.name=simulationName
		theGarden.theWorldSize=theWorldSize
		print "***Beginning Simulation: %s***" % (simulationName)

	theGarden.showProgressBar=showProgressBar

	print "     World size: %ix%i" % (theWorldSize, theWorldSize)
	print "     Maximum population size will be: %i" % (maxPopulation)
	print "              and"
	print "     Running simulation for %i cycles" % (maxCycles)
	print "              (whichever comes first)"
	print "     Starting population size: %i" % (startPopulationSize)
	if theGarden.carbonAllocationMethod==0:
		print "     Plants will allocate carbon to stem and leaf using methods defined by the species."
	else:
		print "     All plants will allocate carbon to stem and leaf using method %i" % (theGarden.carbonAllocationMethod)

	print ""
	if produceGraphics==1: 
		print "     Graphical output will be produced."
		if theView==1:
			print "       Graphical output will be a bottom-up view."
		elif theView==2:
			print "       Graphical output will be a top-down view."
		elif theView==3:
			print "       Graphical output will be a side-view."
		elif theView==12:
			print "       Graphical output will be a combination bottom-up and top-down view."
		elif theView==21:
			print "       Graphical output will be a combination top-down and bottom-up view."
		elif theView==23:
			print "       Graphical output will be a combined top-down and side view."
		elif theView==13:
			print "       Graphical output will be a combined bottom-up and side view."
		elif theView==123:
			print "       Graphical output will be a combination bottom-up, top-down and side view."
		if produceVideo==1:
			print "       Graphical output will include a %s frame/second video." % (framesPerSecond)
	###I think this is where to start the times to repeat bit
	for x in range(timesToRepeat):
		###make necessary directories
		outputDirectory="Output-"+simulationName+"/"
		outputDirectory=makeDirectory(outputDirectory)
		if produceGraphics==1 or produceDXFGraphics==1:
			outputGraphicsDirectory = outputDirectory +"Graphics/"
			makeDirectory(outputGraphicsDirectory)
			if produceDXFGraphics==1:
				outputDXFGraphicsDirectory = outputGraphicsDirectory +"DXF/"
				makeDirectory(outputDXFGraphicsDirectory)
			####SUPER IMPORTANT!!!!
			####DON'T USE SPACES IN DIR NAMES!
			####COMMAND LINES HATE THAT SHIT
			if theView==1:
				outputGraphicsDirectory = outputGraphicsDirectory +"bottom-up/"
				makeDirectory(outputGraphicsDirectory)
			elif theView==2:
				outputGraphicsDirectory = outputGraphicsDirectory +"top-down/"
				makeDirectory(outputGraphicsDirectory)
			elif theView==3:
				outputGraphicsDirectory = outputGraphicsDirectory +"side/"
				makeDirectory(outputGraphicsDirectory)
			elif theView==12:
				outputGraphicsDirectory = outputGraphicsDirectory +"combined-bottom-top/"
				makeDirectory(outputGraphicsDirectory)
			elif theView==21:
				outputGraphicsDirectory = outputGraphicsDirectory +"combined-top-bottom/"
				makeDirectory(outputGraphicsDirectory)
			elif theView==13:
				outputGraphicsDirectory = outputGraphicsDirectory +"combined-bottom-side/"
				makeDirectory(outputGraphicsDirectory)
			elif theView==23:
				outputGraphicsDirectory = outputGraphicsDirectory +"combined-top-side/"
				makeDirectory(outputGraphicsDirectory)
			elif theView==123:
				outputGraphicsDirectory = outputGraphicsDirectory +"combined-bottom-top-side/"
				makeDirectory(outputGraphicsDirectory)
		if not archive=="n":
			saveDirectory = outputDirectory+"Save_points/"
			makeDirectory(saveDirectory)
		if not saveData=="n":
			dataDirectory = outputDirectory+"Simulation_data/"
			makeDirectory(dataDirectory)
			makeDirectory(dataDirectory+"Seeds/")
			makeDirectory(dataDirectory+"Plants/")
			makeDirectory(dataDirectory+"Corpses/")


		
		if resumeSim==0:
			#2008.11.06 Moved a huge block of code related to placing seeds to vworldr.py
			theGarden.placeSeed(seedPlacement, sList, startPopulationSize, useDefaultYml, ymlList)
		if produceGraphics and CFDGtext=="": 
			CFDGtext=outputGraphics.initCFDGText(theGarden, theView, percentTimeStamp, 50.0)	
		#######
		cycleNumber=0
		print "\n***Running simulation.***"
		if not showProgressBar and not runningInNodeBox:
			theProgressBar= progressBarClass.progressbarClass(maxCycles,"*") #why -1? because index 0. So if total=100, 0-99.
		#print "Cycle, plant age, Mass Stem, Mass Leaf, # Seeds, Mass all Seeds, Radius Stem, Radius Leaf, Height Plant, areaPhoto, new mass"
		while (theGarden.numbPlants<=maxPopulation and cycleNumber<=maxCycles) and (theGarden.numbPlants+theGarden.numbSeeds)>0:
			###################################################################################
			####Experimental scripting event stuff                                            #
			if cycleNumber in eventTimes:                                                     # 
				for aItem in eventData[cycleNumber]:                                          #
					for aKey in aItem.keys():                                                 #
						if aKey=="Garden":                                                    #
							if debug==1: print "debug: A garden related event has been triggered."   #
							theDict=aItem[aKey][0]                                            #
							gardenAttrs=theDict.keys()                                        #
							for theGardenAttr in gardenAttrs:                                 #
								setattr(theGarden, theGardenAttr, theDict[theGardenAttr])     #
							gardenAttrs=""	
						elif aKey=="Killzone" or aKey=="Safezone":
							if debug==1: print "debug: generation of a zone event has been triggered."
							theDict=aItem[aKey][0]                                           #
							zoneAttrs=theDict.keys()
							zoneX=float(theDict['x'])
							zoneY=float(theDict['y'])
							zoneSize=float(theDict['size'])
							zoneShape=theDict['shape']
							if zoneShape not in ['circle','square']:
								print "***WARNING: improper zone shape defined. Defaulting to square.***"
								zoneShape='square'
							zoneTarget=theDict['target']
							if zoneTarget not in ['all','plants','seeds']:
								print "***WARNING: improper zone target defined. Defaulting to all.***"
								zoneTarget='all'
							if zoneShape=='circle':
								killThese=[]
								for theObject in theGarden.soil:
									if theObject.isSeed:
										r=theObject.radiusSeed
									else:
										r=theObject.radiusStem
									theResult=geometry_utils.checkOverlap(theObject.x, theObject.y, r, zoneX, zoneY, zoneSize)
									if theResult>0 and aKey=='Killzone':
										if zoneTarget=='all' or (theObject.isSeed and zoneTarget=='seeds') or (not theObject.isSeed and zoneTarget=='plants'):
											killThese.append(theObject)	
									elif aKey=='Safezone':
										if theResult==0:
											killThese.append(theObject)
										elif theResult>0:
											if (theObject.isSeed and zoneTarget=='plants') or (not theObject.isSeed and zoneTarget=='seeds'):
												killThese.append(theObject)	
																				
								for theObject in killThese:
									theObject.causeOfDeath="zone"
									theGarden.kill(theObject)
						elif aKey=="Seed":
							if debug==1: print "debug: A seeding related event has been triggered."   #
							theDict=aItem[aKey][0]                                            #
							seedingInfo=theDict.keys()                                        #
							for infoItem in seedingInfo:
								if infoItem=="number" and not seedPlacement=="fromFile": startPopulationSize=theDict[infoItem]
								if infoItem=="species": 
									sList=theDict[infoItem]
									if sList=="random": sList=[]
								if infoItem=="placement": seedPlacement=theDict[infoItem]
								if seedPlacement=="hexagon": seedPlacement="hex" #just make sure it is consistant
								if os.path.isfile(seedPlacement):
									theFile=open(seedPlacement)
									try:
										sList=theFile.readlines()
									finally:
										theFile.close()
									sList=checkSeedPlacementList(sList)
									startPopulationSize=len(sList)
									seedPlacement="fromFile"
							if not seedPlacement=="fromFile" and not sList==[]:
								newList=[]
								for j in range(startPopulationSize):
									newList.append(sList)
								#print sList
								sList=newList
								newList=[]
								#print sList
							theGarden.placeSeed(seedPlacement, sList, startPopulationSize, useDefaultYml, ymlList)
						elif aKey=="Region":
							if debug: print "debug: Region event detected..."
							theDict=aItem[aKey][0] 
							regionAttrs=theDict.keys()
							theRegionName=str(theDict['name'])
							if debug: print "debug: Region %s event detected." % (theRegionName)
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
										if debug: print "debug: Region %s has had a change in one or more attributes." % (theRegionName)
										updatePlants=True
										break
								#if (not theRegion.size==theDict["size"]) or (not theRegion.x==theDict["x"]) or (not theRegion.y==theDict["y"]) or (not theRegion.shape==theDict["shape"]):
								#	if debug:print "debug: a region has changed shape, size or location"
								#	updatePlants=True
								##now just read in the values#
								if debug: print "debug: Updating attributes for region %s." % (theRegionName)
								for theRegionAttr in regionAttrs:                                 #
									setattr(theRegion, theRegionAttr, theDict[theRegionAttr])     #
								if updatePlants:
									if debug:print "debug: updating plants with changed region info"
									for aPlant in theGarden.soil:
										plantX=aPlant.x
										plantY=aPlant.y
										if theRegion.shape=='square':
											inSubregion=geometry_utils.pointInsideSquare(theRegion.x, theRegion.y, theRegion.size, plantX, plantY)
										elif theRegion.shape=='circle':
											#size needs to be radius but region defines diameter
											inSubregion=geometry_utils.pointInsideCircle(theRegion.x, theRegion.y, theRegion.size/2.0, plantX, plantY)
										if inSubregion:
											if not theRegion in aPlant.subregion:
												aPlant.subregion.append(theRegion)
												#print "\nX: %f  Y: %f  In region: %s" % (plantX, plantY, newRegion)

								#print theRegion.size
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
								if debug: print "debug: Making attributes for region"
								for theRegionAttr in regionAttrs:                                 #
									setattr(newRegion, theRegionAttr, theDict[theRegionAttr])     #
								theGarden.theRegions.append(newRegion)
								for aPlant in theGarden.soil:
									plantX=aPlant.x
									plantY=aPlant.y
									if newRegion.shape=='square':
										inSubregion=geometry_utils.pointInsideSquare(newRegion.x, newRegion.y, newRegion.size, plantX, plantY)
									elif newRegion.shape=='circle':
										#size needs to be radius but region defines diameter
										inSubregion=geometry_utils.pointInsideCircle(newRegion.x, newRegion.y, newRegion.size/2.0, plantX, plantY)
									if inSubregion:
										if not newRegion in aPlant.subregion:
											aPlant.subregion.append(newRegion)
											#print "\nX: %f  Y: %f  In region: %s" % (plantX, plantY, newRegion)
										
								newRegion=""
							
							
						theDict=[]#just clear this to free up the memory
			###################################################################################
			theGarden.cycleNumber=cycleNumber
			if not showProgressBar and not runningInNodeBox:
					theProgressBar.update(cycleNumber)
			#print "%i, %i, %f, %f, %i, %f, %f, %f, %f, %f, %f" % (cycleNumber-1, theGarden.soil[0].age, theGarden.soil[0].massStem, theGarden.soil[0].massLeaf, len(theGarden.soil[0].seedList), theGarden.soil[0].massSeedsTotal, theGarden.soil[0].radiusStem, theGarden.soil[0].radiusLeaf, theGarden.soil[0].heightStem+theGarden.soil[0].heightLeafMax, theGarden.soil[0].areaPhotosynthesis, theGarden.soil[0].massFixed)

			###START OF SEEING CHANGES TO SPECIES FOLDER
			#########Check for multiple species. If none, use default
			fileList=os.listdir("Species")
			#print fileList
			#ymlList=[]
			#print "***Checking for species...***"
			#for file in fileList:
			#	theExtension=os.path.splitext(file)[1]
			#	if theExtension==".yml":
			#		#add this file to the list of yaml files
			#		ymlList.append(file)
			#		useDefaultYml=False
			#fileList=[]
			##########





			if debug==1: print "number of plants: "+str(theGarden.numbPlants)
			if debug==1: print "number of seeds: "+str(theGarden.numbSeeds)
			
			#generate graphics if requested
			if produceDXFGraphics:
				theData=vdxfGraphics.makeDXF(theGarden)
				theFileName= simulationName+str(cycleNumber)
				vdxfGraphics.writeDXF(outputDXFGraphicsDirectory, theFileName, theData)
			if produceGraphics:
				theData=outputGraphics.makeCFDG(theView, CFDGtext, theGarden, cycleNumber)
				if webOutput==0:
					if theView==1:
						cfdgFileName= simulationName +"-bottom-"+str(cycleNumber)
					elif theView==2:
						cfdgFileName= simulationName +"-top-"+str(cycleNumber)
					elif theView==3:
						cfdgFileName= simulationName +"-side-"+str(cycleNumber)
					elif theView==12:
						cfdgFileName= simulationName +"-bottom-top-"+str(cycleNumber)
					elif theView==21:
						cfdgFileName= simulationName +"-top-bottom-"+str(cycleNumber)
					elif theView==13:
						cfdgFileName= simulationName +"-bottom-side-"+str(cycleNumber)
					elif theView==23:
						cfdgFileName= simulationName +"-top-side-"+str(cycleNumber)
					elif theView==123:
						cfdgFileName= simulationName +"-bottom-top-side"+str(cycleNumber)
					outputGraphics.writeCFDG(outputGraphicsDirectory, cfdgFileName, theData)
				else:
					cfdgFileName= simulationName
					outputGraphics.writeCFDG(outputGraphicsDirectory, cfdgFileName, theData)
					outputGraphics.outputPNGs(outputGraphicsDirectory, webDirectory)
					#outputGraphics.deleteCFDGFiles(outputGraphicsDirectory)

			###go through the soil list and germinate seed or grow plant
			if theGarden.showProgressBar:
				print"***Allowing plants a turn to grow***"
				theProgressBar= progressBarClass.progressbarClass(len(theGarden.soil),"*")
				theBar=0
			for obj in theGarden.soil[:]:
				if obj.isSeed:
					obj.germinate(theGarden)
				else:
					obj.growPlant(theGarden)
				if theGarden.showProgressBar:
					theBar=theBar+1
					theProgressBar.update(theBar)

			###deal with violaters of basic physics
			theGarden.causeRandomDeath()
			theGarden.checkSenescence()
			theGarden.removeOffWorldViolaters()
			theGarden.removeEulerGreenhillViolaters()
			theGarden.removeOverlaps()
			

			###sort the garden.soil by height of the plants.Ordered shortest to tallest
			theGarden.soil= list_utils.sort_by_attr(theGarden.soil, "heightStem")
			###flip the list so it's ordered tallest to shortest
			theGarden.soil.reverse()

			###work out shading
			worldBasics.determineShade(theGarden)

			###Calculate the amount of carbon each plant will have to start the next turn
			if theGarden.showProgressBar:
				print "***Calculating new mass from photosynthesis***"
				theProgressBar= progressBarClass.progressbarClass(len(theGarden.soil),"*")
				i=0
			for plant in theGarden.soil[:]:
				if plant.isSeed==False:
					plant.massFixed=plant.calcNewMassFromLeaf(theGarden)
					if plant.massFixed==-1.0:
						plant.causeOfDeath="lack of light"
						theGarden.kill(plant)
					else:
						plant.massFixedRecord.append(plant.massFixed)
						while len(plant.massFixedRecord)>plant.numYearsGrowthMemory:
							plant.massFixedRecord.pop(0)
				if theGarden.showProgressBar:
					i=i+1
					theProgressBar.update(i)




			if archive=="a":
				fileName=simulationName+'-'+str(cycleNumber)+'.pickle'
				saveSimulationPoint(saveDirectory, fileName, theGarden)

			if saveData=="a":
				fileName=simulationName+'-'+str(cycleNumber)+'.csv'
				saveDataPoint(dataDirectory, fileName, theGarden)
			#print theGarden.deathNote
			theGarden.deathNote=[]		
			
			cycleNumber= cycleNumber+1

			###pause if you're making web graphic
			#if webOutput==1:
			#	time.sleep(5)

		if archive=="e":
			fileName=simulationName+'-'+str(cycleNumber)+'.pickle'
			saveSimulationPoint(saveDirectory, fileName, theGarden)

		if saveData=="e":
				fileName=simulationName+'-'+str(cycleNumber)+'.csv'
				saveDataPoint(dataDirectory, fileName, theGarden)
				
							
		if produceStats:
			#print dataDirectory
			theArgument="-n '%s' -fs" % (dataDirectory+"Seeds/")
			print "***sending to Extract: %s" % (theArgument)
			os.system("python Vida_Data/vextract.py %s" % (theArgument))
			theArgument="-n '%s' -fs" % (dataDirectory+"Plants/")
			print "***sending to Extract: %s" % (theArgument)
			os.system("python Vida_Data/vextract.py %s" % (theArgument))
			theArgument="-n '%s' -fs" % (dataDirectory+"Corpses/")
			print "***sending to Extract: %s" % (theArgument)
			os.system("python Vida_Data/vextract.py %s" % (theArgument))


		###final graphics calls
		if produceGraphics==1 and webOutput==0: 
			print "Producing PNG files..."
			outputGraphics.outputPNGs(outputGraphicsDirectory, outputGraphicsDirectory)
		if produceGraphics==1 and deleteCfdgFiles==1 and webOutput==0:
			print "Deleting .cfdg files..."
			outputGraphics.deleteCFDGFiles(outputGraphicsDirectory)

		###only try and make a video if it is wanted and if pngs were made
		if produceVideo and produceGraphics and webOutput==0:
			print "Producing MOV file..." 
			outputGraphics.outputMOV(outputGraphicsDirectory, simulationName, framesPerSecond)
		print "*****Simulation Complete*****"
		#print theGarden.deathNote
		#clear the values
		theGarden.soil=[]
		theGarden.deathNote=[]
		theGarden.cycleNumber=0
		for aRegion in theGarden.theRegions:
			aRegion.size=0.0
		#print theGarden.theRegions[0].size
	###And this would be the end of the loop bit

		
				
if __name__ == '__main__':
	#This section could use some serious fixing. The parsing is very kludgy
	
	######Read in any run time arguments provided
	print ""
	theArguments=sys.argv
	specifiedSeedPlaces=0
	seedPlacement="random"
	###Turn on debug output text
	if "-d" in theArguments:
		debug=1
	if "-dd" in theArguments:
		debug2=1
		debug=0
	if "-n" in theArguments:
		loc= theArguments.index("-n")
		simulationName=theArguments[loc+1]
	##########################
	if "-g" in theArguments:
		produceGraphics=1
		theView=1
	if "-gb" in theArguments:
		produceGraphics=1
		theView=1
	if "-gt" in theArguments:
		produceGraphics=1
		theView=2
	if "-gs" in theArguments:
		produceGraphics=1
		theView=3
	if "-gts" in theArguments or "-gst" in theArguments:
		produceGraphics=1
		theView=23
	if "-gbs" in theArguments or "-gsb" in theArguments:
		produceGraphics=1
		theView=13
	if "-gbt" in theArguments:
		produceGraphics=1
		theView=12
	if "-gtb" in theArguments:
		produceGraphics=1
		theView=21
	if "-gbts" in theArguments:
		produceGraphics=1
		theView=123
	if "-g3d" in theArguments:
		import vdxfGraphics
		produceDXFGraphics=1
	##########################
	if "-o" in theArguments:
		produceGraphics=1
		webOutput=1
	if "-v" in theArguments:
		produceVideo=1
		loc= theArguments.index("-v")
		if (len(theArguments)-1)>=(loc+1):
			if theArguments[loc+1].isdigit():
				framesPerSecond=int(theArguments[loc+1])
	if "-c" in theArguments:
		deleteCfdgFiles=0
	if "-p" in theArguments:
		deletePngFiles=1
	if "-w" in theArguments:
		loc= theArguments.index("-w")
		theWorldSize=int(theArguments[loc+1])
	if "-rl" in theArguments:
		loc= theArguments.index("-rl")
		simulationFile=theArguments[loc+1]
		resumeSim=1
		reloadSpeciesData=1
	if "-r" in theArguments:
		loc= theArguments.index("-r")
		simulationFile=theArguments[loc+1]
		resumeSim=1
	###load in the events file###
	if "-e" in theArguments:
		loc= theArguments.index("-e")
		eventFile=theArguments[loc+1]
		
	###Seed placement###
	if "-s" in theArguments or "-sh" in theArguments or "-ss" in theArguments:
		if "-s" in theArguments:
			seedPlacement="random"
			loc=theArguments.index("-s")
		elif "-sh" in theArguments:
			seedPlacement="hex"
			loc=theArguments.index("-sh")
		elif "-ss" in theArguments:
			seedPlacement="square"
			loc=theArguments.index("-ss")
		sList=theArguments[loc+1]
		#print sList
		if (len(theArguments)-1)>=(loc+1):
			if sList.isdigit():
				startPopulationSize=int(sList)
				sList=[]
			elif sList[0]=="[" and sList[-1]=="]":
				#print "here"
				###it is probably a list
				sList=correctSList(sList)
				###figure out what the total population count is
				for x in sList:
					if type(x) is int:
						startPopulationSize=startPopulationSize+x
				if not startPopulationSize==thePrefs.startPopulationSize:
					startPopulationSize=startPopulationSize-thePrefs.startPopulationSize
				###expand the list so you have correct numbers of each species
				###this makes the list compatable with existing seeding routines					
				k=1
				newList=[]
				for i in range(len(sList)/2):
					for j in range(sList[k]):
						newList.append(sList[k-1])
					k=k+2
				sList=newList
				newList=[]
				###mix up the list if you have multiple species
				if not sList.count(sList[0])==len(sList):
					random.shuffle(sList)
				
		
		
	#if "-sl" in theArguments:
	#	###Be nice to have a -sf to load x,y from a file
	#	###Make it a tupple with x,y,species so you can seed multiple species
	#	loc= theArguments.index("-sl")
	#	theInput=theArguments[loc+1]
	#	if theInput[0]=="[" and theInput[-1]=="]":
	#		###this is probably a list###
	#		theInput=theInput[1:-1]
	#	theInput=theInput.split(",")
	#	seedPlacementList= map(correctType, theInput)
	#	print seedPlacementList
	#	#print seedPlacementList
	#	seedPlacement="argumentList"

	if "-sf" in theArguments:
		print "***Attempting to load plant placement file...***"
		loc= theArguments.index("-sf")
		seedPlacementFile=theArguments[loc+1]
		if os.path.isfile(seedPlacementFile):
			theFile=open(seedPlacementFile)
			try:
				sList=theFile.readlines()
			finally:
				theFile.close()
			##send the file off to make sure it's in the correct format
			sList=checkSeedPlacementList(sList)
			startPopulationSize=len(sList)
			seedPlacement="fromFile"
			print "***Plant placement file loaded.***"
			#print sList
		else:
				seedPlacement="random"
				startPopulationSize=int(sList)
				sList=[]
		

	################
	if "-m" in theArguments:
		loc= theArguments.index("-m")
		maxPopulation=abs(int(theArguments[loc+1]))
	if "-t" in theArguments:
		loc= theArguments.index("-t")
		maxCycles=abs(int(theArguments[loc+1]))
	if "-i" in theArguments:
		loc= theArguments.index("-i")
		percentTimeStamp=abs(int(theArguments[loc+1]))
	if "-aa" in theArguments:
		archive="a"##archive all
	if "-ae" in theArguments:
		archive="e"##archive end only
	if "-an" in theArguments:
		archive="n"##archive nothing
	if "-a" in theArguments:
		loc= theArguments.index("-a")
		archive=int(theArguments[loc+1])
	if "-fa" in theArguments:
		saveData="a"##archive all
	if "-fe" in theArguments:
		saveData ="e"##archive end only
	if "-fn" in theArguments:
		saveData ="n"##archive nothing
	if "-f" in theArguments:
		loc= theArguments.index("-f")
		saveData =int(theArguments[loc+1])
	if "-fa" in theArguments:
		produceStats=1
	if "-b" in theArguments:
		if runningInNodeBox:
			print"***Vida running within NodeBox. Progress bar is disabled.***"
			showProgressBar=0
		else:
			showProgressBar=1
	if "-x" in theArguments:
		loc= theArguments.index("-x")
		timesToRepeat=int(theArguments[loc+1])
	if "-?" in theArguments:
		print """
Usage: 
scriptName [options]


***These options need to be updated***
Options: 
    -d        turn basic debugging text on.
    -dd       turn on debugging for accessory subroutines and basic debugging.
    -n str    simulation name.Default simulation name is 'default'.
    -g        graphical output
    -c        delete .cfdg files after .pngs files made.
    -p        NOT IMPLEMENTED.delete .png files after .mov made.
    -v        produce a quicktime movie of the simulation.
    -i        how large to make the time stamp text.This is a size in %.Default is 2.5%.
    -s int    number of seeds to begin the simulation with.
              Default is 1.
    -m int    Maximum population.
    -t int    Time to run simulation for(number of cycles).
              Note: -m and -t can be combined to end the simulation after a given time or when a population is reached.
    -w int    world size in meters.Default is 200.
              A value of 200 results in a world 200x200.
    -?        show this message.
              NOTE IT SHOULD SHOW THIS AND THEN EXIT, BUT DOESN'T
"""
	main()
else:
	main()
	
	


		
