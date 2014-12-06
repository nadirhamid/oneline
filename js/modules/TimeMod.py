#! /usr/bin/python

##############################################################################
# A practical test module for oneline
# it is not intended to ran as a test and
# should serve as an actual module
##############################################################################

from oneline import ol

class TimeMod(ol.module):
    def start(self):
        """ starting chat module """
    	self.pipeline = ol.stream()
        print "Running module: " + self.__str__()

    def receiver(self, message):
    	self.pipeline.run(message)

    def provider(self, message):
        self.pipeline.broadcast('testing. reporting from:' + self.__str__()) 

    def end(self):
        print "Closing module: " + self.__str__()