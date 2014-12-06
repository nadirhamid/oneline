#! /usr/bin/python

##############################################################################
# A practical test module for oneline
# it is not intended to ran as a test and
# should serve as an actual module
##############################################################################

"""
Stream Module will take the output
from oneline and compose with another
scripting language's input. In other words

{ScriptingLanguage} [input]
"""

from oneline import ol

class StreamMod(ol.module):
    def start(self):
	print "Starting Stream Module using language: PHP"
    	self.pipeline = ol.stream()
    	
    def receiver(self, message):
    	self.pipeline.run(message)

    def end(self):
	print "Ending Stream module"
