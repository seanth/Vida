"""This file is part of Vida.
    --------------------------
    Copyright 2022, Sean T. Hammond
    
    Vida is experimental in nature and is made available as a research courtesy "AS IS," but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 
    
    You should have received a copy of academic software agreement along with Vida. If not, see <https://github.com/seanth/Vida/blob/master/LICENSE.txt>.
"""

import glob
import os
import sys
import re

CFDGtext=\
"""
startshape garden

//include ../../Vida_Data/i_pix.cfdg
include %(thePathToiPix)s

rule garden{
    %(theWorldType)s
    %(theTimeStamp)s
    %%(thePopulationData)s
}

%(theWorldTypeRule)s

rule seed{CIRCLE{size 1 1}}
rule seedAttached{CIRCLE{size 1 1}}

rule leafCircle{CIRCLE{size 1 1}}
rule stemCircle{CIRCLE{size 1 1}}

rule leafRect{SQUARE{size 1 1}}
rule stemRect{SQUARE{size 1 1}}

rule leafHemi{
    91*[x 0.0086 r -1]SQUARE{size 0.1 1.0}
    91*[x -0.0086 r 1]SQUARE{size 0.1 1.0}
}

%(theTimeStampRule)s
"""

CFDGTopWorldRule=\
"""
rule worldTop{
    //provides border
    SQUARE{x 0 y 0 z -1000001 size %i %i b 1}
    SQUARE{x 0 y 0 z -1000000 size %i %i }
    //for 'blue sky':
    SQUARE{x 0 y 0 z -1000000 size %i %i hue 40.2 sat 0.4205 b 0.3837}
}
"""

CFDGBottomWorldRule=\
"""
rule worldBottom{
    //provides border
    SQUARE{x 0 y 0 z -1000001 size %i %i b 1}
    SQUARE{x 0 y 0 z -1000000 size %i %i }
    //for 'blue sky':
    SQUARE{x 0 y 0 z -1000000 size %i %i hue 206.6 sat 0.3037 b 0.74}
}
"""

CFDGSideWorldRule=\
"""
rule worldSide{
    //provides border
    SQUARE{x 0 y 0 z -1000001 size %i %i b 1}
    SQUARE{x 0 y 0 z -1000000 size %i %f}
    SQUARE{x 0 y 0 z -1000000 size %i %f b 1}
}
"""

CFDGTimeStamp="timeStamp{x %f y %f size %f %f}"

CFDGTimeStampRule=\
"""
rule timeStamp{
    C_5by5{x 0}
    Y_5by5{x 1.2}
    C_5by5{x 2.4}
    L_5by5{x 3.6}
    E_5by5{x 4.8}
        %(theCycleNumber)s
}
"""

