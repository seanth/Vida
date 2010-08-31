"""This file is part of Vida.
--------------------------
Copyright 2009, Sean T. Hammond

Vida is experimental in nature and is made available as a research courtesy "AS IS," but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 

You should have received a copy of academic software agreement along with Vida. If not, see <http://iorek.ice-nine.org/seant/Vida/license.txt>.
"""

import sys
import os
import shutil
import csv
import glob
import linecache
import pickle
###append the path to basic data files
sys.path.append("Vida_Data")
import vgraphics as outputGraphics
import vplantr as defaultSpecies

###import default settings
import vdefaults as thePrefs
produceGraphics=thePrefs.produceGraphics
produceVideo=thePrefs.produceVideo
percentTimeStamp=thePrefs.percentTimeStamp
framesPerSecond=thePrefs.framesPerSecond
produceSummary=0

class Species1(defaultSpecies.genericPlant):
	###The routine in defaultSpecies.genericPlant reads in default values from .yml file
	def __init__(self):
		##super(type, obj) -> bound super object; requires isinstance(obj, type)
		super(Species1, self).__init__()

def makeDirectory(theDirectory):
	if not os.path.exists(theDirectory):
		os.mkdir(theDirectory)

def saveDataToCSVFile (theDirectory, theFileName, theData):
	makeDirectory(theDirectory)
	if not theFileName.endswith(".csv"):
		theFileName=theFileName+".csv"
	saveDataFile =csv.writer(file(theDirectory + theFileName, 'w'),delimiter=',',lineterminator='\n')
	for l in theData:
		saveDataFile.writerow(l)

