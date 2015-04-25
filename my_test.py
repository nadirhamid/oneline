

##############################################################################
# Factory created module. Edit 
# as you like 
# @author Your Name
# @package Example Module
# @does Shows an example
##############################################################################

from oneline import ol

class my_test(ol.module):
    def start(self):
        self.pipeline = ol.stream()
    
    def receiver(self, message):
        self.pipeline.run(message)
