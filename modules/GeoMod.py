from oneline import ol

class GeoMod(ol.module):
  def start(self):
    self.pipeline = ol.stream()
  def receiver(self,message):
    return self.pipeline.run(message)
  def stop(self):
    pass
