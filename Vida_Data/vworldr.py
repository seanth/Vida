"""This file is part of Vida.
    --------------------------
    Copyright 2019, Sean T. Hammond
    
    Vida is experimental in nature and is made available as a research courtesy "AS IS," but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 
    
    You should have received a copy of academic software agreement along with Vida. If not, see <http://iorek.ice-nine.org/seant/Vida/license.txt>.
    """

import sys
import math
import random
import time
import copy
import uuid
###append the path to basic data files
sys.path.append("Vida_Data")
import geometry_utils
import list_utils
import yaml
import progressBarClass


debug1=0
debug2=0

def determineShade(theGarden):
    if theGarden.showProgressBar:
        print "***Generating lists of overlapping plants. This could take a while...***"
        theProgressBar= progressBarClass.progressbarClass(len(theGarden.soil),"*")
        i=0
    ###populate the overlap list
    theIndex=0
    for plantOne in theGarden.soil:
        if plantOne.isSeed==0 or (plantOne.isSeed and plantOne.minimumLightForGermination>0.0):
            plantOne.overlapList=[]
            plantOne.areaCovered=0.0
            plantOne.colourLeaf[2]= 1.0
            ###the following might be able to be used to speed things up
            #for overlappingItem in plantOne.overlapList:
            #    if not overlappingItem in theGarden.soil or not overlappingItem.z>plantOne.z: 
            #        ###make sure the overlapping item is still alive
            #        ###and that overlapping item is still taller
            #        plantOne.overlapList.remove(overlappingItem)
            ###need to insert something so tallest plant looks at all the other plants of exactly the same size
            ###if they are the same size and overlapping, they need to share shading
            for plantTwo in range(theIndex):
                plantTwo=theGarden.soil[plantTwo]
                ###is plant two overlapping you?
                overlapStatus=geometry_utils.checkOverlap(plantOne.x, plantOne.y, plantOne.r, plantTwo.x, plantTwo.y, plantTwo.r)
                if overlapStatus>0:
                    if not plantTwo in plantOne.overlapList:
                        if not plantTwo==plantOne:
                            plantOne.overlapList.append(plantTwo)
            ###sort the overlap list by height of the plants. Ordered shortest to tallest
            plantOne.overlapList = list_utils.sort_by_attr(plantOne.overlapList, "heightStem")
            ###flip the list so it's ordered tallest to shortest
            plantOne.overlapList.reverse()
            theIndex=theIndex+1
            if theGarden.showProgressBar:
                i=i+1
                theProgressBar.update(i)
    
    ###take the overlap list and start dropping photons onto it.
    if theGarden.showProgressBar:
        print "***Determining shading. This could take a while...***"
        theProgressBar= progressBarClass.progressbarClass(len(theGarden.soil),"*")
        i=0
    for plant in theGarden.soil:
        if plant.isSeed==0 or (plant.isSeed and plant.minimumLightForGermination>0.0):
            fractionExposed=1.0
            if len(plant.subregion)>0:
                theRegion=plant.subregion[-1]
            else:
                theRegion=theGarden
            if len(plant.overlapList)>0:
                thePlantAreaTotal=geometry_utils.areaCircle(plant.r)
                if thePlantAreaTotal==0.0:
                    print "name:%s r:%f isSeed:%i massSeed:%f massTotal:%f"%(plant.name, plant.r, plant.isSeed, plant.massSeed, plant.massTotal)
                if len(plant.overlapList)==1: ###if you are covered by just 1 other, do a direct calc
                    overPlant =plant.overlapList[0]
                    areaCovered=geometry_utils.areaOverlappingCircles(plant.x, plant.y, plant.r, overPlant.x, overPlant.y, overPlant.r)
                    areaCovered=areaCovered-(areaCovered*plantTwo.canopyTransmittance)
                    thePlantAreaExposed=thePlantAreaTotal-areaCovered
                    #plant.areaCovered=areaCovered
                    fractionExposed= thePlantAreaExposed/thePlantAreaTotal
                    #fractionExposed=fractionExposed*theGarden.lightIntensity #try and take into account overall world light intensity
                    fractionExposed=fractionExposed*theRegion.lightIntensity #try and take into account overall world light intensity
                    thePlantAreaExposed= thePlantAreaTotal*fractionExposed
                    plant.areaCovered=thePlantAreaTotal-thePlantAreaExposed
                elif len(plant.overlapList)>1: ###if you are covered by 2, use monte-carlo
                    numbPhotons=int(thePlantAreaTotal)
                    if numbPhotons==0:
                        numbPhotons=1
                    numbPhotons= numbPhotons*100
                    if numbPhotons>750: #we don't need monster numbers
                        numbPhotons=750
                    hitCount=0
                    for photon in range(numbPhotons):
                        #####consider moving this to geometry_utils
                        ###pick uniformly distributed point in a circle
                        randr=(random.random()*(plant.r-0))+0 #random between 0 and the radius
                        twoPi=math.pi*2
                        randAngle=random.random()*twoPi
                        #randr =math.sqrt(randr) #if you don't use sqrt, you get clustering in the center
                        randr =randr**0.5 #if you don't use sqrt, you get clustering in the center
                        photonX = (randr*math.cos(randAngle))+plant.x
                        photonY = (randr*math.sin(randAngle))+plant.y
                        ######
                        for overPlant in plant.overlapList:
                            if not photonX=="gone":
                                if geometry_utils.pointInsideCircle(overPlant.x, overPlant.y, overPlant.r, photonX, photonY):
                                    randomValue=random.random()
                                    if randomValue > overPlant.canopyTransmittance:
                                        ###these points are where the overlap is
                                        photonX="gone"
                                    break
                        if not photonX=="gone":
                            hitCount=hitCount+1
                    if numbPhotons ==0:
                        fractionExposed=0.0
                    else:
                        fractionExposed=float(hitCount)/float(numbPhotons)
                    #fractionExposed=fractionExposed*theGarden.lightIntensity #try and take into account overall world light intensity
                    fractionExposed=fractionExposed*theRegion.lightIntensity #try and take into account overall world light intensity
                    thePlantAreaExposed= thePlantAreaTotal*fractionExposed
                    plant.areaCovered=thePlantAreaTotal-thePlantAreaExposed
            else: #if you are not covered at all
                thePlantAreaTotal=geometry_utils.areaCircle(plant.r)
                fractionExposed=1.0
                #fractionExposed=fractionExposed*theGarden.lightIntensity #try and take into account overall world light intensity
                fractionExposed=fractionExposed*theRegion.lightIntensity #try and take into account overall world light intensity
                thePlantAreaExposed= thePlantAreaTotal*fractionExposed
                plant.areaCovered=thePlantAreaTotal-thePlantAreaExposed
            ###now change the colour accordingly
            plant.colourLeaf[2]= fractionExposed
        if theGarden.showProgressBar:
            i=i+1
            theProgressBar.update(i)