#############
def initCFDGText(theGarden, displayType, percentTimeStamp, maxHeightPlant):
    ###display type: 1=bottom up; 2=side; 3=bottom up and side
    global CFDGtext
    global CFDGTopWorldRule
    global CFDGSideWorldRule
    global CFDGTimeStamp
    global CFDGTimeStampRule
    theWorldSize=theGarden.theWorldSize
    fractWorldGraphicEdgeSpacer=theGarden.fractionWorldGraphicEdgeSpacer
    fractWorldBetweenLRGraphicsSpacer=theGarden.fractionWorldBetweenLRGraphicsSpacer
    fractWorldBetweenTBGraphicsSpacer=theGarden.fractionWorldBetweenTBGraphicsSpacer
    worldX=theWorldSize
    if displayType==1:
        ###bottom Up
        worldY1=theWorldSize
        worldY2=0
        worldY=worldY1+worldY2
        worldTypeCode="worldBottom{x %f y %f}"
        worldTypeCode=worldTypeCode % (0.0, 0.0)
        worldTypeRule=CFDGBottomWorldRule
        worldTypeRule=worldTypeRule % (worldX+(worldX*fractWorldGraphicEdgeSpacer), worldY1+(worldY1* fractWorldGraphicEdgeSpacer), worldX, worldY1, worldX-1, worldY1-1)
    elif displayType==2:
        ###top down
        worldY1=theWorldSize
        worldY2=0
        worldY=worldY1+worldY2
        worldTypeCode="worldTop{x %f y %f}"
        worldTypeCode=worldTypeCode % (0.0, 0.0)
        worldTypeRule=CFDGTopWorldRule
        worldTypeRule=worldTypeRule % (worldX+(worldX*fractWorldGraphicEdgeSpacer), worldY1+(worldY1* fractWorldGraphicEdgeSpacer), worldX, worldY1, worldX-1, worldY1-1)
    elif displayType==3:
        ###side view
        worldY1=0
        worldY2=maxHeightPlant
        worldY=worldY1+worldY2
        worldTypeCode="worldSide{x %f y %f}"
        worldTypeCode=worldTypeCode % (0.0, worldY/2.0)
        worldTypeRule =CFDGSideWorldRule
        worldTypeRule=worldTypeRule % (worldX+(worldX*fractWorldGraphicEdgeSpacer), worldY2+(worldY1* fractWorldGraphicEdgeSpacer),worldX, worldY2, worldX-1, worldY2-1)
    elif displayType==12:
        ###bottom up and top down
        worldY1=theWorldSize
        worldY2=theWorldSize
        worldY= theWorldSize
        worldTypeCode="worldBottom{x %f y %f}\n        worldTop{x %f y %f}"
        worldTypeCode=worldTypeCode % (0.0, 0.0, worldY1+(worldY1* fractWorldBetweenLRGraphicsSpacer), 0.0)
        worldTypeRule=CFDGBottomWorldRule
        worldTypeRule=worldTypeRule % (worldX+(worldX* fractWorldGraphicEdgeSpacer), worldY1+(worldY1* fractWorldGraphicEdgeSpacer), worldX, worldY1, worldX-1, worldY1-1)
        worldTypeRule=worldTypeRule+CFDGTopWorldRule
        worldTypeRule=worldTypeRule % (worldX+(worldX* fractWorldGraphicEdgeSpacer), worldY1+(worldY1* fractWorldGraphicEdgeSpacer), worldX, worldY1, worldX-1, worldY1-1)
    elif displayType==13:
        ###bottom up and side view
        worldY1=theWorldSize
        worldY2=maxHeightPlant
        worldY=worldY1+worldY2
        worldTypeCode="worldBottom{x %f y %f}\n        worldSide{x %f y %f}"
        worldTypeCode=worldTypeCode % (0.0, 0.0, 0.0, ((worldY+(theWorldSize*fractWorldBetweenTBGraphicsSpacer))/-2))
        worldTypeRule= CFDGBottomWorldRule
        worldTypeRule=worldTypeRule % (worldX+(worldX* fractWorldGraphicEdgeSpacer), worldY1+(worldY1* fractWorldGraphicEdgeSpacer), worldX, worldY1, worldX-1, worldY1-1)
        worldTypeRule=worldTypeRule+CFDGSideWorldRule
        #worldTypeRule=worldTypeRule % (worldX, worldY2, worldX-1, worldY2-1)
        worldTypeRule=worldTypeRule % (worldX+(worldX*fractWorldGraphicEdgeSpacer), worldY2+(worldY1* fractWorldGraphicEdgeSpacer),worldX, worldY2, worldX-1, worldY2-1)
    elif displayType==21:
        ###bottom up and top down
        worldY1=theWorldSize
        worldY2=theWorldSize
        worldY= theWorldSize
        worldTypeCode="worldTop{x %f y %f}\n        worldBottom{x %f y %f}"
        worldTypeCode=worldTypeCode % (0.0, 0.0, worldY1+(worldY1* fractWorldBetweenLRGraphicsSpacer), 0.0)
        worldTypeRule=CFDGTopWorldRule
        worldTypeRule=worldTypeRule % (worldX+(worldX* fractWorldGraphicEdgeSpacer), worldY1+(worldY1* fractWorldGraphicEdgeSpacer), worldX, worldY1, worldX-1, worldY1-1)
        worldTypeRule=worldTypeRule+CFDGBottomWorldRule
        worldTypeRule=worldTypeRule % (worldX+(worldX* fractWorldGraphicEdgeSpacer), worldY1+(worldY1* fractWorldGraphicEdgeSpacer), worldX, worldY1, worldX-1, worldY1-1)
    elif displayType==23:
        ###bottom up and side view
        worldY1=theWorldSize
        worldY2=maxHeightPlant
        worldY=worldY1+worldY2
        worldTypeCode="worldTop{x %f y %f}\n        worldSide{x %f y %f}"
        worldTypeCode=worldTypeCode % (0.0, 0.0, 0.0, ((worldY+(theWorldSize*fractWorldBetweenTBGraphicsSpacer))/-2))
        worldTypeRule=CFDGTopWorldRule
        worldTypeRule=worldTypeRule % (worldX+(worldX* fractWorldGraphicEdgeSpacer), worldY1+(worldY1* fractWorldGraphicEdgeSpacer), worldX, worldY1, worldX-1, worldY1-1)
        worldTypeRule=worldTypeRule+CFDGSideWorldRule
        worldTypeRule=worldTypeRule % (worldX+(worldX* fractWorldGraphicEdgeSpacer), worldY2+(worldY2* fractWorldGraphicEdgeSpacer),worldX, worldY2, worldX-1, worldY2-1)
    elif displayType==123:
        ###bottom up and top down and side
        worldY1=theWorldSize
        worldY2=maxHeightPlant
        worldY=worldY1+worldY2
        worldTypeCode="worldBottom{x %f y %f}\n        worldTop{x %f y %f}\n        worldSide{x %f y %f}\n        worldSide{x %f y %f}"
        worldTypeCode=worldTypeCode % (0.0, 0.0, worldY1+(worldY1*0.3), 0.0, 0.0, -(worldY2+(worldY1/4)), worldY1+(worldY1*0.3), -(worldY2+(worldY1/4)))
        worldTypeRule=CFDGBottomWorldRule
        worldTypeRule=worldTypeRule % (worldX+(worldX*0.3), worldY1+(worldY1*0.3), worldX, worldY1, worldX-1, worldY1-1)
        worldTypeRule=worldTypeRule+CFDGTopWorldRule
        worldTypeRule=worldTypeRule % (worldX+(worldX*0.3), worldY1+(worldY1*0.3), worldX, worldY1, worldX-1, worldY1-1)
        worldTypeRule=worldTypeRule+CFDGSideWorldRule
        worldTypeRule=worldTypeRule % (worldX, worldY2, worldX-1, worldY2-1)

    if percentTimeStamp>0.0:
        timeStampCode= CFDGTimeStamp
        ###this puts the time stamp in the lower left corner
        i=(percentTimeStamp*theWorldSize)/100
        x= (worldX/-2)+(i/2)
        if displayType==1 or displayType==2 or displayType==12 or displayType==21:
            ###bottom up or top down
            y= (worldY/-2)-(i/2)-1
        if displayType==3:
            y= 0-(i/2)-1
        if displayType==13 or displayType==23 or displayType==123:
            y=(worldY1/-2)-worldY2-(theWorldSize* fractWorldBetweenTBGraphicsSpacer/2)-(i/2)-1
        timeStampCode = timeStampCode % (x, y, i, i)
    #print CFDGtext
    if sys.platform=="win32":
        retCFDGtext=CFDGtext % {"thePathToiPix": "\"../../../Vida_Data/i_pix.cfdg\"", "theWorldType": worldTypeCode, "theTimeStamp": timeStampCode, "theWorldTypeRule": worldTypeRule, "theTimeStampRule": CFDGTimeStampRule}
    else:
        #retCFDGtext=CFDGtext % {"thePathToiPix": "../../../Vida_Data/i_pix.cfdg", "theWorldType": worldTypeCode, "thePopulationData":"%(thePopulationData)s", "theTimeStamp": timeStampCode, "theWorldTypeRule": worldTypeRule, "theTimeStampRule": CFDGTimeStampRule, "theCycleNumber":"%(theCycleNumber)s"}
        retCFDGtext=CFDGtext % {"thePathToiPix": "\"../../../Vida_Data/i_pix.cfdg\"", "theWorldType": worldTypeCode, "theTimeStamp": timeStampCode, "theWorldTypeRule": worldTypeRule, "theTimeStampRule": CFDGTimeStampRule}
        #CFDGtext=CFDGtext % {"thePathToiPix": "../../../Vida_Data/i_pix.cfdg"}
    #print CFDGtext
    return retCFDGtext


