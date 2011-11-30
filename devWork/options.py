import argparse
import ConfigParser

try:
    theConfig=ConfigParser.RawConfigParser()
    theConfig.optionxform = str 
    theConfig.read('Vida.ini')
    theConfigSection='Vida Options'
except ConfigParser.MissingSectionHeaderError:
    print("Warning: Invalid config file, no [%s] section.") % (theConfigSection)
    raise

theDefaults={}
for i in theConfig.items(theConfigSection):
    theItem=i[0]
    try:
        theValue=theConfig.getint(theConfigSection, theItem)
    except:
        try:
            theValue=theConfig.getboolean(theConfigSection, theItem)
        except:
            try:
                theValue=theConfig.getfloat(theConfigSection, theItem)
            except:
                try:
                    theValue=theConfig.get(theConfigSection, theItem)
                    if theValue=="None": theValue=None
                except:
                    print "what the...?"
    theDefaults[theItem]=theValue
print theDefaults
print "#################"
	
###the actions stuff can probably be rolled together with a few ifs
###rolled several seperate action classes into a general on with lots of ifs
class parseAction(argparse.Action):
    def __call__(self,parser,args,theValues,option_string=None):
        ###reload species option
        if self.dest=="resumeSim":
            theValues=[theValues, True]
        ###video option
        if self.dest=="produceVideo":
            if theValues==None:
                theValues=True
            else:
                try:
                    theValues=[True, int(theValues)]
                except:
                    print "\n***Warning: -v [int] must have an integer value\n   Setting frames per second to the default value"
                    theValues=[True, theDefaults['framesPerSecond']]  
        ###graphical option
        if self.dest=="produceGraphics":
            if theValues==[]:
                theValues=[True, theDefaults['graphicalView']]
            else:
                theValues=[True, theValues]
        ###seed placement option
        if self.dest=="startPopulationSize":
            theOpt=self.option_strings
            if theOpt==['-ss']: theOpt='square'
            elif theOpt==['-sh']: theOpt='hex'
            elif theOpt==['-sf']: theOpt='fromFile'
            else: theOpt='random'
            if theValues==None:
                theValues=[self.default, theOpt]
            else:
                theValues=[theValues, theOpt]
        ###archive options
        if self.dest=="archive" or self.dest=="saveData":
            #theOpt=self.option_strings
            theValues=theValues[0]
        setattr(args, self.dest, theValues)

    
if __name__ == '__main__':
    parser=argparse.ArgumentParser(description='blargity blarg blarg')
    parser.add_argument('-n', type=str, metavar='string', dest='simulationName', required=False, help='Name of the simulation')
    parser.add_argument('-w', type=int, metavar='int', dest='theWorldSize', required=False, help='Size of the world')
    parser.add_argument('-x', type=int, metavar='int', dest='timesToRepeat', required=False, help='Times to repeat simulation')
    parser.add_argument('-m', type=int, metavar='int', dest='maxPopulation', required=False, help='Maximum population before stop')
    parser.add_argument('-t', type=int, metavar='int', dest='maxCycles', required=False, help='Maximum time before stop')
    parser.add_argument('-i', type=float, metavar='float', dest='percentTimeStamp', required=False, help='Percent size of time stamp')
    parser.add_argument('-d', dest='debug', action='store_true', required=False, help='Debug level 1')
    parser.add_argument('-dd',dest='debug2',action='store_true', required=False, help='Debug level 2')
    parser.add_argument('-c', dest='deleteCfdgFiles', action='store_false', required=False, help='Keep cfdg files')
    parser.add_argument('-p', dest='deletePngFiles', action='store_true', required=False, help='Delete png files')
    parser.add_argument('-b', dest='showProgressBar', action='store_true', required=False, help='Show progress bars')    
    parser.add_argument('-r', metavar='file', type=file, dest='resumeSim', required=False, help='Load a saved simulation and continue')
    parser.add_argument('-e', metavar='file', type=file, dest='eventFile', required=False, help='Load an event file')    
    ###options that use a code action
    parser.add_argument('-rl', metavar='file', type=file, dest='resumeSim', action=parseAction, required=False, help='Load a saved simulation and continue')
    parser.add_argument('-v', type=int, metavar='int', nargs='?', action=parseAction, dest='produceVideo', required=False, help='Produce a video from images. Optional frames/second')    
    parser.add_argument('-g', nargs='*', type=str, action=parseAction, dest='produceGraphics', required=False, choices=['b','t','s','ts','st','bs','sb','bt','tb','bts','3d' ], help='Graphical view desired')    
    parser.add_argument('-s', type=int, metavar='int', nargs='?', dest='startPopulationSize', action=parseAction)
    parser.add_argument('-ss', type=int, metavar='int', nargs='?', dest='startPopulationSize', action=parseAction)
    parser.add_argument('-sh', type=int, metavar='int', nargs='?', dest='startPopulationSize', action=parseAction)
    parser.add_argument('-sf', type=file, metavar='file', nargs=1, dest='startPopulationSize', action=parseAction)
    parser.add_argument('-a', type=str, dest='archive', action=parseAction, nargs=1, choices=['a', 'e','n','s'])
    parser.add_argument('-ai', type=int, dest='archive', action=parseAction, nargs=1 )
    parser.add_argument('-f', type=str, dest='saveData', action=parseAction, nargs=1, choices=['a', 'e','n','s'])
    parser.add_argument('-fi', type=int, dest='saveData', action=parseAction, nargs=1 )

    ##########

    parser.set_defaults(**theDefaults)
    
    theOptsVals=vars(parser.parse_args())#have it presented as a dict
    theOpts=theOptsVals.keys()#this returns a list of the arguments entered

    globalVarsVals=globals()#dictionary of all local variables and their values
	
    for theVar in theOpts:
        globalVarsVals[theVar]=theOptsVals[theVar]
        
    ###parse the graphic options a bit more
    if type(produceGraphics)==list:
        graphicalView=produceGraphics[1]
        produceGraphics=produceGraphics[0]    
    if type(graphicalView)!=list:
        graphicalView=[graphicalView]#make sure the graphicalView is a list
    #now convert the letter code into the number code used
    for i in range(len(graphicalView)):
        if graphicalView[i]!='3d':
            graphicalView[i]=graphicalView[i].replace('b','1')
            graphicalView[i]=graphicalView[i].replace('t','2')
            graphicalView[i]=graphicalView[i].replace('s','3')
            graphicalView[i]=int(graphicalView[i])
        
    ###parse the video options a bit more
    if type(produceVideo)==list:
        framesPerSecond=produceVideo[1]
        produceVideo=produceVideo[0]
    if produceVideo==True:
        if produceGraphics==False:
            print "***Warning: A video output was desired, but a graphical option was not specified\n   Graphical output has been set to the default"
            produceGraphics=True
            graphicalView=[theDefaults['graphicalView']]
        if graphicalView==['3d']:
            print "***Warning: A video can not be auto generated from the '3d' graphical option\n   Video output turned off"
            produceVideo=False
    ##parse resume sim option a bit more
    if type(resumeSim)==list:
        reloadSpeciesData=resumeSim[1]
        resumeSim=resumeSim[0]
    ###parse seed placement options a bit more
    if type(startPopulationSize)==list:
        seedPlacement=startPopulationSize[1]
        startPopulationSize=startPopulationSize[0]
    ###parse achival options a bit more
    
    

    for x in theOpts:
        print "%s: \t%s   %s" % (x, theDefaults[x], globalVarsVals[x])
        
    theDefaults=None#just clear it to free up memory

print simulationName
print reloadSpeciesData
