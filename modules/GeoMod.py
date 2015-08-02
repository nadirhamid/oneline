from oneline.core.module import OnelineModule

class GeoMod(OnelineModule):
  def start(self):
    pass
  def receiver(self,message):
    return self.pipeline.run(message)
  def stop(self):
    pass