def makeCFDG(theView, CFDGtext, theGarden, cycleNumber):
    thePlantData=""
    theWorldSize=theGarden.theWorldSize
    fractWorldGraphicEdgeSpacer=theGarden.fractionWorldGraphicEdgeSpacer
    fractWorldBetweenLRGraphicsSpacer=theGarden.fractionWorldBetweenLRGraphicsSpacer
    fractWorldBetweenTBGraphicsSpacer=theGarden.fractionWorldBetweenTBGraphicsSpacer
    theData= CFDGtext
    seedCode="         seed{x %2f y %2f z %2f hue %2f sat %2f b %2f alpha -%f size %2f %2f}\n"
    attachedSeedCode="         seedAttached{x %2f y %2f z %2f hue %2f sat %2f b %2f alpha -%f size %2f %2f}\n"
    leafCode1="         leafCircle{x %2f y %2f z %2f hue %2f sat %2f b %2f alpha -%f size %2f %2f}\n"
    stemCode1="         stemCircle{x %2f y %2f z %2f hue %2f sat %2f b %2f alpha -%f size %2f %2f}\n"
    leafCode2="         leafRect{x %2f y %2f z %2f hue %2f sat %2f b %2f alpha -%f size %2f %2f}\n"
    stemCode2="         stemRect{x %2f y %2f z %2f hue %2f sat %2f b %2f alpha -%f size %2f %2f}\n"
    leafCode3="         leafHemi{x %2f y %2f z %2f hue %2f sat %2f b %2f alpha -%f size %2f}\n"
    for obj in theGarden.soil:
        x=obj.x
        y=obj.y
        color1=obj.colourSpecies[0]
        color2=obj.colourSpecies[1]
        color3=obj.colourSpecies[2]
        alpha=obj.canopyTransmittance
        if obj.isSeed:
            theSeedDiameter=obj.radiusSeed*2*obj.radiusSeedMultiplier
            theSeedBorder=theSeedDiameter-(theSeedDiameter*obj.borderImagePercent/100)        
            color4=obj.colourSeedDispersed[0]
            color5=obj.colourSeedDispersed[1]
            color6=obj.colourSeedDispersed[2]
            if theView==1:
                ###bottom up
                z1=10000.0            
                thePlantData=thePlantData+seedCode %  (x, y, z1, color1, color2, color3, 0.0, theSeedDiameter, theSeedDiameter)
                thePlantData=thePlantData+seedCode %  (x, y, z1, color4, color5, color6, 0.0, theSeedBorder, theSeedBorder)
            elif theView==2:
                ###top down
                z2=0.0            
                thePlantData=thePlantData+seedCode %  (x, y, z2, color1, color2, color3, 0.0, theSeedDiameter, theSeedDiameter)
                thePlantData=thePlantData+seedCode %  (x, y, z2, color4, color5, color6, 0.0, theSeedBorder, theSeedBorder)
            elif theView==3:
                ###side view
                y3=0.0
                z3=0.0        
                thePlantData=thePlantData+seedCode %  (x, y3, z3, color1, color2, color3, 0.0, theSeedDiameter, theSeedDiameter)
                thePlantData=thePlantData+seedCode %  (x, y3, z3, color4, color5, color6, 0.0, theSeedBorder, theSeedBorder)
            elif theView==12:
                ###bottom up
                z1=10000.0        
                thePlantData=thePlantData+seedCode %  (x, y, z1, color1, color2, color3, 0.0, theSeedDiameter, theSeedDiameter)
                thePlantData=thePlantData+seedCode %  (x, y, z1, color4, color5, color6, 0.0, theSeedBorder, theSeedBorder)
                ###top down
                z2=0.0            
                thePlantData=thePlantData+seedCode %  ((theWorldSize)+(theWorldSize* fractWorldBetweenLRGraphicsSpacer)-x, y, z2, color1, color2, color3, 0.0, theSeedDiameter, theSeedDiameter)
                thePlantData=thePlantData+seedCode %  ((theWorldSize)+(theWorldSize* fractWorldBetweenLRGraphicsSpacer)-x, y, z2, color4, color5, color6, 0.0, theSeedBorder, theSeedBorder)
            elif theView==21:
                ###top down
                z2=0.0            
                thePlantData=thePlantData+seedCode %  (x, y, z2, color1, color2, color3, 0.0, theSeedDiameter, theSeedDiameter)
                thePlantData=thePlantData+seedCode %  (x, y, z2, color4, color5, color6, 0.0, theSeedBorder, theSeedBorder)
                ###bottom up and side view
                z1=10000.0            
                thePlantData=thePlantData+seedCode %  ((theWorldSize)+(theWorldSize* fractWorldBetweenLRGraphicsSpacer)-x, y, z1, color1, color2, color3, 0.0, theSeedDiameter, theSeedDiameter)
                thePlantData=thePlantData+seedCode %  ((theWorldSize)+(theWorldSize* fractWorldBetweenLRGraphicsSpacer)-x, y, z1, color4, color5, color6, 0.0, theSeedBorder, theSeedBorder)
            elif theView==13 or theView==23:
                if theView==13: z1=10000.0
                if theView==23: z1=0.0
                #40 is the size of the side view world.
                #set up in init of graphics
                y3=(theWorldSize/-2)-50.0-(theWorldSize* fractWorldBetweenTBGraphicsSpacer/2)
                z3=0.0                
                thePlantData=thePlantData+seedCode %  (x, y, z1, color1, color2, color3, 0.0, theSeedDiameter, theSeedDiameter)
                thePlantData=thePlantData+seedCode %  (x, y, z1, color4, color5, color6, 0.0, theSeedBorder, theSeedBorder)
                thePlantData=thePlantData+seedCode %  (x, y3, z3, color1, color2, color3, 0.0, theSeedDiameter, theSeedDiameter)
                thePlantData=thePlantData+seedCode %  (x, y3, z3, color4, color5, color6, 0.0, theSeedBorder, theSeedBorder)
            elif theView==123:
                z1=10000.0
                y3=(theWorldSize/-2)-35
                z3=0.0
                ###bottom up
                thePlantData=thePlantData+seedCode %  (x, y, z1, color1, color2, color3, 0.0, theSeedDiameter, theSeedDiameter)
                thePlantData=thePlantData+seedCode %  (x, y, z1, color4, color5, color6, 0.0, theSeedBorder, theSeedBorder)
                ###top down
                thePlantData=thePlantData+seedCode %  (x+10, y, z1, color1, color2, color3, 0.0, theSeedDiameter, theSeedDiameter)
                thePlantData=thePlantData+seedCode %  (x+10, y, z1, color4, color5, color6, 0.0, theSeedBorder, theSeedBorder)
                ###bottom up side
                thePlantData=thePlantData+seedCode %  (x, y3, z3, color1, color2, color3, 0.0, theSeedDiameter, theSeedDiameter)
                thePlantData=thePlantData+seedCode %  (x, y3, z3, color4, color5, color6, 0.0, theSeedBorder, theSeedBorder)
                ###top down side
                thePlantData=thePlantData+seedCode %  (x+10, y3, z3, color1, color2, color3, 0.0, theSeedDiameter, theSeedDiameter)
                thePlantData=thePlantData+seedCode %  (x+10, y3, z3, color4, color5, color6, 0.0, theSeedBorder, theSeedBorder)    
        else:
            theStemDiameter=obj.radiusStem*2*obj.radiusStemMultiplier
            theStemBorder1xy= theStemDiameter-(theStemDiameter*obj.borderImagePercent/100)
            theLeafDiameter=obj.radiusLeaf*2*obj.radiusLeafMultiplier
            theLeafBorder1xy= theLeafDiameter-(theLeafDiameter*obj.borderImagePercent/100)    
            if theView==3 or theView==13 or theView==23:
                if obj.heightLeafMax<=0.1:
                    leafHeight=0.1##this is so a very thin leaf is visable at all
                else:
                    leafHeight=obj.heightLeafMax
                theStemBorderAdj= theStemDiameter*obj.borderImagePercent/100
                theLeafBorderAdj= theLeafDiameter*obj.borderImagePercent/100
                theStemBorder2x=theStemDiameter-theStemBorderAdj
                theStemBorder2y=obj.heightStem-theStemBorderAdj
                theLeafBorder2x=theLeafDiameter-theLeafBorderAdj
                theLeafBorder2y=leafHeight-theLeafBorderAdj
            color4L=obj.colourLeaf[0]
            color5L=obj.colourLeaf[1]
            color6L=obj.colourLeaf[2]
            color4S=obj.colourStem[0]
            color5S=obj.colourStem[1]
            color6S=obj.colourStem[2]
            if theView==1:
                z1Leaf=obj.heightStem+obj.heightLeafMax
                z1Stem=obj.heightStem
                thePlantData= thePlantData+leafCode1 %  (x, y, -z1Leaf, color1, color2, color3, alpha, theLeafDiameter, theLeafDiameter)
                thePlantData=thePlantData+leafCode1 %  (x, y, -z1Leaf, color4L, color5L, color6L, alpha+alpha, theLeafBorder1xy, theLeafBorder1xy)        
                thePlantData=thePlantData+stemCode1 %  (x, y, -z1Stem, color1, color2, color3, 0.0, theStemDiameter, theStemDiameter)
                thePlantData=thePlantData+stemCode1 %  (x, y, -z1Stem, color4S, color5S, color6S, 0.0, theStemBorder1xy, theStemBorder1xy)
            if theView==2:
                z2Leaf=obj.heightStem+obj.heightLeafMax
                z2Stem=obj.heightStem
                thePlantData= thePlantData+leafCode1 %  (x, y, z2Leaf, color1, color2, color3, alpha, theLeafDiameter, theLeafDiameter)
                thePlantData=thePlantData+leafCode1 %  (x, y, z2Leaf, color4L, color5L, color6L, alpha+alpha, theLeafBorder1xy, theLeafBorder1xy)        
                thePlantData=thePlantData+stemCode1 %  (x, y, z2Stem, color1, color2, color3, 0.0, theStemDiameter, theStemDiameter)
                thePlantData=thePlantData+stemCode1 %  (x, y, z2Stem, color4S, color5S, color6S, 0.0, theStemBorder1xy, theStemBorder1xy)    
            elif theView==3:
                y2=obj.heightStem
                y3=obj.heightStem/2.0
                z3=-y
                if obj.leafIsHemisphere:
                    thePlantData=thePlantData+leafCode3 %  (x, (y2-(theLeafDiameter/4.0)), z3, color1, color2, color3, alpha, theLeafDiameter/2.0)
                    thePlantData=thePlantData+leafCode3 %  (x, (y2-(theLeafDiameter/4.0)), z3, color4L, color5L, color6L, alpha+alpha, theLeafBorder2x/2.0)
                else:
                    thePlantData= thePlantData+leafCode2 %  (x, y2, z3, color1, color2, color3, alpha, theLeafDiameter, leafHeight)
                    thePlantData=thePlantData+leafCode2 %  (x, y2, z3, color4L, color5L, color6L, alpha+alpha, theLeafBorder2x, theLeafBorder2y)
                thePlantData=thePlantData+stemCode2 %  (x, y3, z3-0.00003, color1, color2, color3, 0.0, theStemDiameter, obj.heightStem)
                thePlantData=thePlantData+stemCode2 %  (x, y3, z3-0.00003, color4S, color5S, color6S, 0.0, theStemBorder2x, theStemBorder2y)
            elif theView==12:
                z1Leaf=obj.heightStem+obj.heightLeafMax
                z1Stem=obj.heightStem
                thePlantData= thePlantData+leafCode1 %  (x, y, -z1Leaf, color1, color2, color3, alpha, theLeafDiameter, theLeafDiameter)
                thePlantData=thePlantData+leafCode1 %  (x, y, -z1Leaf, color4L, color5L, color6L, alpha+alpha, theLeafBorder1xy, theLeafBorder1xy)        
                thePlantData=thePlantData+stemCode1 %  (x, y, -z1Stem, color1, color2, color3, 0.0, theStemDiameter, theStemDiameter)
                thePlantData=thePlantData+stemCode1 %  (x, y, -z1Stem, color4S, color5S, color6S, 0.0, theStemBorder1xy, theStemBorder1xy)
                z2Leaf=obj.heightStem+obj.heightLeafMax
                z2Stem=obj.heightStem
                thePlantData= thePlantData+leafCode1 %  ((theWorldSize)+(theWorldSize*0.3)-x, y, z2Leaf, color1, color2, color3, alpha, theLeafDiameter, theLeafDiameter)
                thePlantData=thePlantData+leafCode1 %  ((theWorldSize)+(theWorldSize*0.3)-x, y, z2Leaf, color4L, color5L, color6L, alpha+alpha, theLeafBorder1xy, theLeafBorder1xy)        
                thePlantData=thePlantData+stemCode1 %  ((theWorldSize)+(theWorldSize*0.3)-x, y, z2Stem, color1, color2, color3, 0.0, theStemDiameter, theStemDiameter)
                thePlantData=thePlantData+stemCode1 %  ((theWorldSize)+(theWorldSize*0.3)-x, y, z2Stem, color4S, color5S, color6S, 0.0, theStemBorder1xy, theStemBorder1xy)
            elif theView==21:
                z2Leaf=obj.heightStem+obj.heightLeafMax
                z2Stem=obj.heightStem
                thePlantData= thePlantData+leafCode1 %  (x, y, z2Leaf, color1, color2, color3, alpha, theLeafDiameter, theLeafDiameter)
                thePlantData=thePlantData+leafCode1 %  (x, y, z2Leaf, color4L, color5L, color6L, alpha+alpha, theLeafBorder1xy, theLeafBorder1xy)        
                thePlantData=thePlantData+stemCode1 %  (x, y, z2Stem, color1, color2, color3, 0.0, theStemDiameter, theStemDiameter)
                thePlantData=thePlantData+stemCode1 %  (x, y, z2Stem, color4S, color5S, color6S, 0.0, theStemBorder1xy, theStemBorder1xy)
                z1Leaf=obj.heightStem+obj.heightLeafMax
                z1Stem=obj.heightStem
                thePlantData= thePlantData+leafCode1 %  ((theWorldSize)+(theWorldSize*0.3)-x, y, -z1Leaf, color1, color2, color3, alpha, theLeafDiameter, theLeafDiameter)
                thePlantData=thePlantData+leafCode1 %  ((theWorldSize)+(theWorldSize*0.3)-x, y, -z1Leaf, color4L, color5L, color6L, alpha+alpha, theLeafBorder1xy, theLeafBorder1xy)        
                thePlantData=thePlantData+stemCode1 %  ((theWorldSize)+(theWorldSize*0.3)-x, y, -z1Stem, color1, color2, color3, 0.0, theStemDiameter, theStemDiameter)
                thePlantData=thePlantData+stemCode1 %  ((theWorldSize)+(theWorldSize*0.3)-x, y, -z1Stem, color4S, color5S, color6S, 0.0, theStemBorder1xy, theStemBorder1xy)
            elif theView==13 or theView==23:
                z1Leaf=obj.heightStem+obj.heightLeafMax
                z1Stem=obj.heightStem
                if theView==13:
                    z1Leaf=0-z1Leaf
                    z1Stem=0-z1Stem
                y2=(theGarden.theWorldSize/-2)-50.0+obj.heightStem-(theWorldSize* fractWorldBetweenTBGraphicsSpacer/2)
                y3=(theGarden.theWorldSize/-2)-50.0+(obj.heightStem/2.0)-(theWorldSize* fractWorldBetweenTBGraphicsSpacer/2)
                z3=-y
                thePlantData= thePlantData+leafCode1 %  (x, y, z1Leaf, color1, color2, color3, alpha, theLeafDiameter, theLeafDiameter)
                thePlantData=thePlantData+leafCode1 %  (x, y, z1Leaf, color4L, color5L, color6L, alpha+alpha, theLeafBorder1xy, theLeafBorder1xy)    
                thePlantData=thePlantData+stemCode1 %  (x, y, z1Stem, color1, color2, color3, 0.0, theStemDiameter, theStemDiameter)
                thePlantData=thePlantData+stemCode1 %  (x, y, z1Stem, color4S, color5S, color6S, 0.0, theStemBorder1xy, theStemBorder1xy)    

                if obj.leafIsHemisphere:
                    thePlantData=thePlantData+leafCode3 %  (x, (y2-(theLeafDiameter/4.0)), z3, color1, color2, color3, alpha, theLeafDiameter/2.0)
                    thePlantData=thePlantData+leafCode3 %  (x, (y2-(theLeafDiameter/4.0)), z3, color4L, color5L, color6L, alpha+alpha, theLeafBorder2x/2.0)
                else:
                    thePlantData= thePlantData+leafCode2 %  (x, y2, z3, color1, color2, color3, alpha, theLeafDiameter, leafHeight)
                    thePlantData=thePlantData+leafCode2 %  (x, y2, z3, color4L, color5L, color6L, alpha+alpha, theLeafBorder2x, theLeafBorder2y)
                thePlantData=thePlantData+stemCode2 %  (x, y3, z3-0.00003, color1, color2, color3, 0.0, theStemDiameter, obj.heightStem)
                thePlantData=thePlantData+stemCode2 %  (x, y3, z3-0.00003, color4S, color5S, color6S, 0.0, theStemBorder2x, theStemBorder2y)

            for attachedSeed in obj.seedList:
                x= attachedSeed.x
                y= attachedSeed.y
                theSeedDiameter= attachedSeed.radiusSeed*2* attachedSeed.radiusSeedMultiplier
                theSeedBorder=theSeedDiameter-(theSeedDiameter* attachedSeed.borderImagePercent/100)
                color4= attachedSeed.colourSeedAttached[0]
                color5= attachedSeed.colourSeedAttached[1]
                color6= attachedSeed.colourSeedAttached[2]
                if theView==1:
                    #z1=10000.0
                    z1=obj.heightStem+obj.heightLeafMax
                    thePlantData=thePlantData+ attachedSeedCode %  (x, y, -z1, color1, color2, color3, 0.0, theSeedDiameter, theSeedDiameter)
                    thePlantData=thePlantData+ attachedSeedCode %  (x, y, -z1, color4, color5, color6, 0.0, theSeedBorder, theSeedBorder)
                elif theView==2:
                    #z2=10000.0
                    z2=obj.heightStem+obj.heightLeafMax
                    thePlantData=thePlantData+ attachedSeedCode %  (x, y, z2, color1, color2, color3, 0.0, theSeedDiameter, theSeedDiameter)
                    thePlantData=thePlantData+ attachedSeedCode %  (x, y, z2, color4, color5, color6, 0.0, theSeedBorder, theSeedBorder)
                elif theView==3:
                    y3=attachedSeed.z
                    #y3=obj.heightStem+(obj.heightLeafMax/2.0)
                    z3=-y
                    thePlantData=thePlantData+ attachedSeedCode %  (x, y3, z3, color1, color2, color3, 0.0, theSeedDiameter, theSeedDiameter)
                    thePlantData=thePlantData+ attachedSeedCode %  (x, y3, z3, color4, color5, color6, 0.0, theSeedBorder, theSeedBorder)
                elif theView==12:
                    #z1=10000.0
                    z1=obj.heightStem+obj.heightLeafMax
                    thePlantData=thePlantData+ attachedSeedCode %  (x, y, -z1, color1, color2, color3, 0.0, theSeedDiameter, theSeedDiameter)
                    thePlantData=thePlantData+ attachedSeedCode %  (x, y, -z1, color4, color5, color6, 0.0, theSeedBorder, theSeedBorder)
                    #z2=10000.0
                    z2=obj.heightStem+obj.heightLeafMax
                    thePlantData=thePlantData+ attachedSeedCode %  ((theWorldSize)+(theWorldSize*0.3)-x, y, z2, color1, color2, color3, 0.0, theSeedDiameter, theSeedDiameter)
                    thePlantData=thePlantData+ attachedSeedCode %  ((theWorldSize)+(theWorldSize*0.3)-x, y, z2, color4, color5, color6, 0.0, theSeedBorder, theSeedBorder)
                elif theView==21:
                    #z2=10000.0
                    z2=obj.heightStem+obj.heightLeafMax
                    thePlantData=thePlantData+ attachedSeedCode %  (x, y, z2, color1, color2, color3, 0.0, theSeedDiameter, theSeedDiameter)
                    thePlantData=thePlantData+ attachedSeedCode %  (x, y, z2, color4, color5, color6, 0.0, theSeedBorder, theSeedBorder)
                    #z1=10000.0
                    z1=obj.heightStem+obj.heightLeafMax
                    thePlantData=thePlantData+ attachedSeedCode %  ((theWorldSize)+(theWorldSize*0.3)-x, y, -z1, color1, color2, color3, 0.0, theSeedDiameter, theSeedDiameter)
                    thePlantData=thePlantData+ attachedSeedCode %  ((theWorldSize)+(theWorldSize*0.3)-x, y, -z1, color4, color5, color6, 0.0, theSeedBorder, theSeedBorder)
                elif theView==13 or theView==23:
                    z1=obj.heightStem+obj.heightLeafMax
                    if theView==13: z1=0-z1
                    #y3=(theGarden.theWorldSize/-2)-50.0+obj.heightStem+(obj.heightLeafMax/2.0)
                    y3=(theGarden.theWorldSize/-2)-50.0+attachedSeed.z-(theWorldSize* fractWorldBetweenTBGraphicsSpacer/2)
                    z3=-y
                    thePlantData=thePlantData+ attachedSeedCode %  (x, y, z1, color1, color2, color3, 0.0, theSeedDiameter, theSeedDiameter)
                    thePlantData=thePlantData+ attachedSeedCode %  (x, y, z1, color4, color5, color6, 0.0, theSeedBorder, theSeedBorder)
                    thePlantData=thePlantData+ attachedSeedCode %  (x, y3, z3, color1, color2, color3, 0.0, theSeedDiameter, theSeedDiameter)
                    thePlantData=thePlantData+ attachedSeedCode %  (x, y3, z3, color4, color5, color6, 0.0, theSeedBorder, theSeedBorder)

    ###insert the time stamp into graphics
    timeString=str(cycleNumber)
    loc=7.2
    theTime=""
    for k in range(len(timeString)):
        theTime= theTime+"     NUM_%i_5by5{x %2f}\n" % (int(timeString[k]), loc)
        loc=loc+1.2

    theData=CFDGtext % {"thePopulationData":thePlantData, "theCycleNumber":theTime}

    return theData

