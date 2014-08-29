#! /usr/bin/python

##############################################################################
# A practical test module for oneline
# it is not intended to ran as a test and
# should serve as an actual module
##############################################################################

from oneline import ol

class BurgerMod(ol.module):
    def start(self):
        print "i am opening a connection!"
    	self.pipeline = ol.stream()
    	
    def receiver(self, message):
        print "Hello" + self.unique
    	self.pipeline.run(message)

    def provider(self, message):
        print " am providing data to: " + self.unique
 
    def end(self):
    	print "i am closing a connection and cleaning up your leftover data"

        del self.pipeline