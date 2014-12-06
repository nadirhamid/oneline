#! /usr/bin/python

##############################################################################
# A practical test module for oneline
# it is not intended to ran as a test and
# should serve as an actual module
##############################################################################

from oneline import ol

class GeoTimeMod(ol.module):
    def start(self):
    	geo = ol.geo()
    	time = ol.time()

    	self.pipeline = ol.stream(pline=[time, geo])
    	
    def receiver(self, message):
    	self.pipeline.run(message)

    def provider(self, message):
    	pass

    def end(self):
    	print "closed GeoTimeMod"