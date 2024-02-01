"""This file is part of Vida.
--------------------------
Copyright 2009, Sean T. Hammond

Vida is experimental in nature and is made available as a research courtesy "AS IS," but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 

You should have received a copy of academic software agreement along with Vida. If not, see <http://iorek.ice-nine.org/seant/Vida/license.txt>.
"""

#This file can be used to convert an image into a placement file for use with vida.py
from PIL import Image

input_file = "TreePattern.jpg"
output_file = "TreePattern.csv"

im = Image.open(input_file)
out = open(output_file,'w')
width, height = im.size
for x in xrange(width):
	for y in xrange(height):
		if im.getpixel((x,y))<=50:
			#print >> out, "%s, %s, %s" % (x-(width/2.0),y-(height/2.0),im.getpixel((x,y)))
			print >> out, "random, %f, %f, 0" % (x-(width/2.0),y-(height/2.0))
out.close()