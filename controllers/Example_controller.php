from oneline import ol

def Example_init(runsql=True)
  print "Hello, this constructs my database, and starts the Oneline server"
  print "Please not the sql file shound be under this directory, under Example.sql"
  return oneline_init(runsql=True,startserver=True) 

def Example_clean(cleansql=True): 
  print "This cleans the database"
  return oneline_clean(cleansql=True)
 

