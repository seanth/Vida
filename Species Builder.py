#!/usr/bin/env python
"""This file is part of Vida.
--------------------------
Copyright 2009, Sean T. Hammond

Vida is experimental in nature and is made available as a research courtesy "AS IS," but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 

You should have received a copy of academic software agreement along with Vida. If not, see <http://iorek.ice-nine.org/seant/Vida/license.txt>.
"""

import cherrypy
import webbrowser
import os
import os.path
import yaml

class HelloWorld(object):
	@cherrypy.expose
	def index(self):
		#return "Hello World!"
		return cherrypy.tools.staticdir.root

	@cherrypy.expose
	def speciesBuilder(self):
		return open('Vida_Data/GUI/speciesBuilder.html').read()

	@cherrypy.expose
	def loadSpeciesNames(self):
		theDirectory="Species/"
		###check and see if what is returned is a file of a directory
		if not os.path.isdir(theDirectory):
			selectedExtension=os.path.splitext(theDirectory)[1]
			theDirectory =os.path.dirname(theDirectory)
		rawFileList = os.listdir(theDirectory)
		###show only files with the desired suffixes
		okFileSuffix=[".yml"]
		theFileList=[] 
		for file in rawFileList:
			theExtension=os.path.splitext(file)[1]
			theFileName=os.path.splitext(file)[0]
			if theExtension in okFileSuffix:
				theFileList.append(theFileName)
		rawFileList=[]
		allOptions="<option value=' '> </option>"
		for fileName in theFileList:
			theOption="<option value='%s.yml'>%s</option>" % (fileName, fileName)
			allOptions= allOptions+theOption
		return allOptions

	@cherrypy.expose
	def submitData(*args, **kw):
		theKeys=kw.keys()
		theKeys.sort()
		theOutput=[]
		for aKey in theKeys:
			splitByPeriod= aKey.split(".")
			if splitByPeriod[1]=="nameSpecies":
				theFileName=kw[aKey]
			if splitByPeriod[1][1]=="#":
				theOutput.append("%s\n" % (splitByPeriod[1]))		
			else:
				theOutput.append("%s: %s\n" % (splitByPeriod[1], kw[aKey]))
		#theFileName=theFileName.replace(" ", "")
		theFileName=theFileName
		fileLoc="Species/"+ theFileName+".yml"
		copyNumb=0
		while os.path.isfile(fileLoc):
			###There should be something here to alert the user if they are going to overwrite an existing file
			#print "the file exists"
			copyNumb=copyNumb+1
			fileLoc="Species/"+ theFileName+str(copyNumb)+".yml"
		theFile=open(fileLoc, 'w')
		theFile.writelines(theOutput)
		theFile.close
		print "File saved"
		return "saved"
	
		
	

	@cherrypy.expose
	def loadSpeciesYMLFile(self, theFileName='Generic Gymnosperm.yml'):
		#print "loading file"
		fileLoc="Species/"+ theFileName
		theFile=open(fileLoc)
		theFileData= theFile.read().splitlines()
		theFile.close
		#print "file closed"
		#now open the file with help/tutorial data
		#print "loading file"
		fileLoc="Vida_Data/SpeciesFileHelpData.yml"
		theFile=open(fileLoc)
		theHelpData= yaml.load(theFile)
		theFile.close
		#print "file closed"
		CSSData="<center><input disabled name='saveButton' id='saveButton' type='submit' value='Save now'></center>\n<div style='width: 450px; background-color: #ccc; border: 1px solid #333; padding: 5px; margin: 0px auto;'>\n%s  <div class='spacer'>&nbsp;</div>\n</div>\n"
		sectionID="<div id='%s'><input type='hidden' name='%s' value='%s' />\n%s</div>\n"
		sectionData=""
		lineData=""
		basicLineData="<div class='row'><span class='label'>%s:</span><span class='formw'><input id='%s' type='text' name='%s' value='%s'  onChange='enableSaveButton()' /><img src='interfaceGraphics/speciesBuilder/question.gif' title='%s'></span></div>\n"
		idSectionName=""

		theFormData=""
		closeDiv="</div>\n"
		sortNumber=0
		for item in theFileData:
			if not item=="":
				if sortNumber<10:
					sortNumbStr="0"+str(sortNumber)
				else:
					sortNumbStr=str(sortNumber)
				splitByColon=item.split(": ")
				if splitByColon[0][0]=="#":
					splitByPound=item.split("#")[-1]
					if idSectionName=="":
						theFormData=theFormData+ sectionData
						sectionData=""
						idSectionName= sectionID % ("section"+splitByPound, sortNumbStr+".###"+splitByPound, "###"+splitByPound, "%s")
					else:
						###prev section has ended and a new one has started
						sectionData = idSectionName % (sectionData)
						theFormData=theFormData+ sectionData
						idSectionName= sectionID % ("section"+splitByPound, sortNumbStr+".###"+splitByPound, "###"+splitByPound, "%s")
						sectionData=""
				else:
					##this error catch is in case the help data file is missing, or partly missing
					theHelpString="No data available."
					if splitByColon[0] in theHelpData:
						theHelpString=theHelpData[splitByColon[0]]
					lineData=basicLineData % (splitByColon[0], splitByColon[0], sortNumbStr+"."+splitByColon[0], splitByColon[-1], theHelpString)
					sectionData= sectionData + lineData
				sortNumber=sortNumber+1
		if not idSectionName=="":
			sectionData = idSectionName % (sectionData)
		theFormData=theFormData+ sectionData
		theHtml=CSSData % (theFormData)
		#print theHtml
		return theHtml






	

theUrlBase="localhost"
thePort=8080
curdir = os.path.join(os.getcwd(), "Vida_Data/GUI")
conf = {
        '/interfaceGraphics': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': 'interfaceGraphics',
            'tools.staticdir.root': curdir,
        },
        '/': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': '',
            'tools.staticdir.root': curdir,
        },
}

cherrypy.tree.mount(HelloWorld(), config=conf)
#something changed in the latest cherrypy build
#cherrypy.engine.start(blocking=False)
cherrypy.engine.start()
cherrypy.server.socketPort=thePort
cherrypy.server.quickstart()
theUrl="http://%s:%s/speciesBuilder" % (theUrlBase, thePort)
webbrowser.open(theUrl)
cherrypy.engine.block()