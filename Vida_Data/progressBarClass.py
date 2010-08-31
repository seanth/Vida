# CLASS NAME: DLLInterface
#
# Author: Larry Bates (lbates@syscononline.com)
#
# Written: 12/09/2002
#
# Released under: GNU GENERAL PUBLIC LICENSE
#
#Minor changes by Sean T. Hammond 2008.03.12
class progressbarClass: 
    def __init__(self, finalcount, progresschar=None):
        import sys
        self.finalcount=finalcount
        self.blockcount=0
        #
        # See if caller passed me a character to use on the
        # progress bar (like "*").  If not use the block
        # character that makes it look like a real progress
        # bar.
        #
        if not progresschar: 
		self.block=chr(178)
        else:                
		self.block=progresschar
        # Get pointer to sys.stdout so I can use the write/flush
        # methods to display the progress bar.
        self.f=sys.stdout
        # If the final count is zero, don't start the progress gauge
        if not self.finalcount : 
		return
        self.f.write('[----------------- % Progress ---------------------]\n')
	self.f.write('[')
        #self.f.write('    10   20   30   40   50   60   70   80   90   100\n')
        #self.f.write('----|----|----|----|----|----|----|----|----|----|\n')
        return

    def update(self, count):
        # Make sure I don't try to go off the end (e.g. >100%)
        count=min(count, self.finalcount)
        # If finalcount is zero, I'm done
        if self.finalcount:
            percentcomplete=int(round(100*count/self.finalcount))
            if percentcomplete < 1:
		percentcomplete=1 
        else:
            percentcomplete=100
        blockcount=int(percentcomplete/2)
        if blockcount > self.blockcount:
            for i in range(self.blockcount,blockcount):
                self.f.write(self.block)
                self.f.flush()
                
        if percentcomplete == 100:
		self.f.write("]\n\n")
        self.blockcount=blockcount
        return

#this is so you can test it alone    
if __name__ == "__main__":
    maxValue=25000
    pb=progressbarClass(maxValue,"*")
    count=0
    while count< maxValue:
        count+=1
        pb.progress(count)
