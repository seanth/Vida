"""This file is part of Vida.
--------------------------
Copyright 2009, Sean T. Hammond

Vida is experimental in nature and is made available as a research courtesy "AS IS," but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 

You should have received a copy of academic software agreement along with Vida. If not, see <http://iorek.ice-nine.org/seant/Vida/license.txt>.
"""

#import operator#python 2.4 only
def sort_by_attr(seq, attr):
	#python 2.3
	intermed=[(getattr(x, attr),i, x) for i, x in enumerate(seq)]
	intermed.sort()
	return [x[-1]for x in intermed]
	#python 2.4
	#return sorted(seq, key=operator.attrgetter(attr))

def sort_by_attr_inplace(lst, attr):
	#python 2.3
	lst[:]=sort_by_attr(lst,attr)
	#python 2.4
	#lst.sort(key=operator.attrgetter(attr))