if __name__ == '__main__':
	######Read in any run time arguments provided
	theArguments=sys.argv

	if "-n" in theArguments:
		loc= theArguments.index("-n")
		fileOrFolder=theArguments[loc+1]
		fileOrFolder=fileOrFolder.split(",")
		#print fileOrFolder

	########################
	if "-g" in theArguments:
		produceGraphics=1
		theView=13
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
	if "-v" in theArguments:
		produceVideo=1
		allFiles=0
	if "-va" in theArguments:
		produceVideo=1
		allFiles=1
	###########################
	if "-fs" in theArguments:
		produceSummary=1
		allFiles=0
	if "-fsa" in theArguments:
		produceSummary=1
		allFiles=1
	
	#need to parse the -n to see if it's a file or folder
	theLastChar= fileOrFolder[0][len(fileOrFolder[0])-1]
	theOutputFolder=os.path.dirname(fileOrFolder[0])+"/"
	#print theOutputFolder
	if theLastChar=="/":
		theOutputFolder=os.path.abspath(fileOrFolder[0])+"/"
		fileOrFolder=os.listdir(theOutputFolder)
		fileOrFolder=[i for i in fileOrFolder if not i.startswith('.')]	
	#print theOutputFolder
	if len(fileOrFolder)>0:
		fileName=fileOrFolder[0].split("/")[-1]
		#what is the file suffux?
		#fileSuffix=fileOrFolder[0].split("/")[-1]
		#fileSuffix=fileSuffix.split(".")[-1]
		fileSuffix=fileName.split(".")[-1]
		#print fileSuffix
		#try and get a simulation name
		#simulationName= fileOrFolder[0]
		#simulationName= simulationName.split("/")
		#simulationName=simulationName[-1]
		#simulationName= simulationName.split("-")[0]
		simulationName=fileName.split("-")[0]

	if produceGraphics==1:
		print "#asked to produce graphics"
		if fileSuffix=="pickle":
			###make the necessary directories, if needed
			outputGraphicsDirectory = theOutputFolder+"../Graphics/"
			makeDirectory(outputGraphicsDirectory)
			if theView==1:
				outputGraphicsDirectory = outputGraphicsDirectory +"bottom-up/"
			elif theView==2:
				outputGraphicsDirectory = outputGraphicsDirectory +"top-down/"
			elif theView==3:
				outputGraphicsDirectory = outputGraphicsDirectory +"side/"
			elif theView==12:
				outputGraphicsDirectory = outputGraphicsDirectory +"combined-bottom-top/"
			elif theView==21:
				outputGraphicsDirectory = outputGraphicsDirectory +"combined-top-bottom/"
			elif theView==13:
				outputGraphicsDirectory = outputGraphicsDirectory +"combined-bottom-side/"
			elif theView==23:
				outputGraphicsDirectory = outputGraphicsDirectory +"combined-top-side/"
			elif theView==123:
				outputGraphicsDirectory = outputGraphicsDirectory +"combined-bottom-top-side/"
			makeDirectory(outputGraphicsDirectory)
			CFDGtext=""
						
			###this is a saved simulation state
			print "***Loading Simulation Data and making CFDG...***"
			for aFile in fileOrFolder:
				###load in the pickle
				simulationFile=open(aFile, 'r')
				theGarden=pickle.load(simulationFile)
				simulationFile.close()
				###set variables from garden data
				simulationName=theGarden.name
				cycleNumber=theGarden.cycleNumber
				###make the cfdg
				if CFDGtext=="":
					CFDGtext=outputGraphics.initCFDGText(theGarden, theView, percentTimeStamp, 50.0)
				theData=outputGraphics.makeCFDG(theView, CFDGtext, theGarden, cycleNumber)
				cfdgFileName= simulationName+"-"+str(cycleNumber)
				outputGraphics.writeCFDG(outputGraphicsDirectory, cfdgFileName, theData)
		simulationData=""
		theGarden=""
		CFDGText=""
		theData=""
		cfdgFileName=""
		###make the png
		#print "Producing PNG files..."
		#print outputGraphicsDirectory
		#print "###"
		#outputGraphics.outputPNGs(outputGraphicsDirectory, outputGraphicsDirectory)
		if fileSuffix =="cfdg":
			print "###Producing PNG files...###"
			outputGraphics.outputPNGs(fileOrFolder, outputGraphicsDirectory)

	if produceVideo==1:
		if fileSuffix =="png":
			if allFiles==0:
				theTempFolder=theOutputFolder+"_temp/"
				if not os.path.exists(theTempFolder):
					os.mkdir(theTempFolder)
				for aFile in fileOrFolder:
					shutil.copy(aFile, theTempFolder)
				outputGraphicsDirectory = theTempFolder
				produceGraphics=1
			else:
				outputGraphicsDirectory= theOutputFolder
				produceGraphics=1
		
	###only try and make a video if it is wanted and if pngs were made
	if produceVideo and produceGraphics==1:
		print "Producing MOV file..." 
		#print outputGraphicsDirectory
		outputGraphics.outputMOV(outputGraphicsDirectory, simulationName)
		if allFiles==0:
			###delete the temp folder and files
			shutil.rmtree(outputGraphicsDirectory)	

	if produceSummary==1 and len(fileOrFolder)>0:
		#print "yes"
		theSummaryOutput=[]
		statDictList=[]
		theSummaryOutputHeader=""
		for theFile in fileOrFolder:
			theFileName=os.path.basename(theFile)
			theOutput=[[],[]]
			if not os.path.exists(theFile):
				theFile=theOutputFolder+theFile
			if os.path.isfile(theFile):
				#what's the sequence # of the file?
				theSimName=theFileName.split("-")[0]
				theSequenceNumb=theFileName.split("-")[-1]
				theSequenceNumb=int(theSequenceNumb.split(".csv")[0])
				theOutput[0].append("Cycle #")
				theOutput[1].append(theSequenceNumb)
				
				fileObject=open(theFile)
				try:
					allText=fileObject.readlines()
				finally:
					fileObject.close()
					
				###get rid of the "\n" from end lines
				tempList=[aLine.rstrip("\n") for aLine in allText]
				allText=tempList
				###get rid of any weird trailing of leading spaces
				tempList=[aLine.strip() for aLine in allText]
				allText=tempList
				###turn the read file into a 1 list/line (2d array)
				tempList=[aLine.split(",") for aLine in allText]
				allText=tempList
				#print "#######"
				#print allText

				
				
				#this makes sure the files are in the correct format
				#if not, updates them
				#allows for backward compatability
				if not tempList[0][0]=="Cycle #":
					for line in tempList:
						#print line
						line=line.insert(0, str(theSequenceNumb))
					tempList[0][0]="Cycle #"
					saveDataToCSVFile(theOutputFolder, theFileName, tempList)
				tempList=[]

					



				##get average, max and min of data that are numbers
				##In general, most of the things that are numbers should be used
				##some should be ignored
				theIndex=0
				while theIndex<len(allText[0]):
					theColumn=[row[theIndex] for row in allText]
					ignoreTheseColumns=["Cycle #", " X Location", " Y Location"]
					totalCommunitySums=["Mass of Stem", "Mass of Canopy", "Mass Stem+Mass Canopy", "Mass of all Seeds", "Mass Total", "Growth Stem (kg)", "Growth Canopy (kg)", "Growth Stem+Canopy (kg)"]
					if not theColumn[0] in ignoreTheseColumns:
						try:
							#print theColumn[0]
							if theColumn[0]=="X Location":
								theIndex=theIndex
							else:
								float(theColumn[1])
						except:
							#do nothing
							#print "it's string"
							theIndex=theIndex
						else:
							theColumnTitle=theColumn.pop(0).strip()
							theColumn=[float(theRow) for theRow in theColumn]
							theColumnMin=min(theColumn)
							theColumnMax=max(theColumn)
							theColumnSum=sum(theColumn)
							theColumnAvg=theColumnSum/float(len(theColumn))
							theOutput[0].extend(["min "+theColumnTitle, "max "+theColumnTitle, "ave "+theColumnTitle])
							theOutput[1].extend([theColumnMin, theColumnMax, theColumnAvg])
							if theColumnTitle in totalCommunitySums:
								theOutput[0].append("sum community "+theColumnTitle)
								theOutput[1].append(theColumnSum)
					theIndex=theIndex+1
					
				#How many seeds on the ground?
				try:
					theIndex=allText[0].index(" is a seed")
				except:
					theIndex="na"
				if not theIndex=="na":
					theColumn=[row[theIndex] for row in allText]
					theColumn.pop(0)
					theCount=0
					for i in range(len(theColumn)):
						theValue=theColumn[i]
						if theValue=="True":
							theCount=theCount+1
					theOutput[0].append("# of seeds in soil")
					theOutput[1].append(theCount)
				
				#print allText[0]
				#how many alive?
				try:
					theIndex=allText[0].index(" Cause of Death")
				except:
					theIndex="na"
				if not theIndex=="na":
					theColumn=[row[theIndex] for row in allText]
					thePopulationAlive=theColumn.count("na")
					thePopulationDead=len(theColumn)-1-thePopulationAlive
					theOutput[0].extend(["# Alive", "# Dead"])
					theOutput[1].extend([thePopulationAlive, thePopulationDead])
					#print theColumn
					theDeathNames=[]
					theDeathCount=[]
					for i in range(len(theColumn)):
						theName=theColumn[i]
						if not theName in theDeathNames:
							theDeathNames.append(theName)
							theDeathCount.append(theColumn.count(theColumn[i]))
					deathHeaders=["failed to germinate(immaturity)", "failed to germinate(other)", "random death", "crushed", "overlap violation", "stem off world", "lack of light", "growth too slow", "violated Euler-Greenhill"]
					for i in deathHeaders:
						theOutput[0].append("#%s" % (i))
						theValue=0
						if i in theDeathNames:
							theIndex=theDeathNames.index(i)
							theValue=theDeathCount[theIndex]
						theOutput[1].append(theValue)
							
				#How many Species
				try:
					theIndex=allText[0].index(" Species")
				except:
					theIndex="na"
				if not theIndex=="na":
					theColumn=[row[theIndex] for row in allText]
					theColumn.pop(0)
					theSpeciesNames=[]
					theSpeciesCount=[]
					for i in range(len(theColumn)):
						theName=theColumn[i]
						if not theName in theSpeciesNames:
							theSpeciesNames.append(theName)
							theSpeciesNames.sort()
							#theSpeciesCount.append(theColumn.count(theColumn[i]))
					theSpeciesNumb=len(theSpeciesNames)
					theOutput[0].append("# of species")
					theOutput[1].append(theSpeciesNumb)
					for name in theSpeciesNames:
						theOutput[0].append(name)
						theOutput[1].append(theColumn.count(name))

				###make sure the header for the summary file is the one having the most data
				if len(theSummaryOutputHeader)<len(theOutput[0]):
					theSummaryOutputHeader=theOutput[0]
					
				####this starts building a series of dictionaries for building an output file###
				statDict=dict(zip(theOutput[0], theOutput[1]))
				statDictList.append(statDict)
				####Write the individual file
				theStatsFolder=theOutputFolder+"statistics/"
				saveDataToCSVFile(theStatsFolder, "stat_"+theFileName, theOutput)

		###this code making the summary file is not so good. there are probably better solutions
		for statDict in statDictList:
			aLine=[]
			for key in theSummaryOutputHeader:
				theValue=statDict.get(key,0)
				aLine.append(theValue)
			theSummaryOutput.append(aLine)
			
		###this sorting is so the cycle numbers are in order
		###The real solution would be to list the files in the selection dialog in order
		theSummaryOutput=sorted(theSummaryOutput)
		theSummaryOutput.insert(0, theSummaryOutputHeader)

		###save the data to a summary file
		theStatsFolder=theOutputFolder+"statistics/"
		saveDataToCSVFile(theStatsFolder, "summary_"+theSimName, theSummaryOutput)



		
		###Go through and turn the individual .csv files into one big one
		###Add cycle number if you need to. Assumes cycle # is the word between '-' and '.csv'
		#this is the simple way to cat the files. It assumes no changes need to be made.
		#Just concatenate them.
		concatFileName="merged_"+theSimName
		theOutput=open(theStatsFolder+concatFileName+".csv",'w')
		print "***Merging files...."
		fileList=glob.glob(theOutputFolder+"*.csv")
		theHeader=""
		for aFile in fileList:
			if theHeader=="":
				theHeader=linecache.getline(aFile,1)
				#print "this is the header: %s" % (theHeader)
			theFile=open(aFile)
			try:
				fileData=theFile.read()
				theOutput.write(fileData)
			finally:
				theFile.close()
		theOutput.close()
		print "***Finished merging. Removing extra headers..."
		import fileinput
		#print theStatsFolder+concatFileName+".csv"
		theFile=fileinput.input(theStatsFolder+concatFileName+".csv", inplace=1)
		i=0
		for line in theFile:
			if not line==theHeader or i==0:
				line=line.strip('\n')
				print line
			i=i+1
		print "***Finished***"
