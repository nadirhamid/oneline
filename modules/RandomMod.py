#! /usr/bin/python

##############################################################################
# A practical test module for oneline
# it is not intended to ran as a test and
# should serve as an actual module
##############################################################################

from oneline import ol

class RandomMod(ol.module):
    def start(self):
    	time = ol.time()
    	random = ol.random()
    	self.pipeline = ol.stream(pline=[time,random])
    	
    def receiver(self, message):
    	self.pipeline.run(message)