def writeCFDG(outputDirectory, fileName, theData):
    ###writes the files to a destination folder
    cfdg = open(outputDirectory + fileName+".cfdg", 'w')
    cfdg.write(theData)
    cfdg.close()

def outputPNGs(inputDirectory, outputDirectory):
    #can supply a directory or list of files
    #theInput should either be a list of files or a directory
    if type(inputDirectory)==list:
        allTargetFiles=inputDirectory
    else:
        allTargetFiles=glob.glob(inputDirectory +"*.cfdg")
    inputDirectory=os.path.dirname(allTargetFiles[0])+"/"
    for fileItem in allTargetFiles:
        #print "*********"+fileItem
        pngFileName =fileItem.replace(outputDirectory, "")
        #print "*********"+pngFileName
        pngFileName = pngFileName.replace(".cfdg", "")
        pngFileName= pngFileName +".png"
        ###this should get the cfdg app to do its thing
        ###windows and linux seem to handle path names differently
        if sys.platform=="win32":
            theArg="ContextFreeCLI.exe /c /b 0 /s 500 %s %s"
            theArg=theArg % (fileItem, pngFileName)
        else:
            theArg="cfdg -q -c -b 0 -s 500 %s %s"
            #theArg="cfdg -c -b 0 -s 500 %s %s"
            theArg=theArg % (fileItem, outputDirectory + pngFileName)
        os.system(theArg)

