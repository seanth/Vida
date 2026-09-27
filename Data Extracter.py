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


class HelloWorld(object):
	@cherrypy.expose
	def index(self):
		#return "Hello World!"
		return cherrypy.tools.staticdir.root

	@cherrypy.expose
	def extract(self):
		return open('Vida_Data/GUI/prototypeExtractor.html').read()

	@cherrypy.expose
	def listdir(self, directory='.'):
		print "**********" 
		print directory
		print "**********"
		###check and see if what is returned is a file of a directory
		if not os.path.isdir(directory):
			selectedExtension=os.path.splitext(directory)[1]
			directory=os.path.dirname(directory)
		rawFileList = os.listdir(directory)
		###show only files with the desired suffixes
		okFileSuffix=[".csv", ".cfdg", ".png", ".pickle"]
		theFileList=[]
		for file in rawFileList:
			theExtension=os.path.splitext(file)[1]
			if theExtension in okFileSuffix and theExtension==selectedExtension:
				theFileList.append(file)
		rawFileList=[]
		if len(theFileList)==0:
			theFileList=["No compatible file found."]
		return '\n'.join( ['<option>%s</option>' % i for i in theFileList] )

	@cherrypy.expose
	def submitCommands(self, filePath="", fileSuffix="", selectedAll=0, n="", c=0, g=0, v=0, fa=0, fs=0 ):
		if not os.path.isdir(filePath):
			theDirectory=os.path.dirname(filePath)+"/"
		if type(n)==str:
			n=theDirectory+n
		if type(n)==list:
			theIndex=0
			for aFile in n:
				n[theIndex]=theDirectory+n[theIndex]
				theIndex=theIndex+1
			n=",".join(n)	
		theArgument="-n \"%s\""
		if c==1: theArgument=theArgument+" -c "
		if g=="1": theArgument=theArgument+" -g "
		if v=="1":
			if selectedAll=="0": 
				theArgument=theArgument+" -v "
			else:
				theArgument=theArgument+" -va "
		if fa=="1": theArgument=theArgument+" -fa "
		if fs=="1": 
			if selectedAll=="0":
				theArgument=theArgument+" -fs "
			else:			
				theArgument=theArgument+" -fsa "
		print ""
		theArgument=theArgument % (n)
		print "from Extract: %s" % (theArgument)
		os.system("python Vida_Data/vextract.py %s" % (theArgument))


	

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
theUrl="http://%s:%s/extract" % (theUrlBase, thePort)
webbrowser.open(theUrl)
cherrypy.engine.block()