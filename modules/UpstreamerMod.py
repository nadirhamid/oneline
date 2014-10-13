#! /usr/bin/python

##############################################################################
# A practical test module for oneline
# it is not intended to ran as a test and
# should serve as an actual module
##############################################################################

from oneline import ol
"""
A module that will transmit
data onto other servers. These
servers should be running the same
module in 'downstream' mode.
"""

class UpstreamerMod(ol.module):
    def start(self):
        """ starting EventBasedMod """
        print "Upstreamer Mod starting.. "
        
    	self.pipeline = ol.stream()

        print "connected: " + self.unique
    	
    def receiver(self, message):
        print "Dispatching request onto: "
        print self.config['cluster']
    	self.pipeline.run(message)

    def provider(self, message):
        pass
 
    def end(self):
    	print "i am closing a connection and cleaning up your leftover data"

        del self.pipeline