from oneline import ol
class Example_module(ol.module):
  def start(self):
    self.pipeline = ol.stream()
  def receiver(self,message):
    self.pipeline.run(message)
  def stop(self):
    return None