class garden(object):
    def __init__(self):
        super(garden, self).__init__()
        self.name=""
        self.theWorldSize=0
        self.soil=[]
        self.numbSeeds=0
        self.numbPlants=0
        self.deathNote=[]
        self.cycleNumber=0
        self.lightIntensity=1.0
        fileLoc="Vida World Preferences.yml"
        self.importPrefs(fileLoc)
        if self.lightIntensity>1.0: self.lightIntensity=1.0
    
    def importPrefs(self, fileLoc):
        theFile=open(fileLoc)
        theData=yaml.load(theFile)
        theFile.close
        for key in theData:
            setattr(self, key, theData[key])
    
    def makePlatonicSeedDict(self, ymlList, Species1):
        theGarden=self
        i=0
        for s in ymlList:
            theSeed=Species1()
            fileLoc= "Species/"+ymlList[i]
            theSeed.importPrefs(fileLoc)
            #theSeed.name="Platonic %s" % (ymlList[i])
            theGarden.platonicSeeds[ymlList[i]]=theSeed
            i=i+1
    
    
    def plantSeed(self, theSeed):
        #self=garden, obj=seed
        theGarden=self
        theNameList= theSeed.name.split()
        #if len(theNameList)<2:
        #    idNumb=str(random.random())
        #else:
        #    idNumb=theNameList[1]
        theSeed.timePlanted=time.time()
        #theSeed.name="plantedSeed %s" % (idNumb)
        theSeed.name=str(uuid.uuid4())
        if theSeed.motherPlant==0:
            theSeed.motherPlant=theSeed
            theSeed.motherPlantName=theSeed.name
        theGarden.soil.append(theSeed)
        theGarden.numbSeeds=self.numbSeeds+1
        #####If there are subregions defined, see what subregion does it belong in this seed belongs
        #print "the Garden: %s" % (theGarden)
        #print "the region: %s" % (theGarden.theRegions)
        if len(theGarden.theRegions)>0:
            for aRegion in theGarden.theRegions:
                #print aRegion.name
                #print theSeed.name
                if aRegion.shape=='square':
                    inSubregion=geometry_utils.pointInsideSquare(aRegion.x, aRegion.y, aRegion.size, theSeed.x, theSeed.y)
                elif aRegion.shape=='circle':
                    #size needs to be radius but region defines diameter
                    inSubregion=geometry_utils.pointInsideCircle(aRegion.x, aRegion.y, aRegion.size/2.0, theSeed.x, theSeed.y)
                if inSubregion:
                    if not aRegion in theSeed.subregion:
                        theSeed.subregion.append(aRegion)        
        return theSeed
    
    def kill(self, theObject):
        theGarden=self
        if theObject in self.soil:
            #die!
            if len(theObject.seedList)>0:
                for theSeed in theObject.seedList:
                    if theSeed.massSeed>0.0:
                        ###The plant has seeds. Drop them prior to killing plant###
                        ###just drop the seed straight down###
                        theSeed.countToGerm=theObject.delayInGermination
                        theGarden.plantSeed(theSeed)
                    theObject.seedList.remove(theSeed)
            theObject.seedList=[]
            if theObject.isSeed==1:
                self.numbSeeds=self.numbSeeds-1
            else:
                self.numbPlants=self.numbPlants-1
            self.deathNote.append(theObject)
            self.soil.remove(theObject)
    
    def calcEulerGreenhill(self, plant):
        theGarden=self
        #calculate the critial force at which a upright cylinder will deflect
        E=plant.youngsModulusStem*1000000000
        Ds=plant.radiusStem*2.0
        ps=plant.densityStem
        ###let the subregion the plan is in override the gravity###
        ###use only the final one if there are multiple###
        if len(plant.subregion)>0:
            g=plant.subregion[-1].gravity
        else:
            g=theGarden.gravity
        #r=plant.radiusStem
        #z=plant.z
        #Pacr=(math.pow(math.pi, 3)/16.0)*(math.pow(r, 4)/math.pow(z, 2))*E
        heightCritical= 0.79*((E/(g*ps))**0.3333)*(Ds**0.6667)
        #massCritical=0.785*ps*heightCritical*Ds*Ds
        #forceCritical=0.483736625*E*(Ds*Ds*Ds*Ds)
        #denom=(2.0*heightCritical)*(2.0*heightCritical)
        #forceCritical=forceCritical/denom
        return heightCritical
    
    def checkEulerGreenhillViolation(self, plant):
        theGarden=self
        if plant.isSeed==1: return 0 #don't check it if it's a seed.
        #theGravity=theGarden.gravity
        #if len(plant.subregion)>0:
        #    theGravity=plant.subregion[-1].gravity
        #determine if a plant violates the Euler-Greenhill rule
        #ps=plant.densityStem
        #Ds=plant.radiusStem*2.0
        heightCritical=self.calcEulerGreenhill(plant)
        ###
        #massCritical=0.785*ps*heightCritical*Ds*Ds
        #forceCritical=massCritical*theGravity
        #massTotal=plant.massTotal+plant.massSeedsTotal
        #theForce=massTotal*theGravity
        #if plant.heightStem>=heightCritical or massTotal>=massCritical or theForce>= forceCritical:
        if plant.heightStem>=heightCritical:
            #omg! violates euler-greenhill!
            return 1
        else:
            return 0
    
    def outOfBounds(self, theObject):
        ##returns 1 if out of bounds
        ##returns 0 if in bounds
        theGarden=self
        #if the object's radius goes off world, die
        if theObject.isSeed:
            r=theObject.radiusSeed
        else:
            r=theObject.radiusStem
        if theObject.x+r>theGarden.theWorldSize/2.0:
            return 1
        elif theObject.x-r<0.0-theGarden.theWorldSize/2.0:
            return 1
        elif theObject.y+r>theGarden.theWorldSize/2.0:
            return 1
        elif theObject.y-r<0.0-theGarden.theWorldSize/2.0:
            return 1
        else:
            return 0
    
    
    def checkForOverlap(self, theObject):
        #specialized routine for detecting overlaps
        #accepts an object (plant or seed)
        #looks at all objects to see if seeds or stems touch
        #returns a list of objects the query object is touching
        theGarden=self
        if theObject.isSeed:
            r=theObject.radiusSeed
        else:
            r=theObject.radiusStem
        theIndex=0
        theOverlapList=[]
        if len(theObject.overlapList)==0:
            listToCheck=theGarden.soil
        else:
            listToCheck=theObject.overlapList
        for anObject in listToCheck:
            if not anObject==theObject: #don't look at yourself thx
                if anObject.isSeed:
                    rr=anObject.radiusSeed
                else:
                    rr=anObject.radiusStem
                theOverlap=geometry_utils.checkOverlap(theObject.x, theObject.y, r, anObject.x, anObject.y, rr)
                if theOverlap==1 and anObject not in theOverlapList:
                    ##occupy same space or completely covered
                    theOverlapList.append(anObject)
                elif theOverlap==2 and anObject not in theOverlapList:
                    ###there is partial overlap
                    theOverlapList.append(anObject)
        return theOverlapList
    
    def removeOverlaps(self):
        if not self.allowOverlaps:
            theGarden=self
            if theGarden.showProgressBar:
                print "***Removing overlapping objects***"
                theProgressBar= progressBarClass.progressbarClass(len(theGarden.soil),"*")
                i=0
            for obj in theGarden.soil[:]:
                ###seeds and or stems that overlap are violating physics.
                ##Rules about overlapping objects:
                #####1.) If 2 objects overlap, the more massive object remains.
                #####2.) If 2 seeds overlap and they have the same mass, the oldest seed remains.
                objectList=theGarden.checkForOverlap(obj)
                for overlappingObject in objectList:
                    if obj.massTotal>overlappingObject.massTotal:
                        overlappingObject.causeOfDeath="crushed"
                        theGarden.kill(overlappingObject)
                        break
                    elif obj.massTotal<overlappingObject.massTotal:
                        obj.causeOfDeath="crushed"
                        theGarden.kill(obj)
                        break
                    elif obj.massTotal==overlappingObject.massTotal:
                        if obj.timePlanted>overlappingObject.timePlanted:
                            obj.causeOfDeath="overlap violation"
                            theGarden.kill(obj)
                            break
                        else:
                            obj.causeOfDeath="overlap violation"
                            theGarden.kill(overlappingObject)
                            break
                if theGarden.showProgressBar:
                    i=i+1
                    theProgressBar.update(i)
    
    def removeOffWorldViolaters(self):
        if not self.allowOffWorld:
            theGarden=self
            if theGarden.showProgressBar:
                print "***Removing plants growing off world...***"
                theProgressBar= progressBarClass.progressbarClass(len(theGarden.soil),"*")
                i=0
            ###see if plants or seeds extend over the edge of the world
            ### if so, kill them off
            for obj in theGarden.soil[:]:
                if theGarden.outOfBounds(obj)==1:
                    obj.causeOfDeath="stem off world"
                    theGarden.kill(obj)
                if theGarden.showProgressBar:
                    i=i+1
                    theProgressBar.update(i)
    
    def removeEulerGreenhillViolaters(self):
        if not self.allowEulerGreenhillViolations:
            theGarden=self
            if theGarden.showProgressBar:
                print "***Checking for Greenhill-Euler violations...***"
                theProgressBar= progressBarClass.progressbarClass(len(theGarden.soil),"*")
                i=0
            for obj in theGarden.soil[:]:
                if theGarden.checkEulerGreenhillViolation(obj)==1:
                    obj.causeOfDeath="violated Euler-Greenhill"
                    theGarden.kill(obj)
                if theGarden.showProgressBar:
                    i=i+1
                    theProgressBar.update(i)
    
    def causeRandomDeath(self):
        if self.allowRandomDeath:
            theGarden=self
            if theGarden.showProgressBar:
                print "***A time to die...***"
                theProgressBar= progressBarClass.progressbarClass(len(theGarden.soil),"*")
                i=0
            for obj in theGarden.soil[:]:
                tooBad=random.random()
                theRegion=theGarden
                if len(obj.subregion)>0:
                    #if there are multiple regions, only the most recently made one is used.
                    theRegion=obj.subregion[-1]
                if (obj.isSeed) and (tooBad<theRegion.randomDeathSeed):
                    obj.causeOfDeath="random death"
                    theGarden.kill(obj)
                if (not obj.isSeed) and (tooBad<theRegion.randomDeathPlant):
                    obj.causeOfDeath="random death"
                    theGarden.kill(obj)
                if theGarden.showProgressBar:
                    i=i+1
                    theProgressBar.update(i)
    
    def checkSenescence(self):
        if self.allowSlowGrowthDeath:
            theGarden=self
            if theGarden.showProgressBar:
                print "***Checking for too slow growth...***"
                theProgressBar= progressBarClass.progressbarClass(len(theGarden.soil),"*")
                i=0
            for obj in theGarden.soil[:]:
                if not obj.isSeed and obj.maxAvgHeightGrowthRate>0.0: #only look at growth if the object is a plant, not a seed.
                    fractOfMaxHeightGrowth=obj.avgHeightGrowthRate/obj.maxAvgHeightGrowthRate
                    if obj.randomSlowGrowth>fractOfMaxHeightGrowth or theGarden.randomSlowGrowth>fractOfMaxHeightGrowth:
                        #the garden defines a value at which plants will start to stochastically die
                        #each species also defines a value at which that species will start to stochastically die
                        #this way the garden can have a 'bad' environment that triggers problems earlier than a species might define
                        #to simulate a virus or something.
                        tooBad=random.random()
                        theRegion=theGarden
                        if len(obj.subregion)>0:
                            #if there are multiple regions, only the most recently made one is used.
                            theRegion=obj.subregion[-1]
                        chanceOfDeath=theRegion.randomDeathPlant
                        if tooBad<=chanceOfDeath:
                            obj.causeOfDeath="growth too slow"
                            theGarden.kill(obj)
                if theGarden.showProgressBar:
                    i=i+1
                    theProgressBar.update(i)
    
    #the following is purely experimental. Testing mortality related to distance from mother plant.
    #use the formula chanceOfDeath= ((1/(stddev*((2*3.14)^0.5)))*2.71)^-((((distance-average)^2))/((2*stddev)^2))
    #where average=0 and stddev=?
    def checkDistanceMortality(self):
        if self.allowDistanceFromMother and self.janzenConnell>0.0:
            theGarden=self
            if theGarden.showProgressBar:
                print "***Checking for mortality due to proximity to mother...***"
                theProgressBar= progressBarClass.progressbarClass(len(theGarden.soil),"*")
            #print "Name : Distance : Chance"
            for obj in theGarden.soil[:]:
                if not obj.isSeed:
                    twoPi=2.0*3.14
                    stddev=self.janzenConnell
                    theAvg=0.0
                    theDistance=geometry_utils.distBetweenPoints(obj.motherPlant.x, obj.motherPlant.y, obj.x, obj.y)
                    if theDistance>0.0:
                        theExponent=-(((theDistance-theAvg)**2.0)/((2.0*stddev)**2.0))
                        theDeathChance=((1/(stddev*(twoPi**0.5)))*2.71)**theExponent
                        #print "%s : %s :%s" % (obj.name, theDistance, theDeathChance)
                        tooBad=random.random()
                        if tooBad<theDeathChance:
                            obj.causeOfDeath="experimental death due to distance from mother"
                            theGarden.kill(obj)
                if theGarden.showProgressBar:
                    i=i+1
                    theProgressBar.update(i)
    
    
    
    
    def placeSeed(self, seedPlacement, sList, startPopulationSize, useDefaultYml, ymlList):
        theGarden=self
        #print sList
        #This block of code came from the main Vida.py. Moved and working on 2008.11.06 to allow for calling during simulation runs at
        #not just at the start.
        if theGarden.cycleNumber<1: print "***Generating and placing seeds.***"
        ###initialize progress bar###
        if theGarden.showProgressBar or theGarden.cycleNumber<1:
            theProgressBar= progressBarClass.progressbarClass(startPopulationSize-1,"*") #why -1? because index 0. So if total=100, 0-99.
        
        if seedPlacement=="square" or seedPlacement=="hex":
            seedDistance=geometry_utils.placePointsInGrid(startPopulationSize, theGarden.theWorldSize)
            prevX=-theGarden.theWorldSize/2.0
            prevY= theGarden.theWorldSize/2.0
            if seedPlacement=="hex":
                currentRow=0
                prevX= prevX-(seedDistance/2.0)
                prevY= prevY+(seedDistance/2.0)
        
        if seedPlacement=="defined" or len(sList)>0:
            theIndex=0
        #print sList
        for i in range(startPopulationSize):
            countToGerm=0
            theSpeciesFile=""
            if debug1 and startPopulationSize==1:
                x=0
                y=0
            elif len(sList)>0:
                if seedPlacement=="fromFile":
                    x=sList[i][1]
                    y=sList[i][2]
                    countToGerm=sList[i][3]
                    #radius of canopy would be sList[i][4]. Unused, but in place to be built on    
                    if sList[i][0] in ymlList:
                        theSpeciesFile=sList[i][0]
                    else:
                        print "\nWARNING: The desired species %s was not found. \nA random species will be used.\n" % (sList[i][0])
                else:
                    if sList[i] in ymlList:
                        theSpeciesFile=sList[i]                                    
            if seedPlacement=="fromFile":
                x=sList[i][1]
                y=sList[i][2]
                countToGerm=sList[i][3]
            #radius of canopy would be sList[i][4]. Unused, but in place to be built on        
            elif seedPlacement=="random":
                x=random.randrange(-(theGarden.theWorldSize/2),(theGarden.theWorldSize/2))+random.random()
                y=random.randrange(-(theGarden.theWorldSize/2),(theGarden.theWorldSize/2))+random.random()
            elif seedPlacement=="square" or seedPlacement=="hex":
                x=prevX+seedDistance
                y=prevY-seedDistance
                if x+seedDistance>=(theGarden.theWorldSize/2.0):
                    prevX=-theGarden.theWorldSize/2.0
                    if seedPlacement=="hex":
                        if currentRow==0:
                            currentRow=1
                        else:
                            currentRow=0
                            prevX= prevX-(seedDistance/2.0)    
                    prevY= prevY-seedDistance
                else:
                    prevX=x
            
            #print theSpeciesFile
            if useDefaultYml==False or theSpeciesFile=="":
                if theSpeciesFile=="" or theSpeciesFile=="_random_":
                    whichSpecies=random.randint(0,len(ymlList)-1)##pick from the species randomly
                    fileLoc= "Species/"+ymlList[whichSpecies]
                    theSpeciesFile=ymlList[whichSpecies]
                #print theSpeciesFile
                if theGarden.platonicSeeds.has_key(theSpeciesFile):
                    platonicSeed=theGarden.platonicSeeds[theSpeciesFile]
                    theSeed=copy.deepcopy(platonicSeed)
            #else:
            #print "something is very wrong"
            else:
                #if there are no species listed, use the default species.
                theSeed=Species1()                
            theSeed=theGarden.plantSeed(theSeed)
            #print theSeed.subregion                
            #now set some attributes
            theSeed.timeCreation=time.time()
            theSeed.countToGerm=countToGerm
            theSeed.x=x
            theSeed.y=y
            #this is just to get the properties calculated.Give the seed the max seed mass
            #bootstrap the seed
            theSeed.massSeed=theSeed.massSeedMax
            #convert mass to volume and the get the radius
            j= theSeed.massSeed/theSeed.densitySeed #this is volume in m^3
            j=j/(4.0/3.0)
            j=j/(math.pi)
            j=math.pow(j, 1.0/3.0)
            theSeed.radiusSeed=j
            theSeed.z= theSeed.radiusSeed
            theSeed.r= theSeed.radiusSeed            
            #theSeed.growSeedOnPlant(theSeed.massSeedMax)
            #print "#######"
            #print theSeed.__class__().name
            #print "#######"
            #update the progress meter
            if theGarden.showProgressBar or theGarden.cycleNumber<1:
                theProgressBar.update(i)


