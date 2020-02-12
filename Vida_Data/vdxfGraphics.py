"""This file is part of Vida.
--------------------------
Copyright 2009, Sean T. Hammond

Vida is experimental in nature and is made available as a research courtesy "AS IS," but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 

You should have received a copy of academic software agreement along with Vida. If not, see <http://iorek.ice-nine.org/seant/Vida/license.txt>.
"""

import glob
import os
import sdxf_utils as sdxf
import colour_utils

def makeDXF(theGarden):
	theData=sdxf.Drawing()
	#Blocks
	b=sdxf.Block('world')
	b.append(sdxf.Solid(points=[(0,0,0),(1,0,0),(1,1,0),(0,1,0)]))
	theData.blocks.append(b)		
	b=sdxf.Block('stem')
	b.append(sdxf.Circle(center=(0,0,0),radius=1,thickness=1))
	theData.blocks.append(b)
	b=sdxf.Block('seed')
	b.append(sdxf.Sphere())
	theData.blocks.append(b)
	b=sdxf.Block('canopy')
	b.append(sdxf.Hemisphere())
	theData.blocks.append(b)
	theWorldSize=theGarden.theWorldSize
	theData.append(sdxf.Insert('world',point=(0-(theWorldSize/2.0),0-(theWorldSize/2.0),0),xscale=theWorldSize,yscale=theWorldSize,zscale=0,color=0,rotation=0))
	dictColoursUsed={}
	for obj in theGarden.soil:
		x=obj.x
		y=obj.y
		z=obj.z
		aicLeaf=colour_utils.HSV_to_AIC(obj.colourLeaf)
		aicStem=colour_utils.HSV_to_AIC(obj.colourStem)
		aicSeedDispersed=colour_utils.HSV_to_AIC(obj.colourSeedDispersed)
		aicSeedAttached=colour_utils.HSV_to_AIC(obj.colourSeedAttached)
		#aicLeaf=90
		#aicStem=45
		#aicSeedDispersed=45
		#aicSeedAttached=1
		if obj.isSeed:
			theSeedRadius=obj.radiusSeed*obj.radiusSeedMultiplier
			#theData.append(sdxf.Insert('seed',point=(x,y,0+theSeedRadius),xscale=theSeedRadius,yscale=theSeedRadius,zscale=theSeedRadius,color=aicSeedDispersed,rotation=0))
			theData.append(sdxf.Insert('seed',point=(x,y,z),xscale=theSeedRadius,yscale=theSeedRadius,zscale=theSeedRadius,color=aicSeedDispersed,rotation=0))
		else:
			theStemRadius=obj.radiusStem*obj.radiusStemMultiplier
			theLeafRadius=obj.radiusLeaf*obj.radiusLeafMultiplier
			if (obj.crownShape == "PARA"):
				#bole height is not calculated. It's defined in the species file
				#print theLeafRadius
				#print obj.heightStem
				#print obj.boleHeight
				#print obj.heightStem*(obj.boleHeight/100.0)
				theData.append(sdxf.Insert('canopy',point=(x,y,z+obj.heightStem-obj.heightStem*(obj.boleHeight/100.0)),xscale=theLeafRadius,yscale=theLeafRadius,zscale=obj.heightStem*(obj.boleHeight/100.0),color=aicLeaf,rotation=0))
			else:
				#default shape is a perfect hemisphere
				theData.append(sdxf.Insert('canopy',point=(x,y,z+obj.heightStem-theLeafRadius),xscale=theLeafRadius,yscale=theLeafRadius,zscale=theLeafRadius,color=aicLeaf,rotation=0))
			theData.append(sdxf.Insert('stem',point=(x,y,z),xscale=theStemRadius,yscale=theStemRadius,zscale=obj.heightStem,color=aicStem,rotation=0))
			for attachedSeed in obj.seedList:
				x= attachedSeed.x
				y= attachedSeed.y
				z= attachedSeed.z
				theSeedRadius= attachedSeed.radiusSeed* attachedSeed.radiusSeedMultiplier
				theData.append(sdxf.Insert('seed',point=(x,y,z),xscale=theSeedRadius,yscale=theSeedRadius,zscale=theSeedRadius,color=aicSeedAttached,rotation=0))
	return theData

def writeDXF(outputDirectory, fileName, theData):
	###writes the files to a destination folder
	theData.saveas(outputDirectory + fileName+".dxf")