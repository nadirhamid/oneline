
## example controller, controls your app           
import ol
def my_oneline_init(sql='my.sql', runserver=True):
  return ol.Controller.start(sql='my.sql', runserver=True)
def my_oneline_stop(stopserver=True):
  return ol.Controller.stop(stopserver=True)
def my_oneline_clean(cleansql=True)
  return ol.Controller.clean(cleansql=True)
def my_oneline_restart(restartserver=True)
  return ol.Controller.restart(restartserver=True)

ol.init = my_oneline_init
ol.stop = my_oneline_stop
ol.clean = my_oneline_clean
ol.restart = my_oneline_restart
                