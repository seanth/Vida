#STH 2016.0112
import sys
def HSV_to_ACI(theHSV):
    import colorsys
    #this will accept a HSV value and return the closest matching autocad colour index
    #the input is in the form [H in degrees, S in decimal1, V in decimal1]
    #degrees is between 0 and 360, inclusive
    #decimal1 and decimal2 are between 0 and 1, inclusive

    dictRGBtoACI={(0,0,0): 0, (255,0,0): 1, (255,255,0): 2, (0,255,0): 3, (0,255,255): 4, (0,0,255): 5, (255,0,255): 6, (255,255,255): 7, (65,65,65): 8, (128,128,128): 9, (255,0,0): 10, (255,170,170): 11, (189,0,0): 12, (189,126,126): 13, (129,0,0): 14, (129,86,86): 15, (104,0,0): 16, (104,69,69): 17, (79,0,0): 18, (79,53,53): 19, (255,63,0): 20, (255,191,170): 21, (189,46,0): 22, (189,141,126): 23, (129,31,0): 24, (129,96,86): 25, (104,25,0): 26, (104,78,69): 27, (79,19,0): 28, (79,59,53): 29, (255,127,0): 30, (255,212,170): 31, (189,94,0): 32, (189,157,126): 33, (129,64,0): 34, (129,107,86): 35, (104,52,0): 36, (104,86,69): 37, (79,39,0): 38, (79,66,53): 39, (255,191,0): 40, (255,234,170): 41, (189,141,0): 42, (189,173,126): 43, (129,96,0): 44, (129,118,86): 45, (104,78,0): 46, (104,95,69): 47, (79,59,0): 48, (79,73,53): 49, (255,255,0): 50, (255,255,170): 51, (189,189,0): 52, (189,189,126): 53, (129,129,0): 54, (129,129,86): 55, (104,104,0): 56, (104,104,69): 57, (79,79,0): 58, (79,79,53): 59, (191,255,0): 60, (234,255,170): 61, (141,189,0): 62, (173,189,126): 63, (96,129,0): 64, (118,129,86): 65, (78,104,0): 66, (95,104,69): 67, (59,79,0): 68, (73,79,53): 69, (127,255,0): 70, (212,255,170): 71, (94,189,0): 72, (157,189,126): 73, (64,129,0): 74, (107,129,86): 75, (52,104,0): 76, (86,104,69): 77, (39,79,0): 78, (66,79,53): 79, (63,255,0): 80, (191,255,170): 81, (46,189,0): 82, (141,189,126): 83, (31,129,0): 84, (96,129,86): 85, (25,104,0): 86, (78,104,69): 87, (19,79,0): 88, (59,79,53): 89, (0,255,0): 90, (170,255,170): 91, (0,189,0): 92, (126,189,126): 93, (0,129,0): 94, (86,129,86): 95, (0,104,0): 96, (69,104,69): 97, (0,79,0): 98, (53,79,53): 99, (0,255,63): 100, (170,255,191): 101, (0,189,46): 102, (126,189,141): 103, (0,129,31): 104, (86,129,96): 105, (0,104,25): 106, (69,104,78): 107, (0,79,19): 108, (53,79,59): 109, (0,255,127): 110, (170,255,212): 111, (0,189,94): 112, (126,189,157): 113, (0,129,64): 114, (86,129,107): 115, (0,104,52): 116, (69,104,86): 117, (0,79,39): 118, (53,79,66): 119, (0,255,191): 120, (170,255,234): 121, (0,189,141): 122, (126,189,173): 123, (0,129,96): 124, (86,129,118): 125, (0,104,78): 126, (69,104,95): 127, (0,79,59): 128, (53,79,73): 129, (0,255,255): 130, (170,255,255): 131, (0,189,189): 132, (126,189,189): 133, (0,129,129): 134, (86,129,129): 135, (0,104,104): 136, (69,104,104): 137, (0,79,79): 138, (53,79,79): 139, (0,191,255): 140, (170,234,255): 141, (0,141,189): 142, (126,173,189): 143, (0,96,129): 144, (86,118,129): 145, (0,78,104): 146, (69,95,104): 147, (0,59,79): 148, (53,73,79): 149, (0,127,255): 150, (170,212,255): 151, (0,94,189): 152, (126,157,189): 153, (0,64,129): 154, (86,107,129): 155, (0,52,104): 156, (69,86,104): 157, (0,39,79): 158, (53,66,79): 159, (0,63,255): 160, (170,191,255): 161, (0,46,189): 162, (126,141,189): 163, (0,31,129): 164, (86,96,129): 165, (0,25,104): 166, (69,78,104): 167, (0,19,79): 168, (53,59,79): 169, (0,0,255): 170, (170,170,255): 171, (0,0,189): 172, (126,126,189): 173, (0,0,129): 174, (86,86,129): 175, (0,0,104): 176, (69,69,104): 177, (0,0,79): 178, (53,53,79): 179, (63,0,255): 180, (191,170,255): 181, (46,0,189): 182, (141,126,189): 183, (31,0,129): 184, (96,86,129): 185, (25,0,104): 186, (78,69,104): 187, (19,0,79): 188, (59,53,79): 189, (127,0,255): 190, (212,170,255): 191, (94,0,189): 192, (157,126,189): 193, (64,0,129): 194, (107,86,129): 195, (52,0,104): 196, (86,69,104): 197, (39,0,79): 198, (66,53,79): 199, (191,0,255): 200, (234,170,255): 201, (141,0,189): 202, (173,126,189): 203, (96,0,129): 204, (118,86,129): 205, (78,0,104): 206, (95,69,104): 207, (59,0,79): 208, (73,53,79): 209, (255,0,255): 210, (255,170,255): 211, (189,0,189): 212, (189,126,189): 213, (129,0,129): 214, (129,86,129): 215, (104,0,104): 216, (104,69,104): 217, (79,0,79): 218, (79,53,79): 219, (255,0,191): 220, (255,170,234): 221, (189,0,141): 222, (189,126,173): 223, (129,0,96): 224, (129,86,118): 225, (104,0,78): 226, (104,69,95): 227, (79,0,59): 228, (79,53,73): 229, (255,0,127): 230, (255,170,212): 231, (189,0,94): 232, (189,126,157): 233, (129,0,64): 234, (129,86,107): 235, (104,0,52): 236, (104,69,86): 237, (79,0,39): 238, (79,53,66): 239, (255,0,63): 240, (255,170,191): 241, (189,0,46): 242, (189,126,141): 243, (129,0,31): 244, (129,86,96): 245, (104,0,25): 246, (104,69,78): 247, (79,0,19): 248, (79,53,59): 249, (51,51,51): 250, (80,80,80): 251, (105,105,105): 252, (130,130,130): 253, (190,190,190): 254, (255,255,255): 255}
    listRGBsum=[0, 255, 510, 255, 510, 255, 510, 765, 195, 384, 255, 595, 189, 441, 129, 301, 104, 242, 79, 185, 318, 616, 235, 456, 160, 311, 129, 251, 98, 191, 382, 637, 283, 472, 193, 322, 156, 259, 118, 198, 446, 659, 330, 488, 225, 333, 182, 268, 138, 205, 510, 680, 378, 504, 258, 344, 208, 277, 158, 211, 446, 659, 330, 488, 225, 333, 182, 268, 138, 205, 382, 637, 283, 472, 193, 322, 156, 259, 118, 198, 318, 616, 235, 456, 160, 311, 129, 251, 98, 191, 255, 595, 189, 441, 129, 301, 104, 242, 79, 185, 318, 616, 235, 456, 160, 311, 129, 251, 98, 191, 382, 637, 283, 472, 193, 322, 156, 259, 118, 198, 446, 659, 330, 488, 225, 333, 182, 268, 138, 205, 510, 680, 378, 504, 258, 344, 208, 277, 158, 211, 446, 659, 330, 488, 225, 333, 182, 268, 138, 205, 382, 637, 283, 472, 193, 322, 156, 259, 118, 198, 318, 616, 235, 456, 160, 311, 129, 251, 98, 191, 255, 595, 189, 441, 129, 301, 104, 242, 79, 185, 318, 616, 235, 456, 160, 311, 129, 251, 98, 191, 382, 637, 283, 472, 193, 322, 156, 259, 118, 198, 446, 659, 330, 488, 225, 333, 182, 268, 138, 205, 510, 680, 378, 504, 258, 344, 208, 277, 158, 211, 446, 659, 330, 488, 225, 333, 182, 268, 138, 205, 382, 637, 283, 472, 193, 322, 156, 259, 118, 198, 318, 616, 235, 456, 160, 311, 129, 251, 98, 191, 153, 240, 315, 390, 570, 765]

    rawRGB=colorsys.hsv_to_rgb(theHSV[0]/360.0,theHSV[1],theHSV[2])
    theRGB=int(round(rawRGB[0]*255,0)),int(round(rawRGB[1]*255,0)),int(round(rawRGB[2]*255,0))

    theRGBsum=theRGB[0]+theRGB[1]+theRGB[2]
    theDictKeys=dictRGBtoACI.keys()
    if theRGB in theDictKeys:
        return dictRGBtoAIC[theRGB]
    else:
        listACIindexs=[]
        r1=theRGB[0]
        g1=theRGB[1]
        b1=theRGB[2]
        thePrevSum=1000
        theKey=''
        for aRGB in theDictKeys:
            r2=aRGB[0]
            g2=aRGB[1]
            b2=aRGB[2]
            deltaR = abs(r2-r1)
            deltaG = abs(g2-g1)
            deltaB = abs(b2-b1)
            deltaSum = deltaR+deltaG+deltaB
            if deltaSum<thePrevSum:
                thePrevSum=deltaSum
                theKey=aRGB
        
        return dictRGBtoACI[theKey]



