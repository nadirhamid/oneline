#! /usr/bin/python

##############################################################################
# A practical test module for oneline
# it is not intended to ran as a test and
# should serve as an actual module
##############################################################################

from oneline import ol

class BurgerMod(ol.module):
    def start(self):

    	
    	self.pipeline = ol.stream()
    	
    def receiver(self, message):
    	self.pipeline.run(message)

    def provider(self, message):
    	pass
 
    def end(self):
    	print "bye bye"