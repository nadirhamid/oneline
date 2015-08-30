from oneline import ol

## for  example controller 
## writings please use oneline --init "my_module_name"
##
def Example_module_init(startserver=True  ):
  return ol.controller_init(startserver=startserver,sql='Example_module.sql')

def Example_module_clean(cleansql=True):
  return ol.controller_clean(cleansql=cleansql)
 
def Example_module_stop(stopserver=True):
  return ol.controller_stop(stopserver=stopserver)

def Example_module_restart():
  return ol.controller_restart()
