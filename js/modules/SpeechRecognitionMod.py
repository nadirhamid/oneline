#! /usr/bin/python

##############################################################################
# A practical test module for oneline
# it is not intended to ran as a test and
# should serve as an actual module
##############################################################################

from oneline import ol
"""
Test a table with join support. This will basically
ask for two tables when found, stream data from both

Join table setup can be found in ./conf/JoinTable.conf
under two fields:
db_join_table
and
db_join_on
"""

class SpeechRecognitionMod(ol.module):
    def start(self):
        """ starting join table module """
    	self.pipeline = ol.stream()

        print "connected: " + self.unique
    	
    def receiver(self, message):
    	self.pipeline.run(message)

    def provider(self, message):
        pass
 
    def end(self):
    	print "i am closing a connection and cleaning up your leftover data"

        del self.pipeline