#def convertDXF(inputDirectory, outputDirectory):

def deleteCFDGFiles(outputDirectory):
    allTargetFiles=glob.glob(outputDirectory+"*.cfdg")
    for fileItem in allTargetFiles:
        #print "Deleting .cfdg file %s." % (fileItem)
        os.remove(fileItem)

def outputMOV(outputDirectory, simulationName, framesPerSec):
    # if sys.platform=="darwin":
    #     ###Absolute path to output png files necessary
    #     ###for the embedded applescript to work correctly
    #     absolutePath=os.path.abspath(outputDirectory)
    #     #print "#################"
    #     #print simulationName
    #     firstFile=glob.glob(outputDirectory+"*.png")[0]
    #     firstFile=firstFile.replace(outputDirectory,"")
    #     ###turn "/" into ":" so applescript understand the path
    #     absolutePath= absolutePath.replace("/", ":")
    #     if not absolutePath.endswith(":"):
    #         absolutePath=absolutePath+":"
    #     ###get quicktime to make the video###
    #     appleScriptCmd="""osascript<<END
    #     set folderPath to path to me as string
    #     set the clipboard to folderPath as text
    #     tell application "QuickTime Player 7"
    #     activate
    #     --need absolute path of file here--
    #     open image sequence "%s%s" frames per second %i
    #     tell movie 1
    #         save self contained in "%s%s.mov"
    #         --optional close?
    #         --close
    #     end tell
    #     end tell
    #     """
    #     appleScriptCmd=appleScriptCmd % (absolutePath, firstFile, framesPerSec, absolutePath, simulationName)
    #     os.system(appleScriptCmd)
    #     print "     Quicktime video made"
    #uses ffmpeg to make videos
    ###Absolute path to output png files necessary
    absolutePath=os.path.abspath(outputDirectory)
    firstFile=glob.glob(outputDirectory+"*.png")[0]
    firstFile=os.path.normpath(firstFile)
    outputDirectory = os.path.normpath(outputDirectory)
    firstFile=firstFile.replace(outputDirectory,"")
    firstFile=os.path.normpath(firstFile)
    firstFile=os.path.splitext(firstFile)[0]
    firstFile=re.sub(r'\d', '', firstFile)
    firstFile= firstFile.rstrip("-")

    theArg = "ffmpeg -hide_banner -loglevel panic -framerate %i -i %s%s-%%01d.png -c:v libx264 -pix_fmt yuv420p %s%s.mp4"
    #theArg = "ffmpeg -framerate %i -i %s%s-%%01d.png -c:v libx264 -pix_fmt yuv420p %s%s.mp4"
    theArg=theArg % (framesPerSec, absolutePath, firstFile, absolutePath, firstFile)
    os.system(theArg)
    print("     mp4 video made")
    ###Delete png files if requested
    #if deletePngFiles:
    #    allTargetFiles =glob.glob(outputDirectory+"*.png")
    #    for fileItem in allTargetFiles:
    #        print "Deleting .png file %s." % (fileItem)
    #        os.remove(fileItem)






