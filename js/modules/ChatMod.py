#! /usr/bin/python

##############################################################################
# A practical test module for oneline
# it is not intended to ran as a test and
# should serve as an actual module
##############################################################################

from oneline import ol

class ChatMod(ol.module):
    def start(self):
        """ starting chat module """
    	self.pipeline = ol.stream()

        print "connected: " + self.unique
    	
    def receiver(self, message):
    	self.pipeline.run(message)

    def provider(self, message):
        pass
 
    def end(self):
    	print "i am closing a connection and cleaning up your leftover data"

        del self.pipeline