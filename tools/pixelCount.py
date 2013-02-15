from PIL import Image
import os.path
import sys

theRGB=(131,163,189)#this colour code represents the blue sky

def main(theFolder):
	thePath=theFolder+"/Graphics/bottom-up/"
	fileList=os.listdir(thePath) 
	print "***Checking for image files...***"
	for file in fileList:
	    theExtension=os.path.splitext(file)[1]
	    theNumber=os.path.splitext(file)[0]
	    theNumber=theNumber.split('-')[-1]
	    if theExtension==".png":
	    	if theNumber[-1]=="0": 
	    		#count only files whose cucle number ends in 0
				theImg=Image.open(thePath+file).getdata()

				theCount=0
				for i in list(theImg):
					if i==theRGB:
						theCount=theCount+1

				#print "%s %s" % (theNumber, theCount)
				print "%s" % (theCount)

if __name__ == '__main__':
	theArguments=sys.argv
	if "-f" in theArguments:
		loc= theArguments.index("-f")
		theFolder=theArguments[loc+1]
		main(theFolder)
	else:
		print "     Requires a -f option followed by a path to a Vida output folder"
		print "     Example: python pixelCount.py -f /path/to/data/Output-Example"
