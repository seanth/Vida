"""This file is part of Vida.
    --------------------------
    Copyright 2023, Sean T. Hammond

    Vida is experimental in nature and is made available as a research courtesy "AS IS," but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

    You should have received a copy of academic software agreement along with Vida. If not, see <https://github.com/seanth/Vida/blob/master/LICENSE.txt>.
"""

###Reading seed placement files: csv files where each line is
###    species file, x, y, cycles to wait before germinating
###for example:
###    Generic Gymnosperm.yml, 0.0, 0.0, 0
###They are used with the -sf command line option and in "Seed" events.


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
    ###################
    ######STH 2022-1105
    ###remove trailing "\n"
    seedPlacementList = [aLine.rstrip() for aLine in seedPlacementList]
    ###remove blank lines
    seedPlacementList = [aLine for aLine in seedPlacementList if aLine!=""]
    ###break the CSV on each line into a list
    seedPlacementList = [aLine.split(",") for aLine in seedPlacementList]
    i=0
    for aLine in seedPlacementList:
        aLine = [x.strip() for x in aLine] #remove any leading or trailing white spaces
        theLength=len(aLine)
        if theLength>4: del aLine[4:theLength] #if it is too long, just chop it
        aLine = aLine+["0.0"]*(4-theLength) #if too short, make it longer
        #check item in the list and convert from string to correct type
        aLine = [correctType(x) for x in aLine]
        seedPlacementList[i]=aLine
        i=i+1
    ###keep the lines that are a species name, x, y and a whole number of
    ###cycles. (This used to delete the bad lines from the list while going
    ###through it, which skipped the line after each one it deleted.)
    goodLines=[]
    printErrorMessage=0
    for aLine in seedPlacementList:
        if type(aLine[3])==float:
            aLine[3]=int(aLine[3])
        if (type(aLine[0])!=str) or (type(aLine[1])!=float) or (type(aLine[2])!=float) or (type(aLine[3])!=int):
            printErrorMessage=1
        else:
            goodLines.append(aLine)
    seedPlacementList=goodLines
    if printErrorMessage:
        print("***Improper seeding file format...")
        print("     Questionable lines will be ignored.")
    return seedPlacementList

def readPlacementFile(fileName):
    #read a placement file and return its lines as [species, x, y, delay] lists
    theFile=open(fileName)
    try:
        theLines=theFile.readlines()
    finally:
        theFile.close()
    return checkSeedPlacementList(theLines)
