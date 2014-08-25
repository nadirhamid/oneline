#! /usr/bin/python

##############################################################################
# A practical test module for oneline
# it is not intended to ran as a test and
# should serve as an actual module
##############################################################################

from oneline import ol

class MultiMod(ol.module):
    def start(self):
    	db = ol.storage()
    	geo = ol.geo()
    	ev = ol.event()

        self.pipeline = ol.stream(pline=[geo, ev], db=db)

    def receiver(self, message):
        self.pipeline.run(message) 

    def provider(self, message):
    	self.pipeline.run(message)