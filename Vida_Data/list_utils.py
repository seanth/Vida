"""This file is part of Vida.
    --------------------------
    Copyright 2022, Sean T. Hammond
    
    Vida is experimental in nature and is made available as a research courtesy "AS IS," but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 
    
    You should have received a copy of academic software agreement along with Vida. If not, see <https://github.com/seanth/Vida/blob/master/LICENSE.txt>.
"""

def sort_by_attr(seq, attr):
    intermed=[(getattr(x, attr),i, x) for i, x in enumerate(seq)]
    intermed.sort()
    return [x[-1]for x in intermed]

def sort_by_attr_inplace(lst, attr):
    lst[:]=sort_by_attr(lst,attr)

def remove_duplicates(theList):
    return list(set(theList))