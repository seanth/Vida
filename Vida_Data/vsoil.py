"""This file is part of Vida.
    --------------------------
    Copyright 2026, Sean T. Hammond

    Vida is experimental in nature and is made available as a research courtesy "AS IS," but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

    You should have received a copy of academic software agreement along with Vida. If not, see <https://github.com/seanth/Vida/blob/master/LICENSE.txt>.
"""

###The soil: every plant and seed in the world, in the order they were
###planted (theGarden.soil).
###
###It is a Python list, and Vida goes through it, counts it, copies it and
###looks things up by place in it just as before. The one difference is that
###it also keeps track of where each thing is, so these are quick however big
###the world gets:
###    thing in soil
###    soil.index(thing)
###    soil.remove(thing)
###    del soil[place]
###In a plain list the first three look through the list from the start. In
###a big world, with thousands of things in the soil and thousands dying each
###cycle, kill() doing that was the slowest part of Vida.
###
###How it keeps track: each thing gets a number when it goes into the soil
###(1, 2, 3...), so the numbers are in the same order as the list. A thing's
###place in the list is then how many of the things still in the soil have a
###number up to its own, minus one. Those counts are kept in a Fenwick tree
###(also called a binary indexed tree): a list of partial counts that can
###give "how many up to here", and be updated when a thing is added or
###removed, in about 15 steps for 30,000 things, rather than one step per
###thing.
###
###Anything that rearranges the list (insert, sort, reverse, putting a new
###thing in a place) still works; afterwards everything is simply numbered
###again from the start. If the same thing is ever put into the soil twice,
###the soil goes back to searching like a plain list, which handles that.


class Soil(list):

    def __init__(self, things=()):
        list.__init__(self, things)
        self.numberAgain()

    def __reduce__(self):
        ###saving (pickling) a soil saves just the things in it; the numbers
        ###are worked out again when it's loaded
        return (Soil, (list(self),))

    ###-----------------------------------------------------------------
    ###Keeping track of where things are
    ###-----------------------------------------------------------------

    def numberAgain(self):
        ###number everything in the soil 1, 2, 3... in list order, with room
        ###for as many again to be added before this is needed again
        self.numberOf = {}
        self.plainList = False
        size = list.__len__(self)
        place = 0
        for thing in list.__iter__(self):
            place = place + 1
            try:
                if thing in self.numberOf:
                    ###the same thing twice: search like a plain list from now on
                    self.plainList = True
                self.numberOf[thing] = place
            except TypeError:
                ###something that can't be looked up this way (a list, say)
                self.plainList = True
        self.capacity = 2 * size + 64
        self.nextNumber = size + 1
        ###the Fenwick tree: counts[n] is how many things are still in the
        ###soil with numbers from n - lowestBit(n) + 1 up to n, where
        ###lowestBit(n) is n & -n. To start with every number up to size is in
        ###the soil; each count is passed up to the one above it that covers
        ###it too.
        self.counts = [0] * (self.capacity + 1)
        for number in range(1, self.capacity + 1):
            if number <= size:
                self.counts[number] = self.counts[number] + 1
            above = number + (number & -number)
            if above <= self.capacity:
                self.counts[above] = self.counts[above] + self.counts[number]

    def countUpTo(self, number):
        ###how many things still in the soil have a number up to this one
        total = 0
        while number > 0:
            total = total + self.counts[number]
            number = number - (number & -number)
        return total

    def changeCount(self, number, change):
        ###a thing with this number has come into (+1) or left (-1) the soil
        while number <= self.capacity:
            self.counts[number] = self.counts[number] + change
            number = number + (number & -number)

    def numberFor(self, thing):
        ###the thing's number, or None if it isn't in the soil
        try:
            return self.numberOf.get(thing)
        except TypeError:
            ###something that can't be looked up this way (a list, say) is
            ###never in the soil
            return None

    ###-----------------------------------------------------------------
    ###Adding, finding and removing
    ###-----------------------------------------------------------------

    def append(self, thing):
        if self.numberFor(thing) is not None:
            self.plainList = True
        list.append(self, thing)
        if self.nextNumber > self.capacity:
            self.numberAgain()
            return
        try:
            self.numberOf[thing] = self.nextNumber
        except TypeError:
            self.plainList = True
        self.changeCount(self.nextNumber, 1)
        self.nextNumber = self.nextNumber + 1

    def __contains__(self, thing):
        if self.plainList:
            return list.__contains__(self, thing)
        return self.numberFor(thing) is not None

    def index(self, thing, *startAndStop):
        if self.plainList or startAndStop:
            return list.index(self, thing, *startAndStop)
        number = self.numberFor(thing)
        if number is None:
            raise ValueError("%r is not in the soil" % (thing,))
        return self.countUpTo(number) - 1

    def __delitem__(self, place):
        if isinstance(place, slice):
            list.__delitem__(self, place)
            self.numberAgain()
            return
        thing = list.__getitem__(self, place)
        list.__delitem__(self, place)
        if self.plainList:
            self.numberAgain()
            return
        number = self.numberOf.pop(thing)
        self.changeCount(number, -1)

    def remove(self, thing):
        del self[self.index(thing)]

    def pop(self, place=-1):
        thing = list.__getitem__(self, place)
        del self[place]
        return thing

    ###-----------------------------------------------------------------
    ###Anything that rearranges the list: do it, then number again
    ###-----------------------------------------------------------------

    def insert(self, place, thing):
        list.insert(self, place, thing)
        self.numberAgain()

    def extend(self, things):
        list.extend(self, things)
        self.numberAgain()

    def __iadd__(self, things):
        list.__iadd__(self, things)
        self.numberAgain()
        return self

    def __imul__(self, times):
        list.__imul__(self, times)
        self.numberAgain()
        return self

    def __setitem__(self, place, thing):
        list.__setitem__(self, place, thing)
        self.numberAgain()

    def sort(self, *args, **kwargs):
        list.sort(self, *args, **kwargs)
        self.numberAgain()

    def reverse(self):
        list.reverse(self)
        self.numberAgain()

    def clear(self):
        list.clear(self)
        self.numberAgain()
