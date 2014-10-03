#! /usr/bin/python

##############################################################################
# A practical test module for oneline
# it is not intended to ran as a test and
# should serve as an actual module
##############################################################################

from oneline import ol
"""
A module that is event based and only
called on a browser event. Everything for
the weblet should remain the same..
"""

class EventBasedMod(ol.module):
    def start(self):
        """ starting EventBasedMod """
        print "EventBasedMod starting.. "
        
    	self.pipeline = ol.stream()

        print "connected: " + self.unique
    	
    def receiver(self, message):
        print "A browser event occured.. "
    	self.pipeline.run(message)

    def provider(self, message):
        pass
 
    def end(self):
    	print "i am closing a connection and cleaning up your leftover data"

        del self.pipeline