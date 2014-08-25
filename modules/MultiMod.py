#! /usr/bin/python

##############################################################################
# A practical test module for oneline
# it is not intended to ran as a test and
# should serve as an actual module
##############################################################################

from oneline import ol
import GeoMod

class MultiMod(ol.module):
    def start(self):
    	db = ol.storage()
    	geo = ol.geo()
    	ev = ol.event()
        print "Changing the order of geo and ev "

        self.pipeline = ol.stream(pline=[ev, geo], db=db)

    def receiver(self, message):
        self.pipeline.run(message) 

    def upstream(self, message):
        geo = GeoMod()

        geo.open()

    def provider(self, message):
    	self.pipeline.run(message)

    def end(self):
        print "closing multimod :("
        del self.pipeline