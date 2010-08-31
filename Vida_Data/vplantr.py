"""This file is part of Vida.
--------------------------
Copyright 2009, Sean T. Hammond

Vida is experimental in nature and is made available as a research courtesy "AS IS," but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 

You should have received a copy of academic software agreement along with Vida. If not, see <http://iorek.ice-nine.org/seant/Vida/license.txt>.
"""

import sys
import math
import time
import copy
import random
###append the path to basic data files
sys.path.append("Vida_Data")
import geometry_utils
import yaml

debug=0

#class genericPlant(object):
class genericPlant(object):
	###define the props on this object
	def __init__(self):
		### if the object lacks a certain property, it has not imported the basic prefs
		if not hasattr(self, "massSeedMax"):
			fileLoc="Vida_Data/Default_species.yml"
			self.importPrefs(fileLoc)
		self.zeroSeedValues()


	def zeroSeedValues(self):
		###these values are set during the simulation
		self.name=""
		self.isSeed=True
		self.isMature=False
		self.timeCreation=0
		self.timeGermination=0
		self.timePlanted=0
		self.subregion=[]
		self.massStem=0.0 #kg
		self.massLeaf=0.0 #kg
		self.massSeed=0.0 #kg
		self.massTotal=0.0 #kg
		
		self.massFixed=-0.0 #kg
		self.massFixedRecord=[]#list of kg
		
		self.massSeedsTotal=0.0 #kg
		self.heightStem=0.0
		self.radiusStem=0.0 #meters
		self.radiusLeaf=0.0 #meters
		self.radiusSeed=0.0 #radius in meters
		self.areaPhotosynthesis=0.0#meters^2
		self.areaCovered=0.0#meters^2
		self.fractionAreaCovered=0.0
		self.seedList=[]
		self.motherPlant=0
		self.countToGerm=0.0
		###experimental. allows a plant to change how it does photosythesis based on how shaded it is
		self.photoConstantShade=self.photoConstant#
		############################
		
		self.prevHeightGrowthRate=0.0
		self.heightGrowthRate=[]
		self.avgHeightGrowthRate=0.0
		self.maxAvgHeightGrowthRate=0.0

		self.GHs=0.0 #change in Height. In meters.
		self.GRs=0.0 #change in radius of stem. In meters.
		self.GMs=0.0 #change in mass of stem. In kg.
		self.GMl=0.0 #change in mass of leaves. In kg.
		
		self.causeOfDeath=""
		###World data
		self.x=0.0
		self.y=0.0
		self.z=0.0
		self.r=0.00		
		self.age=0.0
		self.overlapList=[]
		self.colourLeaf[2]=1.0
		#fileLoc="Vida_Data/Default_species.yml"
		#self.importPrefs(fileLoc)

	def importPrefs(self, fileLoc):
		theFile=open(fileLoc)
		theData=yaml.load(theFile)
		theFile.close
		for key in theData:
		     setattr(self, key, theData[key])
		
	def dieNow(self, thePlant, theGarden):
		#die!
		#print len(thePlant.seedList)
		#print "hmmm"
		if len(thePlant.seedList)>0:
			for theSeed in thePlant.seedList:
				###The plant has seeds. Drop them prior to killing plant###
				###just drop the seed straight down###
				#print "********seed %s be being placed at %f, %f" % (theSeed.name, newX, newY)
				theSeed.countToGerm=self.delayInGermination
				theGarden.plantSeed(theSeed)
				thePlant.seedList.remove(theSeed)
		thePlant.seedList=[]
		theGarden.soil.remove(self)
		if self.isSeed:
			theGarden.numbSeeds= theGarden.numbSeeds-1
		else:
			theGarden.numbPlants=theGarden.numbPlants-1


	def growPlant(self, theGarden):
		##if you have attached seeds, allow them to grow
		tempList=copy.copy(self.seedList)
		if self.makeSeeds:
			numbSeeds=float(len(tempList))
			self.massSeedsTotal=0
			if numbSeeds>0.0:
				maxCarbonToSeed=(self.massFixed*self.fractionCarbonToSeeds)
				maxCarbonToSeed=maxCarbonToSeed/numbSeeds
				for attachedSeed in tempList:
					if self.massFixed<=0.0:
						break
					###I don't like this much
					#it gives a base amount of mass to the seed
					#+/- a random amount
					sign=random.random()
					theVarient=(random.random()*(maxCarbonToSeed-0)+0)
					if sign>0.5:
						###Don't give the seed more than you have
						carbonToSeed = maxCarbonToSeed +theVarient
						if carbonToSeed>self.massFixed:
							carbonToSeed=self.massFixed
					else:
						carbonToSeed = maxCarbonToSeed -theVarient
					attachedSeed.growSeedOnPlant(carbonToSeed)
					###if the seed is the max size, disperse it
					if attachedSeed.massSeed>=attachedSeed.massSeedMax:
						attachedSeed.disperseSeed(attachedSeed, self, theGarden)
					else:
						self.massSeedsTotal=self.massSeedsTotal+attachedSeed.massSeed
						#print "plant %f" % (self.massSeedsTotal)
			
			##if you lack seeds, make them
			#if (self.heightStem>=self.startMakingSeedsHeight) or (self.age>=self.startMakingSeedsAge) or self.isMature:
			if self.isMature:
				self.makeSomeSeeds(theGarden.maxSeedsPerPlant)

		self.calcMassStemFromMassNew()
		
		self.calcRadiusStemFromMassStem()
		
		self.calcHeightStemFromRadiusStem(theGarden)
		
		self.calcMassLeafFromMassStem()
		
		self.massTotal=self.massLeaf+self.massStem+self.massSeedsTotal

		###convert mass to get radius of leaf
		self.calcRadiusLeafFromMassLeaf()
		
		self.z=self.heightStem+self.heightLeafMax
		
		if self.radiusLeaf>=self.radiusStem:
			self.r=self.radiusLeaf
		else:
			self.r=self.radiusStem
		#save the changes in height over time
		self.heightGrowthRate.append(self.heightStem-self.prevHeightGrowthRate)
		self.prevHeightGrowthRate=self.heightStem
		while len(self.heightGrowthRate)>self.numYearsGrowthMemory:
			self.heightGrowthRate.pop(0)
		self.avgHeightGrowthRate=sum(self.heightGrowthRate)/float(len(self.heightGrowthRate))
		if self.avgHeightGrowthRate>self.maxAvgHeightGrowthRate:
			self.maxAvgHeightGrowthRate=self.avgHeightGrowthRate
		self.age=self.age+1


	def makeSeed(self, theSeed):
		theSeed=copy.deepcopy(self)
		theSeed.zeroSeedValues()
		theNameList= theSeed.name.split()
		if len(theNameList)<2:
			idNumb=str(random.random())
		else:
			idNumb=theNameList[1]
		theMax=self.locSeedFormation[0]
		theMin=self.locSeedFormation[1]
		###Check these values and fix them if they have weird values
		if theMax>1.0: self.locSeedFormation[0]=1.0
		if theMax<0.0: self.locSeedFormation[0]=0.0
		if theMin>1.0: self.locSeedFormation[1]=1.0
		if theMin<0.0: self.locSeedFormation[1]=0.0
		###
		theRadius=self.radiusLeaf
		r=theRadius*theMax
		delta=theRadius*theMin
		r=(random.random()*(r-delta))+ delta
		twoPi=3.14*2
		theAngle=(random.random()*(twoPi-0)+0)
		seedX=r*math.cos(theAngle)
		seedY=r*math.sin(theAngle)
		theSeed.x= seedX +self.x
		theSeed.y= seedY +self.y
		if self.leafIsHemisphere:
			dist=geometry_utils.distBetweenPoints(seedX+self.x, seedY+self.y, self.x, self.y)
			if dist==self.radiusLeaf:
				deltaY=self.radiusLeaf
			elif dist==0.0:
				deltaY=0.0
			else:
				#deltaY=self.radiusLeaf-math.sqrt(abs((self.radiusLeaf*self.radiusLeaf)-(dist*dist)))
				deltaY=self.radiusLeaf-((abs((self.radiusLeaf*self.radiusLeaf)-(dist*dist)))**0.5)
			seedZ=self.heightStem+(self.heightLeafMax/2.0)-deltaY
		else:
			seedZ=self.heightStem+(self.heightLeafMax/2.0)

		theSeed.name="growingSeed %s" % (idNumb)
		theSeed.timeCreation=time.time()
		theSeed.motherPlant=self
		theSeed.x= seedX +self.x
		theSeed.y= seedY +self.y
		theSeed.z= seedZ
		theSeed.r= theSeed.radiusSeed
		self.seedList.append(theSeed)

	def growSeedOnPlant(self, maxCarbonForSeed):
		if maxCarbonForSeed > self.motherPlant.massSeedMax:
			maxCarbonForSeed =self.motherPlant.massSeedMax
		if not self.motherPlant.massFixed==-0.0:
			if maxCarbonForSeed>self.motherPlant.massFixed:
				maxCarbonForSeed=self.motherPlant.massFixed
		self.motherPlant.massFixed=self.motherPlant.massFixed-maxCarbonForSeed
		self.massSeed= self. massSeed + maxCarbonForSeed
		#use that value to calculate the radius of the seed
		#convert mass to volume and the get the radius
		i= self.massSeed/self.densitySeed #this is volume in m^3
		#i=i/(4.0/3.0)
		i=i/1.3333
		#i=i/(math.pi)
		i=i/3.14
		#i=math.pow(i, 1.0/3.0)
		#i=math.pow(i, 0.3333)
		i=i**0.3333
		self.radiusSeed=i

		###need to move the seed as the plant grows###
		if self.motherPlant.leafIsHemisphere:
			dist=geometry_utils.distBetweenPoints(self.x, self.y, self.motherPlant.x, self.motherPlant.y)
			if dist==self.motherPlant.radiusLeaf:
				deltaY=self.motherPlant.radiusLeaf
			elif dist==0.0:
				deltaY=0.0
			else:
				deltaY=self.motherPlant.radiusLeaf-((abs((self.motherPlant.radiusLeaf*self.motherPlant.radiusLeaf)-(dist*dist)))**0.5)
			seedZ=self.motherPlant.heightStem+(self.motherPlant.heightLeafMax/2.0)-deltaY
		else:
			seedZ=self.motherPlant.heightStem+(self.motherPlant.heightLeafMax/2.0)
		self.z= seedZ
		self.r= self.radiusSeed

	def disperseSeed(self, theSeed, motherPlant, theGarden):
		###this dispersal method needs to be better
		if motherPlant.seedDispersalMethod[0]==0:
			###This is just random anywhere in world###
			newX =random.randrange(-(theGarden.theWorldSize/2),(theGarden.theWorldSize/2))+random.random()
			newY =random.randrange(-(theGarden.theWorldSize/2),(theGarden.theWorldSize/2))+random.random()
		elif motherPlant.seedDispersalMethod[0]==1:
			###just drop the seed straight down###
			newX=theSeed.x
			newY=theSeed.y
		elif motherPlant.seedDispersalMethod[0]==2:
			###drop the seed in a circle with a defined max radius###
			theRadius=motherPlant.seedDispersalMethod[1]
			theMax=1
			theMin=0
			r=theRadius*theMax
			delta=theRadius*theMin
			r=(random.random()*(r-delta))+ delta
			#twoPi=math.pi*2
			twoPi=3.14*2
			theAngle=(random.random()*(twoPi-0)+0)
			newX =r*math.cos(theAngle)
			newY =r*math.sin(theAngle)
			newX = newX + theSeed.x
			newY = newY + theSeed.y
		elif motherPlant.seedDispersalMethod[0]==3:
			###eject the seed straight out from leaf, traveling a defined max distance###
			maxDistance=motherPlant.seedDispersalMethod[1]
			theMax=1
			theMin=0
			theDistance= maxDistance*theMax
			delta= maxDistance*theMin
			theDistance =(random.random()*(theDistance-delta))+ delta
			theHypot=geometry_utils.distBetweenPoints(motherPlant.x, motherPlant.y, theSeed.x, theSeed.y)
			theRise=theSeed.y-motherPlant.y
			theRun=theSeed.x-motherPlant.x
			theAngle=math.asin(theRise/theHypot)
			#theAngle=math.degrees(theAngle)
			newX=math.cos(theAngle)*theDistance
			if theRun<0.0:
				newX=0.0-newX
			newY=math.sin(theAngle)*theDistance
			newX=newX+theSeed.x
			newY=newY+theSeed.y
		elif motherPlant.seedDispersalMethod[0]==4:
			###get a random angle based on input###
			angle=motherPlant.seedDispersalMethod[1]
			theVariance=(random.random()*((angle*0.5)-0.0))+ 0.0
			if random.random()>0.5:
				theVariance=0-theVariance
			angle=angle+theVariance
			angle=math.radians(angle)

			###get a random velocity based on input###
			####it would be nicer to use a force so seed size influences things too
			v=motherPlant.seedDispersalMethod[2]
			theVariance=(random.random()*((v*0.5)-0.0))+ 0.0
			if random.random()>0.5:
				theVariance=0-theVariance
			v=v+theVariance

			g=theGarden.gravity
			h=motherPlant.heightStem+motherPlant.heightLeafMax

			tempVar1= (v*math.cos(angle))/g
			tempVar2= (v*math.sin(angle))
			#tempVar3= math.sqrt((tempVar2*tempVar2)+(2*g*h))
			tempVar3= ((tempVar2*tempVar2)+(2*g*h))**0.5
			tempVar3= tempVar2+tempVar3
			theDistance=tempVar1*tempVar3
			theHypot=geometry_utils.distBetweenPoints(motherPlant.x, motherPlant.y, theSeed.x, theSeed.y)
			theRise=theSeed.y-motherPlant.y
			theRun=theSeed.x-motherPlant.x
			theAngle=math.asin(theRise/theHypot)
			newX=math.cos(theAngle)*theDistance
			if theRun<0.0:
				newX=0.0-newX
			newY=math.sin(theAngle)*theDistance
			newX=newX+theSeed.x
			newY=newY+theSeed.y

			
		#print "********seed %s be being placed at %f, %f" % (theSeed.name, newX, newY)
		theSeed.x=newX
		theSeed.y=newY
		theSeed.countToGerm=self.delayInGermination
		theGarden.plantSeed(theSeed)
		motherPlant.seedList.remove(theSeed)

	def germinate(self, theGarden):
		if self.countToGerm<1:
			###death due to failure to germinate
			tooBad=random.random()
			if theGarden.cycleNumber==0 and theGarden.ignoreGermDeathAtStart:
				tooBad=1.0
			if tooBad<self.fractionFailGerminate:
				self.causeOfDeath="failed to germinate(random death)"
				theGarden.kill(self)
			else:
				massForGrowth=self.massSeed*self.fractionSeedMassToPlant
				if massForGrowth <=self.massSeedMax*self.fractMassSeedMaxToGerm*self.fractionSeedMassToPlant or massForGrowth <=0.0:
					self.causeOfDeath="failed to germinate(immaturity)"
					theGarden.kill(self)
				else:
					self.isSeed=False
					self.age=1
					self.timeGermination=time.time()
					theNameList=self.name.split()
					if len(theNameList)<2:
						idNumb=str(random.random())
					else:
						idNumb=theNameList[1]
					self.name="Plant %s" % (idNumb)
					###update the garden
					theGarden.numbSeeds= theGarden.numbSeeds-1
					theGarden.numbPlants= theGarden.numbPlants+1

					###For germination only, mass to
					###stem and leaf is a straight fraction.
					self.massStem= massForGrowth*self.fractionCarbonToStem
					self.massLeaf= massForGrowth-self.massStem

					###convert massStem to radiusStem and heightStem
					self.calcRadiusStemFromMassStem()
					self.calcHeightStemFromRadiusStem(theGarden)
	
					###what's the radius of the leaf and area?
					self.calcRadiusLeafFromMassLeaf()

					###need a special routine where a single plant is checked against the garden
					###to determine its shadedness.
					###will be in world_basics

					###rename the seed so you know it's a plant
					self.z=self.heightStem+self.heightLeafMax
					###why am I doing this, again?
					if self.radiusLeaf>=self.radiusStem:
						self.r=self.radiusLeaf
					else:
						self.r=self.radiusStem
		else:
			self.countToGerm=self.countToGerm-1

	def calcNewMassFromLeaf(self, theGarden):
		#print "mass stem: %s" % (self.massStem)
		#print "mass leaf: %s" % (self.massLeaf)
		areaAvailable=self.areaPhotosynthesis-self.areaCovered
		#print "Ap: %s" % (areaAvailable)
		if self.areaPhotosynthesis>0.0:
			fractionAvailable=areaAvailable/self.areaPhotosynthesis
		else:
			fractionAvailable=0.0
		if fractionAvailable>self.fractionMinimumSurvival:
			#lightConversion=self.photoConstant*(self.massLeaf**self.photoExponent)#in units of kgGrowth/area leaf for photosynthesis
			#newMass= (areaAvailable*lightConversion)
			var1=(self.massLeaf**self.photoExponent)#in units of kgGrowth/area leaf
			var1=areaAvailable*var1#in units of kgGrowth/area leaf
			var2=(self.photoConstant*fractionAvailable)+(self.photoConstantShade*(1-fractionAvailable))
			#print "%s: %s" % (self, var2)
			newMass=var2*var1
			###decide whether canopy transmission impacts conversion
			alterMassWitTransmission=0
			if theGarden.canopyTransmittanceImpactsConversion==1:
				alterMassWitTransmission=1
			elif theGarden.canopyTransmittanceImpactsConversion==0:
				alterMassWitTransmission=0
			else:
				if self.canopyTransmittanceImpactsConversion:
					alterMassWitTransmission=1
				else: 
					alterMassWitTransmission=0
			if alterMassWitTransmission==1:
				newMass=newMass*(1-self.canopyTransmittance)
			#print "mass new: %s" % (newMass)
			return newMass
		else:
			return -1.0

	def calcMassStemFromMassNew(self):
		massNew=self.massFixed
		#GMs=self.speciesConstant1*math.pow(massNew, self.speciesExponent1)
		GMs=self.speciesConstant1*(massNew**self.speciesExponent1)
		massStem=self.massStem+GMs
		self.GMs=GMs
		self.massStem=massStem
		
	def calcMassLeafFromMassStem(self):
		massLeaf=self.massLeaf
		massNew=self.massFixed
		massStem=self.massStem
		massTotal=self.massTotal+massNew
		if (self.age>=self.startMakingSeedsAge) or self.isMature:
			#massLeaf=self.speciesConstant3*(math.pow(massStem, self.speciesExponent3))
			massLeaf=self.speciesConstant3*(massStem**self.speciesExponent3)
			#print "mature at: %i" % (self.age)
		else:
			#massLeaf=self.speciesConstant2*(math.pow(massStem, self.speciesExponent2))
			massLeaf=self.speciesConstant2*(massStem**self.speciesExponent2)
			#print "young"
		#if not massStem+massLeaf==massTotal:
			###something went wonky with calcs.
			#print "Age: %i  a bit off: %f" % (self.age, massTotal-massStem-massLeaf)
			#massLeaf=massTotal-massStem
		self.GMl=massLeaf-self.massLeaf
		self.massLeaf=massLeaf

		
	def calcRadiusLeafFromMassLeaf(self):
		leafVolume=self.massLeaf/self.densityLeaf
		leafAreaDisc=leafVolume/self.heightLeafMax
		leafRadius= geometry_utils.radiusCircle(leafAreaDisc)
		if self.leafIsHemisphere:		
			leafRadius=leafRadius*0.7071067812
		self.radiusLeaf=leafRadius
		self.areaPhotosynthesis =3.14*leafRadius*leafRadius
		if debug==1:print "          calcRadiusLeafFromMassLeaf: Radius of Leaf is %f" % (self.radiusLeaf)

	def calcRadiusStemFromMassStem(self):
		Ms=self.massStem
		#Ds=self.speciesConstant20*math.pow(Ms,self.speciesExponent20)
		Ds=self.speciesConstant20*(Ms**self.speciesExponent20)
		Rs=Ds/2.0
		self.GRs=Rs-self.radiusStem
		self.radiusStem=Rs
		if debug==1:print "          calcRadiusStemFromMassStem: Radius of stem is %f" % (self.radiusStem)
		#print "          calcRadiusStemFromMassStem: Radius of stem is %f" % (self.radiusStem)
	
	def calcHeightStemFromRadiusStem(self, theGarden):
		Ds=self.radiusStem*2
		##there is a weird, very rare bug
		if (Ds==0.0):
			self.causeOfDeath="impossible diameter calculation(Ds==0.0)"
			theGarden.kill(self)
		#mature allocation method
		Hs=(self.speciesConstant8*math.log(Ds))+self.heightStemMax
		if Hs<self.heightStem:
			#young method
			#Hs=(self.speciesConstant7*math.pow(Ds, self.speciesExponent7))-self.speciesConstant6
			Hs=(self.speciesConstant7*(Ds**self.speciesExponent7))-self.speciesConstant6
		elif not self.isMature:
			self.isMature=True
			#print "mature at: %i" % (self.age)
		GHs=Hs-self.heightStem
		if (Hs<0.0 or Hs<self.heightStem):
			print "oops. stem is shrinking. that's not right. Die"
			self.GHs=GHs
			self.heightStem=Hs
			#something is wrong. There's either a negative height or it is shrinking
			self.causeOfDeath="impossible height calculation"
			theGarden.kill(self)
		else:
			self.GHs=GHs
			self.heightStem=Hs
			
											
	def makeSomeSeeds(self, maxSeedsPerPlant):
		#make a seed on yourself if you don't have the max number of seeds
		theNum=float(sum(self.massFixedRecord))
		theDenom=float(len(self.massFixedRecord))
		###this addresses a rare bug where theDenom==0.0
		if theDenom<=0:
			avgMassFixed=0
		else:
			avgMassFixed=theNum/theDenom
		###see code from 2008.10.05 for attempts at having seed mass change as plant size increases.
		maxKgSeeds=self.reproductionConstant*(self.massFixed**self.reproductionExponent)
		#maxKgSeeds=self.reproductionConstant*(self.massFixed**self.reproductionExponent)
		adjMaxKgSeeds=maxKgSeeds*self.fractionCarbonToSeeds
		#the adjMaxKgSeeds makes use of how selfish a plant is (fractionCarbonToSeeds) to either
		###use all of the possible seed carbon for seeds, or some fraction there of.
		if self.massFixed<avgMassFixed:
			###if the plant is suddenly stressed, adjust how it is making seeds
			theFractDifference=self.massFixed/avgMassFixed
			if theFractDifference<self.fractionSelfishness and self.fractionCarbonToSeeds<1.0:
				#adjMaxKgSeeds=maxKgSeeds*1.0
				adjMaxKgSeeds=float(maxKgSeeds)#just make sure it's a float
		numbSeedsOnPlant=len(self.seedList)
		makeThisManySeeds=int(adjMaxKgSeeds/self.massSeedMax)-numbSeedsOnPlant
		if makeThisManySeeds>maxSeedsPerPlant:
			makeThisManySeeds=maxSeedsPerPlant
		for i in range(makeThisManySeeds):
			self.makeSeed(self)
