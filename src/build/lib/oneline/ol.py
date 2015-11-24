# -*- coding: utf-8 -*- 
import argparse 
import json
import bsonlib
import operator
import hashlib
import ast
import inspect
import array
import thread
import weakref
import string
import memcache
import socket
import datetime
import os
import re
import sys
import cherrypy
import requests
import uuid
import random as _random
import time as _time

try:
    import boto
except:
    pass

from dal import DAL, Field
from ws4py.server.cherrypyserver import WebSocketPlugin, WebSocketTool
from ws4py.websocket import WebSocket
from ws4py.messaging import TextMessage

DEFAULTS = dict(debug_mode=True, host='127.0.0.1', port=9000, path=os.path.abspath(os.path.join(os.path.dirname(__file__), 'static')))
SETTINGS = dict(table='', agent=[], nodes=[])
SERVERS = dict(host='server.socket_host', port='server.socket_port', path='tools.staticdir.root', ssl_key='server.ssl_private_key', ssl_certificate='server.ssl_certificate')
TABLE = ''
MODULES = []
_OL_SERVER = {}
_OL_CALLER = None
_OL_DB = []
_OL_DBS = []
_OL_TABLES = []

_OL_AGENT = {}
_OL_TABLE = '' ## the used table
_OL_CURRENT_APP = "" ## used by the cli
"""
shorthand for operator logic. Thanks to
Amnon from StackOverflow
"""
OPS = { 
        "<=": operator.le, 
        ">=": operator.ge,
        "<": operator.lt,
        ">": operator.gt,
        "==": operator.eq,
        "!=": operator.ne,
      } 
OBJS = [
            "geo",
            "event",
            "echo",
            "random",
            "sound",
            "time",
            "writer"
       ]
PCCS = {
        "py": "python",
        "php": "php",
        "pl": "perl",
        "rb": "ruby"
       }

"""
update this table
whenever an object is updated
and call within modules
"""
MOBJS = {}


def str_to_class(str):
    return getattr(sys.modules[__name__], str)

@cherrypy.expose
def proto(self):
    log_message("Handler created: " + repr(cherrypy.request.ws_handler))

##  parse the type from a mysql or postgresql
##  type column, VARCHAR(255) -> VARCHAR
##  BIGINT  -> BIGINT
##
def sub_field(field_type):
  import re
  matches = re.findall("(.*)\(",field_type)
  if matches:
    return matches[0]
  return field_type

def make_field(field_name,field_type):
  sub_match = sub_field(field_type).lower()
  if sub_match == "float":
    return Field(field_name, "double")
  elif sub_match in ['int','bigint','smallint','integer']:
    return Field(field_name, "integer")
  elif sub_match in ['date','datetime']:
    return Field(field_name, "date")
  elif sub_match in ['time']:
    return Field(field_name, "time")
  elif sub_match in ['double', 'decimal']:
    return Field(field_name, "double")
  elif sub_match in ['char', 'varchar', 'string']:
    return Field(field_name, "string")
  elif sub_match in ['mediumblob', 'blob']:
    return Field(field_name, "blob")
  return Field(field_name,"string")


"""
get the caller information
from within another method
'borrowed' from techto nick
"""
def caller_name(skip=2):
    """Get a name of a caller in the format module.class.method
       `skip` specifies how many levels of stack to skip while getting caller
       name. skip=1 means "who calls me", skip=2 "who calls my caller" etc.
       An empty string is returned if skipped levels exceed stack height
    """

    details =  {
        "module": "",
        "class": "",
        "function": ""  
    }
    stack = inspect.stack()
    start = 0 + skip
    if len(stack) < start + 1:
      return details
    parentframe = stack[start][0]    

    name = []
    module = inspect.getmodule(parentframe) # `modname` can be None when frame is executed directly in console
    # TODO(techtonik): consider using __main__
    if module:
        details['module'] = module.__name__
    # detect classname
    if 'self' in parentframe.f_locals:
        # I don't know any way to detect call from the object method
        # XXX: there seems to be no way to detect static method call - it will
        #      be just a function call
        details['class'] =  parentframe.f_locals['self'].__class__.__name__
    codename = parentframe.f_code.co_name
    if codename != '<module>':  # top level usually
        details['function']  = codename # function or a method del parentframe
    return details
    #return ".".join(name)

"""
scan the whole config aside from the
database settings.  """
def scan_config(caller):
    config = dict()
    #conf = False
    config_file = ""
    if not ".conf" in caller:
      config_file = caller + ".conf"
    else:
      config_file = caller

   
    if os.path.isfile("/usr/local/oneline/conf/"+config_file):

      keyword = "(.*)\s+?=\s+?'(.*)'"
      file = open("/usr/local/oneline/conf/"+ config_file).read()
      lines = file.split("\n")
      for i in lines:
        if not re.findall("^#", i):
          match = re.findall(keyword, i)
        
          if match:
            if match[0][0] == "microservice":
              if not "microservice" in config.keys():
                config['microservice']  = [match[0][1]]
              else:
                config['microservice'].append(match[0][1])
            else:
              config[match[0][0]] = match[0][1]
        
    return config


"""
start the streaming
process
"""
def stream(agent='', pline='', db='',objects=dict()):
    obj = inspect.currentframe().f_back.f_locals['self']
    config = caller_name()
    log_message("received information from module: as")
    log_message(caller_name().__str__())
    if db == '':
        config = caller_name()

        db = storage(caller=config['class']) 
    log_message("waiting for ready state")
    #ready()
    log_message("ONELINE is ready") 

    return pipeline(obj, db, config, scan_config(config['class']))


"""
      ol.query(db.table.id==1)
      query = ol.execute(single=True, last=True)
     
      print query.name 
     
      or 
      ol.query(db.table.name.like("Nadir"))
      ol.query(db.table.age=="23")
      ol.query(db.table.develops="PHP") 
      
      results = ol.execute(single=True,last=True,serialized=True)
      
      return json.dumps(results)
"""


 

def nextcheck(pieces, cnt, pred):
  list = []
  list.append(pieces[cnt]['expr'])
  cnt +=1
  while pieces[cnt]['op'] == pred:
    list.append(pieces[cnt]['expr'])
    cnt += 1
  return list

def execute(single=False,last=True, serialized=True):
  global _OL_DB
  global _OL_QUERY
  querypieces = []
  for i in range(0, len(_OL_QUERY)):
    piece = []
    pieces = nextcheck(_OL_QUERY,i,  i['op'])
    if i['op'] == "&":
      querypieces.append(reduce(lambda a,b: (a&b), pieces))
    else:
      querypieces.append(reduce(lambda a,b: (a|b), pieces))
      
   
  fullquery = reduce(lambda a,b: (a&b),querypieces)
        
  result =  _OL_DB(fullquery).select()
  if result:
    _OL_QUERY = []
  else:
    raise Exception("Could not execute query")

  if single:
    if last:
      result =  result.last()
    else:
      result = result.first()

  if serialized and not single:
    return result.as_list()
  if serialized:
    return result.as_dict()

  return result
 
def log_message(the_message):
  global DEFAULTS
  if DEFAULTS['debug_mode']:
    #using cherry py
    if isinstance(the_message,str):
      cherrypy.log(the_message)
    else:
      log_message(the_message.__str__())
    

class request(object):
  def __init__(self, requestCurrent=dict()):
    self.settings = []
    for i in requestCurrent.keys(): 
      self.set(i, requestCurrent[i])
    ## when we have a generic set the type of  result
    if self.get("generic"):
      generic = self.get("generic")
      self.set("type", generic['type'])
  ##backwards compat
  def __getitem__(self,key):
    return self.get(key)
  def set(self,thing,value):
    self.settings.append(thing)
    setattr(self,thing,value)
  def as_dict(self):
    asdict = dict()
    for i in range(0, len(self.settings)):
      attrOfI = getattr(self,self.settings[i]) 
      if isinstance(attrOfI, response):
        asdict[self.settings[i]] = attrOfI.as_dict()
      else:
        asdict[self.settings[i]] = attrOfI
    return unicodeAll(asdict)
  def get(self,key):
    if key in self.settings:
      return getattr(self,key)
    else:
      if 'packet' in self.settings:
        packet = getattr(self,'packet')
        if key in packet.keys():
          return packet[key]
    return None
    


class response(object):
  def __init__(self):
    self.settings = []
  def set(self,thing,value):
    self.settings.append(thing)
    setattr(self,thing,value)
  def as_dict(self):
    keys = dir(self)
    newDict = dict()
    for i in self.settings:
      newDict[i] =getattr(self,i)
    return unicodeAll(newDict)

def unicodeReplace(theString):
  ##do not reencode already unicode strings, this will create an
  ## error with errors="replace" mode
  if isinstance(theString,str) and not isinstance(theString, unicode):

    return unicode(theString, errors="replace")
  return theString

def unicodeAll(dictionaryorlist):
  if isinstance(dictionaryorlist,list):
    for i in range(0,len(dictionaryorlist)):
      if isinstance(dictionaryorlist[i],list):
        dictionaryorlist[i] = unicodeAll(dictionaryorlist[i])
      if isinstance(dictionaryorlist[i], dict):
        dictionaryorlist[i] = unicodeAll(dictionaryorlist[i])
      if isinstance(dictionaryorlist[i], str):
        dictionaryorlist[i] = unicodeReplace(dictionaryorlist[i])
      if isinstance(dictionaryorlist[i], int):
        dictionaryorlist[i] = int(dictionaryorlist[i])
      if isinstance(dictionaryorlist[i],long):
        dictionaryorlist[i]  = long(dictionaryorlist[i])
      if isinstance(dictionaryorlist[i], float):
        dictionaryorlist[i] = float(dictionaryorlist[i])
  if isinstance(dictionaryorlist,dict):
      keys = dictionaryorlist.keys()
      for i in keys:
        keyUnicode = unicodeReplace(i)
        if isinstance(dictionaryorlist[i], list):
          dictionaryorlist[keyUnicode] = unicodeAll(dictionaryorlist[i])
        if isinstance(dictionaryorlist[i], dict):
          dictionaryorlist[keyUnicode] = unicodeAll(dictionaryorlist[i])
        if isinstance(dictionaryorlist[i], str):
          dictionaryorlist[keyUnicode] = unicodeReplace(dictionaryorlist[i])
        if isinstance(dictionaryorlist[i], int):
          dictionaryorlist[keyUnicode] = int(dictionaryorlist[i])
        if isinstance(dictionaryorlist[i], long):
          dictionaryorlist[keyUnicode] = long(dictionaryorlist[i])
        if isinstance(dictionaryorlist[i], float):
          dictionaryorlist[keyUnicode] = float(dictionaryorlist[i])
  return dictionaryorlist
    

    



## deprecated in 0.7.5
def parse_message(message):
  if isinstance(message,str):
    literal = ast.literal_eval(message.__str__())
    return bsonlib.loads(bytearray(literal).__str__())
  return message

## opposite parse_message
## deprecated in 0.7.5
def pack_message(message):
  if isinstance(message, dict):
    if not 'order' in message.keys():
      message['order'] = []
    if not 'data' in message.keys():
      message['data'] = []

    bytes = map(ord, bsonlib.dumps(message)).__str__()
    return bytes
  return message

def parse(message,module=None):
  return parse_message(message) 

def pack(message, resp=None):
  return pack_message(message)


def  tables():
  global _OL_TABLES
  return _OL_TABLES

#def clean_db():
#  global _OL_DB
#  global _OL_TABLES
#  _OL_DB =None
#  _OL_TABLES = []

def controller_init(sql='',startserver=False, name=''):
  global _OL_CURRENT_APP 
  from oneline import olcli
  callername = caller_name()

  if callername['function']:
    caller = re.sub("_init$",  "", callername['function'])
    ##premature exit on False for sql. This would mean there is no SQL to commit
    ##(only) when no database is being used
    if isinstance(sql,bool) and sql ==  False:
      if startserver:
        olcli.Runtime(['olcli.py', 'start'])
        return True
        
    db = storage(conf=caller + ".conf", silent=True).get()['db']
    db.commit()
    
    contents =open(os.getcwd() + "/" + sql,'r+').read()
    ## bug the MySQL db api needs to 
    ## read each statement separtly to 
    ## do this we will
    ## commit each time
    ##  the cursor has been executed
    for i in contents.split(";"):  
      query = re.sub("\n", "", i)
      try: 
        print "Executing " + query
        result =db.executesql(query)
        db.commit()
      except:
        if not allwhitespace(query):
          print "Could not execute: " + query
    
  if startserver:
    return olcli.startserver()
  else:
    ## return true by default even if db
    ## fails
    ## the effort will be seen on screen
    return True

def allwhitespace(str):
  for i in range(0, len(str)):
      if not str[i] == " " or str[i] == "\n" or str[i] == "\r":
        return False
  return True
 


def controller_stop(stopserver=True):
  from oneline import olcli
  if stopserver: 
    cli.stopserver()

def controller_clean(cleansql=False):
  global _OL_CURRENT_APP
   
  caller= caller_name()
  
  if caller['function']:
    #caller = m[0]
    absolute =  re.sub("_clean","", caller['function'])
      
    db = storage(conf=absolute + ".conf")
    print "Cleaning tables for application: " + absolute
    realdb = db.get()['db'] 
    realdb.commit()
    if cleansql:
      try:
        realdb = db.get()['db']
        realdb.commit() 
        to_tables = tables()
        for i in to_tables:
          print "Attempting to clean: {0}".format(i)
          rows = realdb(getattr(realdb, i)).select() 
          for j in rows:
            row = realdb(getattr(getattr(realdb,i), 'id') == j.id).delete()
            realdb.commit()
      except Exception, e:
        print e.__str__() 
        raise Exception("Was not able to clean the database")
      return True

      
def controller_restart():
  from  oneline import olcli
  olcli.restartserver()
 

def ready():
  global _OL_DB
  global _OL_TABLES
  if _OL_DB:
    """
    count_of_tables_ready = 0
    for i in _OL_TABLES:
      if i in dir(_OL_DB):
        count_of_tables_ready += 1
    if count_of_tables_ready == len(_OL_TABLES) - 1:
      return True
    """
    return True
  return False
    
     

def db_by_module(module_name):
  stor= storage(conf=module_name + ".conf", silent=False)
  if stor:
    return stor.get()['db']
    


 
def db(caller_object):
  #global _OL_DB
  #return _OL_DB
  caller_object = caller_object.callerObject
  storage = cherrypy.engine.publish('get-database',caller_object.dbunique).pop()
  if  storage:
    return storage.get()['db']
   


def  signalStop(object):
  global _OL_DB
  object = object.callerObject
  clients = cherrypy.engine.publish('get-client', object.unique).pop()
  for i in range(0, len(clients)):
    if clients[i].unique == object.unique:
      log_message("removing client: " + clients[i].unique) 
      log_message("removing client that has db uniquie: " +clients[i].dbunique)
      #del clients[i]
  
      #log_message("removing client: " + clients[i].unique)
      #cherrypy.engine.publish('set-client', clients)
      cherrypy.engine.publish('close-database',  clients[i].dbunique)
      cherrypy.engine.publish('del-client',clients[i].dbunique)
      return True
  return False


""" 
parse the config
and provide a key value structure
"""
def config():
  conf =  caller_name() 
  return scan_config(conf['class'])

class _server(object):
    def __init__(self, host, port, ssl=False):
        self.host = host
        self.port = port
        self.scheme = 'ws' if not ssl else 'wss'
        self.propagated_modules = []

    """
    newly made objects need to run from
    the dispatcher
    """
    def _cp_dispatch(self, *args, **kw):
        vpath = '/' + kw['vpath'][0]
        _vpath = kw['vpath'][0]

        if vpath in cherrypy.config.keys():
            print "ONELINE: recognized a new module however needs to be gracefully restarted"
        else:
            print 'ONELINE: request module ' + _vpath + ' was not recognized'


    def index(self): 
        import pkg_resources
        version = pkg_resources.get_distribution("oneline").version
        return """
            <!DOCTYPE HTML>
                <html>
                      <head>
                          <title> Oneline HomePage</title>
                          </head>
                      <body>
                        <h2>Hello if you see this you have successfully setup oneline {0}</h2>
                      </body>
                    </html>
              """.format(version)


      
    def _make_new(self, name):
        setattr(self, name, proto_)

    def _object_handler(self):
        pass

    ##@cherrypy.expose
    ##def ws(self):
    ##      log_message("Handler created: %s" % repr(cherrypy.request.ws_handler))

"""
plugin for ws4py. defines
some basic methods to add, delete 
and get method
"""
class plugin(WebSocketPlugin):
    def __init__(self, bus):
        WebSocketPlugin.__init__(self, bus)
        self.clients = {}
        self.databases = {}
 
    def start(self):
        WebSocketPlugin.start(self)
        self.bus.subscribe('set-database',self.set_database)
        self.bus.subscribe('get-database',self.get_database)
        self.bus.subscribe('close-database',self.close_database)
        self.bus.subscribe('add-client', self.add_client)
        self.bus.subscribe('set-client', self.set_client)
        self.bus.subscribe('get-client', self.get_client)
        self.bus.subscribe('del-client', self.del_client)
 
    def stop(self):
        WebSocketPlugin.stop(self)
        self.bus.unsubscribe('set-database', self.set_database)
        self.bus.unsubscribe('get-database', self.get_database)
        self.bus.unsubscribe('close-database', self.close_database)
        self.bus.unsubscribe('add-client', self.add_client)
           
        self.bus.unsubscribe('set-client', self.del_client) 
        self.bus.unsubscribe('get-client', self.get_client)
        self.bus.unsubscribe('del-client', self.del_client)


    def close_database(self,name):
      thisDatabase = self.databases[name]
      if thisDatabase:
        theDatabase = thisDatabase.get()['db']
        theDatabase._adapter.close()
        #del self.databases[name]

    def set_database(self,name,dbobj):
      if not name in self.databases.keys():
        self.databases[name]  = dbobj

    def get_database(self,name):
      if name in self.databases.keys():
        theDatabase = self.databases[name]
        databaseConnection = self.databases[name].get()['db'] 
        #databaseConnection._adapter.reconnect()
        databaseConnection.commit()
        #theDatabase = self.databases[name]
        #$theDatabase.reconnect()
        #theDatabase.commit()
        #return self.databases[name]
        return theDatabase
 
    def add_client(self, name, websocket):
        if not name in self.clients.keys():
            self.clients[name] = [] 
        self.clients[name].append(websocket)

    def set_client(self, name, websockets):
        if not name in self.clients.keys():
          self.clients[name] = [] 
        self.clients[name]  =websockets
 
    def get_client(self, name):
        return self.clients[name]
 
    def del_client(self, unique):
        #clients = self.clients
        #for i in self.clients[unique
        for i in self.clients.keys():
          theseclients =  cherrypy.engine.publish('get-client', i).pop()
          for j in range(0, len(theseclients)):
  
            if theseclients[j].dbunique == unique:
               del theseclients[j]
        #del self.clients[unique]
        #for i in range(0, len(self.clients)):
        #  if self.clients[i].unique == unique:
        #    del self.clients[i]

class server(object):
    global SERVERS
    global MODULES
    global DEFAULTS
    global _OL_SERVER

    def __init__(self, 
             host=None,
             port=None,
             path=DEFAULTS['path']):

        """
        first obtain the 
        basic values found
        in the master config at: ../conf/Main.conf
        """

        curr = os.getcwd()
        config = scan_config("Main.conf")
        os.chdir(curr)

        if not host:
          self.host = config['ol_host'] if 'ol_host' in config.keys() else "127.0.0.1"
        else:
          self.host = host
        if  not port:
          self.port = int(config['ol_port']) if 'ol_port' in config.keys() else 9000
        else:
          self.port = int(port)
        self.path = path 
        self.ssl = False

        if 'use_ssl' in config.keys():
          if config['use_ssl']:
            if 'ssl_key' in config.keys() and 'ssl_certificate' in config.keys():
              print "Using SSL support with SSLKey: "  +config['ssl_key'] + ", SSLCertificate: " + config['ssl_certificate']
              self.ssl = True
              cherrypy.config.update({
                    SERVERS['host']: self.host,
                    SERVERS['port']: self.port,
                    SERVERS['path']: self.path
                    #SERVERS['ssl_key']: unicodeReplace(config['ssl_key']),
                    #SERVERS['ssl_certificate']: unicodeReplace(config['ssl_certificate'])
              })
              #cherrypy.server.ssl_module = 'builtin'
              cherrypy.server.ssl_private_key = unicodeReplace(config['ssl_key'])
              cherrypy.server.ssl_certificate = unicodeReplace(config['ssl_certificate'])
            else:
              log_message("If you want to use SSL and WSS please specifiy 'ssl_certificate' and 'ssl_key' in Main.conf")
              exit(1)
        else:
          cherrypy.config.update({SERVERS['host']: self.host,
                        SERVERS['port']: self.port,

                    SERVERS['path']: path}) 
        if os.path.exists('/usr/local/oneline/socket/'):
            piddir = '/usr/local/oneline/socket/'

        plugin(cherrypy.engine).subscribe()
        cherrypy.process.plugins.PIDFile(cherrypy.engine, piddir + 'oneline.pid.txt').subscribe()

        cherrypy.tools.websocket = WebSocketTool()

    def start(self):
        global _OL_SERVER
        global MODULES

        curr = os.getcwd()

        """ first try master directory """
        if os.path.exists('/usr/local/oneline/modules/'):
            os.chdir('/usr/local/oneline/modules')
            prefix = os.path.abspath('/usr/local/oneline/modules')
            files = os.listdir('/usr/local/oneline/modules')        
        

        config = dict()
        salt = ''
        sys.path.append(os.getcwd())

        for i in files:
            """
            ignore already compiled 
            """
    
            if not len(re.findall('\.py$', i)) > 0:
                continue
            if  len(re.findall('__init__',i)) >0:
                continue

            salt += '_' + i
           
            module = __import__(re.sub("\.py$", "", i), globals(), locals())
            module_name = module.__name__

            """
            open the file and determine its class
            """
            setattr(_server, module_name, proto)  
            if hasattr(module, module_name):
              classOfModule = getattr(module, module_name)

              config['/' + module_name] = { 'tools.websocket.on': True,
                                            'request.module_md5': hashlib.md5(module_name).hexdigest(),
                                            'request.module_ctime': os.path.getmtime(os.path.realpath("/usr/local/oneline/modules/" + i)),
                                            'request.module_object': module,
                                            'request.module_logger': logger(module_name),
                                            'request.module_uuid': uuid.uuid4().__str__(),
                                            'tools.websocket.handler_cls': classOfModule }


              MODULES.append(module_name)
              ## do storage to create the tables needed
              try:
                stor = storage(conf=module_name)
              except Exception,e: ##tables could not be  created
                print "Couldnt connect to database for module: "  +  module_name
                print  e
    
            else:
              continue ## no class found
      

        os.chdir(curr)

        print 'ONELINE CONFIG: ' 
        
        cherrypy.config.update({ 'request.modules_md5_snapshot': hashlib.md5(salt).hexdigest() })

        _OL_SERVER = _server(self.host, self.port, self.ssl)
        cherrypy.quickstart(_OL_SERVER, "/", config=config)  
        ## return a start by default
        ## if cherrypy errors it will on its
        ## own thread
        return 1


    def stop(self):
        pass

"""
start a storage object
with the provided
credentials. usually we should
look at the configuration for all this
information. This module
uses web2py's DAL to interface
with the database
"""
class storage(object):
    global _OL_DB 
    global _OL_TABLE
    global _OL_TABLES

    def __init__(self, 
                 db_type='mysql', 
                 table='', 
                 host='localhost', 
                 username='root', 
                 password='', 
                 database='', 
                 port='3306',
                 caller='',
                 conf='',
                 silent=False,
                 custom=False
                ):
        global _OL_DB
        global _OL_TABLE_REAL
        global _OL_TABLE
        import ol

        proto = False
        if conf == '':
            if caller:
              config_real_name =  caller
              config_name = config_real_name + ".conf"
              caller = caller_name()
            else:
              caller = caller_name()
              config_name =  caller['class'] + ".conf"
              config_real_name = caller['class']
              #raise Exception("Please provide a valid config")
        else:
            config_name = conf
            #proto = re.sub(".conf","",conf)
            config_real_name = re.sub(".conf","",conf)
            caller = caller_name()

        config = scan_config(config_name)
        print "ONELINE: scanning " +   config_real_name  + " config"
        self.join_table = False

        ## when a db type is not provided
        ## we should not use the storage object
        ## TODO:
        ## provide a mock function  
        #if not 'db_table' in config.keys():
        #  return None
            
        

        if not 'db_type' in config.keys() or not 'db_host' in config.keys():
          return None
        if proto:
          logger = cherrypy.config['/' + proto]['request.module_logger']
        else:
          logger = None

        db_type = config['db_type']
        username= config['db_user'] if 'db_user' in config.keys() else username
        password =config['db_pass'] if 'db_pass' in config.keys() else password
        port =config['db_port'] if 'db_port' in config.keys() else port
        #table = config['db_table']  if 'db_table' in config.keys() else table
        database =config['db_database']
        db_host =config['db_host']
        self.table =table = config['db_table']        
        if 'join_table' in config.keys():
          join_table =config['join_table']

        print "ONELINE: using table: " + table



        """
        do we already have a storage object for this?
        """

        if db_type == 'sqlite':
            _OL_DB = self.db = DAL('sqlite://' + database + '.db', migrate_enabled=False, folder=dbfolder, auto_import=True,pool_size=None)    
        else:   
            if silent:
              _OL_DB = self.db = DAL(db_type + '://' + username + ':' + password + '@' + db_host + ':' + port + '/' + database,pool_size=None)
            else:
              _OL_DB = self.db = DAL(db_type + '://' + username + ':' + password + '@' + db_host + ':' + port + '/' + database, migrate_enabled=False,pool_size=None)

        
        if silent:
          ## return our current
          ## instance
          ##
          return None
      
        

        """
        parse the tables
        """


        if db_type in ['mysql']:

            tables = self.db.executesql('SHOW TABLES; ')

            self.db.commit()
        elif db_type in ['sqlite']:
            tables = self.db.executesql('SELECT name FROM sqlite_master WHERE type = "table"') 
            self.db.commit()

        elif db_type in ['postgres']:

            tables = self.db.executesql("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE';")
            self.db.commit()

        for i in tables:
            table_name = i[0]

            args = []
            args.append(table_name)
            _OL_TABLES.append(table_name)
            if db_type in ['mysql']:
                schema = self.db.executesql('explain ' + i[0])
  
            elif db_type in ['sqlite']:
                schema = self.db.executesql('PRAGMA table_info({0});'.format(i[0]))
                
            elif db_type in ['postgres']:
                schema = self.db.executesql("select column_name, data_type, character_maximum_length from INFORMATION_SCHEMA.COLUMNS where table_name = '" + i[0] + "';")
            self.db.commit()
            """
            update when we don't find an id field try to find an primary_key or auto_increment 
            and use in place. if that doesn't work throw an error
            
            """
            has_id = False
            has_auto_increment = False
            for j in schema:
              if db_type in ['sqlite']:
                if j[1] == "id":
                  has_id = 1
              else:
                if j[0] == "id":
                  has_id = 1
            kw = dict() 
            for j in schema:
                """
                structure is as follows:
                {0 -> field_name, 1 -> type, 2 -> type, 3 ->, 4 -> default, 5 -> column auto increment}
                for sqlite:
                {0 -> int count, 1 -> field_name, 3 -> type }
                """
                if db_type in ['sqlite']:
                    if not has_id and (j[5] == "auto_increment" or j[3] == "PRI"):
                      args.append(Field(j[1], type='id'))
                      has_auto_increment = 1
                      kw['primarykey'] = [j[1]]
                    else:
                      args.append(Field(j[1]))
                else:
                    if not has_id and (j[5] == "auto_increment" or j[3] == "PRI"):
                      args.append(Field(j[0], type='id'))
                      kw['primarykey'] = [j[0]]
                      has_auto_increment = 1
                    else:
                      theField = make_field(j[0],j[2])
                      args.append(theField)

              

                if not has_id and not has_auto_increment:
                  ## warning here!
                  if logger:
                    logger.append(dict(
                      message="Could not find an auto increment key for %s. If you're using this table make sure it has one!" % (i[0]), 
                      object=self.__str__()))
                      
                if len(kw.keys()) > 0:
                  self.db.define_table(*args,**kw)
                else:
                  self.db.define_table(*args)

        _OL_TABLE = table
     
        _OL_DB = self.db
        log_message("registering the database and table under: " + _OL_DB.__str__() + ", " + _OL_TABLE.__str__())
        self.db.commit()

    def query(self, queries, **kwargs):
        self.db.commit()
        result = self.db(queries).select(**kwargs)
        self.db.commit()
        return  result

    def count(self,queries, **kwargs):
      self.db.commit()
      result = self.db(queries).count(**kwargs)
      self.db.commit()
      return result
    def insert(self, table, **kwargs):
      self.db.commit()
      newrow = getattr(self.db,table).insert(**kwargs)
      self.db.commit()
      return newrow


    """
    get a storage object    
    """
    def get(self):

        self.db.commit()
        return dict(db=self.db, table=self.table)

    """
    set something
    """
    def set(self, key, val):
        self[key] = val

"""
class modules defines
a base for internal modules
usage they should all import this class
to use module functionality
This should be a wrapper around ws4py's
Websocket
"""
class module(WebSocket):
    def opened(self):

        """  bind the basics """
        ##self.db = db(self) 
        if 'start' in dir(self):
          try:
            self.start()
            self.db =db(self.pipeline)
            self.query =self.pipeline.storage.query
            self.insert =self.pipeline.storage.insert
            self.count = self.pipeline.storage.count
          except Exception, e:
            print e.__str__()


    def closed(self, *args):
        try:
          signalStop(self.pipeline)
          if 'end' in dir(self):
              
              return self.end()
        except Exception, e:
          print e.__str__()

    def received_message(self, m):
        try:
          if 'receiver' in dir(self):
              if isinstance(m,TextMessage):
                m  =m.__str__()
              return self.receiver(request(parse(m)))
        except Exception, e:
          print e.__str__()
            

"""
agent definition
"""
class agent(object):
    def __init__(self, name='', option=''):
        pass

"""
a node in oneline is anything
that holds content and whos state
can change
"""
class node(object):
    def __init__(self, **kwargs):
        pass

    def __str__(self):
        pass

"""
"""
class nodecollection(object):
    def __init__(self):
        pass

"""
the pipeline object should
cluster ol objects and run them
with the needed functionality
pipeline functionality should follow:
foreach object in lineup
    run with objects
each object must keep the initial
properties intact
"""
class pipeline(object):
    global OBJS

    def __init__(self, callerObject, storage, caller, config):

        #cherrypy.engine.publish('set-database'

        self._objs = ''
        self.storage = storage
        self.callerObject = callerObject
        self.config = config
        self.blob = []
       
        if not 'broadcast' in self.config.keys() or self.config['broadcast'] == 'singular':
            self.callerObject.unique = uuid.uuid4().__str__()
            #self.callerObject.meunique = uuid
            self.callerObject.dbunique = uuid.uuid4().__str__()
      
        else:
            """ use the same unique id as the modules registered one """
            """ database unique should always be unique regardless """
            self.callerObject.unique = cherrypy.config['/' +caller['module']]['request.module_uuid'] 
            self.callerObject.dbunique= uuid.uuid4().__str__()
        """ uuid to identify this connection """

        if not 'freq' in self.config.keys():
            self.callerObject.freq = 0
        else:
            self.callerObject.freq = int(self.config['freq'])
        self.callerObject.config = self.config
        self.logger = cherrypy.config['/' + caller['module']]['request.module_logger']

        self.setup()

    def setup(self):
        client = cherrypy.engine.publish('add-client', self.callerObject.unique, self.callerObject)
        storage = cherrypy.engine.publish('set-database',self.callerObject.dbunique,self.storage)
        self.client = client


    """
    broadcast a message to all connections
    """
    def broadcast(self, message):
        if not isinstance(message, dict):
            message = dict(message=unicodeReplace(message))

        bytes = unicodeReplace(map(ord, bsonlib.dumps(message)).__str__())
        cherrypy.engine.publish('websocket-broadcast', bytes)

    """
    filter the data based on the confidence level and according
    to the limit.
    """
    def _filter(self, data):
        from operator import itemgetter

        return sorted(data, reverse=True, key=itemgetter('confidence')) 

    """
    add the packet to each message, this is usually done whenever
    a message has already been lined once.
    """
    def _append(self, d, p):
        return dict(data=d, packet=p) 

    """
    use the pipeline to decode
    the JSON message
    save all the default options to pass
    to each module.
    ** JSON switched to BSON
    If using JSON set interop option to 'json'
    TODO: recognize object based rules
    """
    def run(self, message):

        if not cherrypy.engine.state == cherrypy.engine.states.STARTED:
            return

        if isinstance(message, str):
          m = parse(message)
        else:
          if isinstance(message,request):        
            m = message.as_dict()
            message = pack(m)
          
        storage = cherrypy.engine.publish('get-database', self.callerObject.dbunique).pop()
        uuid =m['uuid'] if 'uuid'  in m.keys() else uuid.uuid4()
        timestamp = m['timestamp'] if 'timestamp'  in m.keys() else _time.time()
        connection_uuid   = m['connection_uuid']
        """
        check if we need to update the config
        """
        message = TextMessage(message.__str__())
        
        order = m['order']
        p = m['packet']

        if self._objs == '':
            if len(order) > 0:
              self._objs = []
              for i in order:
                if i in p and i in OBJS:
                  self._objs.append(globals()[i]())
            else:
              self._objs = [globals()[i]() for i in m['packet'] if i in OBJS]

        p = m['packet']
        if 'asyncs'  in m.keys():
          asyncs = m['asyncs']
        else:
          asyncs = []
        ## any existing data we need to copy
        ## this is for when the module appends
        ## data. we need to just return it to the client
        if 'response' in m.keys():
          r = m['response']
        else:
          r = dict()

        """
        if no limit is set
        set the limit to the default
        """
        if not 'limit' in dir(p):
            m['limit'] = 20
        else:
            m['limit'] = p['limit']

        c = 0
        i_m = m
        t = 0
        for i in self._objs:
            if not t == len(self._objs):
              try:
                i.storage = storage
                i.logger = self.logger
                log_message("Entering: ")
                #log_message(m.__str__())
                if c == 0:
                    m = i.run(m)
                else:
                    m = i.run(self._append(m, p)) 
                log_message("Leaving: ")
                #log_message(m.__str__())
                c += 1
                t += 1
              except Exception, e:
                i.log()
                print e
                ## main logging routine should be different from the modules, here we will collect the generic errors from python
                t += 1
                self.logger.append( dict(message=str(e)))
            else:
              break

        if len(self._objs)  > 0 and len(m) > 0:
        #do we have the confidence
          if not 'confidence' in m[0]:
            for i in range(0,len(m)):
              m[i]['confidence']  = 1
            #m  = [dict(i) + [dict(confidence=1)] i for i in m]

        """
        by now m should be a nodecollection.
        we must filter this to only the needed
        amount of node:ws
        """
        if isinstance(m, list):
            m = self._filter(m)

        """
        add any join table if set
        also look for id if available
        if it isnt use "table_name"_id for 
        match
        """
        if self.storage.join_table and isinstance(m, list):
            _OL_DB = self.storage.get()['db']
            _OL_TABLE = self.storage.get()['table']
            _OL_JOIN_TABLE = self.storage.join_table

            if _OL_JOIN_TABLE in getattr(_OL_DB, 'tables'):
                if self.storage.join_on:
                    _OL_JOIN_ON = self.storage.join_on
                else:
                    _OL_JOIN_ON = _OL_TABLE

                for i in range(0, len(m)):
                    queries = []
                    queries.append(getattr(getattr(_OL_DB, _OL_JOIN_TABLE), _OL_JOIN_ON) == m[i]['id'])
                    query = reduce(lambda a,b:(a&b),queries)
                    row = _OL_DB(query).select()

                    try:
                        row = row.as_list()[0]

                        for j in row.items():
                            """ prepend ambigious columns with join table name """

                            if j[0] in m[i].keys():
                                continue

                            m[i][j[0]] = j[1]

                    except:
                        pass

            else:
                self.logger.append(dict(message="Could not find join table", object=self.__str__()))

        """
        if results are met
        we need to run the
        provider. First get the client
        this message was received from
        """
      
        client = cherrypy.engine.publish('get-client', self.callerObject.unique).pop()
   
        #cherrypy.engine.log("Client is: %s" % client.__str__())
       
        if len(m) > 0 and len(self._objs) > 0:
            data = unicodeAll(m) 
            m = dict(data=m, good=True, asyncs=unicodeAll(asyncs),status=u'ok', response=unicodeAll(r), connection_uuid=unicodeReplace(connection_uuid), uuid=unicodeReplace(uuid), timestamp_request=int(timestamp), timestamp_response=_time.time())
        else:
            ## this could be a generic only request, as a result do not deem this an error      
            m = dict(data=[], good=True, asyncs=unicodeAll(asyncs), status=u'ok', response=unicodeAll(r), connection_uuid=unicodeReplace(connection_uuid), uuid=unicodeReplace(uuid), timestamp_request=int(timestamp), timestamp_response=_time.time())
       
        try:  
          delta_start = _time.time()
          bytes = map(ord, bsonlib.dumps(m)).__str__()
          delta_end = _time.time()
          print "Encoding took: " + str(delta_end - delta_start)  + " seconds"
        except Exception, e:
          print e.__str__()

        for i in client:
            ## trying to send to a dead client will not work
            try:
              i.send(bytes)   
              
      
            except:
              #self.logger.append(dict(addr='',object=self.__str__(), time=_time.time(), message="Lost a connection, message was not sent"))
              ## this should not happen when the module's stop function is called
              ## it will be implemented automatically in the newer release of oneline
              pass
              #cherrypy.engine.publish('del-client',i.dbunique)
     
        ## TODO 
        ## not correct way of calling a sleep function inside cherrypy use threaded version!
        #_time.sleep(self.callerObject.freq)

"""
oneline's logger
all logs should be stored
at: {base}/logs
README for more
"""
class logger(object):
    def __init__(self, module_name):
        curr = os.getcwd()

        if os.path.exists('/usr/local/oneline/logs/'):
            self.prefix = '/usr/local/oneline/logs/'

        today = datetime.datetime.today()
        datestamp = today.strftime('%d-%b-%Y')

        file_name = module_name + '_' + datestamp + '.log'

        if os.path.isfile(self.prefix + file_name):
            self.file_name = self.prefix  +file_name
        else:
            f = open(self.prefix  + file_name, 'w+')
            f.close()
            self.file_name = self.prefix  +file_name

        os.chdir(curr)


    def append(self, data):
        curr = os.getcwd()
        if os.path.exists('/usr/local/oneline/logs/'):
            self.prefix = '/usr/local/oneline/logs/'

        if not 'time' in data.keys():
            today = datetime.datetime.today()
            data['time'] = today.strftime('%m/%d/%y %I:%M:%S')

        if not 'addr' in data.keys():
            data['addr'] = '127.0.0.1'

        if not 'object' in data.keys():
            data['object'] = 'Main Pipeline Object'

        f = open(self.file_name, 'a+')

        line = "[" + data['time']  + ']' + ' - ' + data['addr'] + ' - ' + data['object'] + ' - ' + data['message'] + "\r\n"
        f.write(line)

        os.chdir(curr)


""" generic echo module take a db table output its contents """
class echo(object):
    def __init__(self):
        self.errors = []
    """ only one possible error: no table. """
    def log(self):
        name = self.__str__()

        for i in self.errors:
            self.logger.append(dict(object=name, message=i))

    def run(self, message):
        _OL_DB = self.storage.get()['db']
        _OL_TABLE = self.storage.get()['table']
        limit = message['packet']['echo']['limit']
        if len(message['data']) == 0:
            rows = _OL_DB(getattr(_OL_DB, _OL_TABLE)).select()
            return rows.as_list() 
        else:
            for k in range(0, len(message['data'])):
                message['data'][k]['confidence'] += 1

            return message['data']

"""
geolocation module:
all lookups in this 'must'
ensure that the table has 'lng' and 'lat'
properties.
"""
class geolocation(object):

    def __init__(self, every=5000):
        self.every = every
        self.range = 10
        self.limit = 100 
        self.last = 0
        self.errors = []

    def log(self):
        name = self.__str__()

        for i in self.errors:
            self.logger.append(dict(object=name, message=i))

    def run(self, message):
        lat = float(message['packet']['geo']['lat'])
        lng = float(message['packet']['geo']['lng'])
        range_ = float(message['packet']['geo']['range'])
        if 'limit' in message['packet']['geo'].keys():
          self.limit = int(message['packet']['geo']['limit'])

        
        _OL_DB = self.storage.get()['db']
        _OL_TABLE = self.storage.get()['table']

        """
        need to ensure the plus
        is always more
        and minus is always lower
        """
        lat_plus = float(lat) + float(range_)
        lng_plus = float(lng) + float(range_)
        """
        add a minus range
          
        make sure it matches
        a minus
        where -50 20 = -70
        """
        lat_minus = float(lat) + -(range_)
        lng_minus = float(lng) + -(range_)
    
        """
        set attributes to a double type
        if there not computations may result
        in error
        """ 

        if getattr(getattr(getattr(_OL_DB, _OL_TABLE), 'lat'), 'type') != 'double':
            setattr(getattr(getattr(_OL_DB, _OL_TABLE), 'lat'), 'type', 'double')

        if getattr(getattr(getattr(_OL_DB, _OL_TABLE), 'lng'), 'type') != 'double':
            setattr(getattr(getattr(_OL_DB, _OL_TABLE), 'lng'), 'type', 'double')
        """
        remember to add its confidence
        level to the packed 
        message, which is 1 to start
        """
        ## add limit based
        ## checkling usually
        ## we can get around
        ## with a decwnt
        ## size in using the geo 
        ## set however
        ## we need the best
        ## matches and subsequent
        ##
        ## objnects nmay need to use its results
        ## so a limit >= 1000 <= 5000 is good
        ## TODO:
        ## 
        ## seek to test
        ##

        if not 'lat' in getattr(_OL_DB, _OL_TABLE).fields:
            self.errors.append('This table does have a latitude column')
            raise NameError('ONELINE: This table does have a latitude column')

        if not 'lng' in getattr(_OL_DB, _OL_TABLE).fields:
            self.errors.append('This table does have a longitude column')
            raise NameError('ONELINE: This table does have a longitude column')

        if len(message['data']) == 0:
            q1 = []
            q2 = []
            q3 = []
            q4 = []
         

            ##  
            ##
            ## forward
            ##
            q1.append(getattr(getattr(_OL_DB, _OL_TABLE), "lat") >= lat) 
            q1.append(getattr(getattr(_OL_DB, _OL_TABLE), "lat") <= lat_plus) 
            q1.append(getattr(getattr(_OL_DB, _OL_TABLE), "lng") >= lng)
            q1.append(getattr(getattr(_OL_DB, _OL_TABLE), "lng") <= lng_plus)


            ## northeast
            ##
            q2.append(getattr(getattr(_OL_DB, _OL_TABLE), "lat") <= lat) 
            q2.append(getattr(getattr(_OL_DB, _OL_TABLE), "lat") >= lat_minus)
            q2.append(getattr(getattr(_OL_DB, _OL_TABLE), "lng") <= lng)
            q2.append(getattr(getattr(_OL_DB, _OL_TABLE), "lng") >= lng_minus)

            ##
            ##
            ##
            q3.append(getattr(getattr(_OL_DB, _OL_TABLE), "lat") >= lat) 
            q3.append(getattr(getattr(_OL_DB, _OL_TABLE), "lat") <= lat_plus)
            q3.append(getattr(getattr(_OL_DB, _OL_TABLE), "lng") <= lng)
            q3.append(getattr(getattr(_OL_DB, _OL_TABLE), "lng") >= lng_minus)

            q4.append(getattr(getattr(_OL_DB, _OL_TABLE), "lat") <= lat)
            q4.append(getattr(getattr(_OL_DB, _OL_TABLE), "lat") >= lat_minus)
            q4.append(getattr(getattr(_OL_DB, _OL_TABLE), "lng") >= lng)
            q4.append(getattr(getattr(_OL_DB, _OL_TABLE), "lng") <= lng_plus) 


            ## when lat is less than
            ## 0 we need to minus otherwise plus
            ## 
            ## lat <= -113 and lat >= -120
            ## or
            ##
              
             

            ## also needs the
            ## range spec
            queriesf = []
          
            q1f = reduce(lambda a,b:(a&b), q1)
            q2f = reduce(lambda a,b:(a&b), q2)
            q3f = reduce(lambda a,b:(a&b), q3)
            q4f = reduce(lambda a,b:(a&b), q4)
            queriesf.append(q1f)
            queriesf.append(q2f)
            queriesf.append(q3f)
            queriesf.append(q4f)
            finalQuery = reduce(lambda a,b:(a|b), queriesf)
            
            rows = _OL_DB(finalQuery).select(limitby=(0,self.limit))
            return rows.as_list()


        else:
            for k in range(0, len(message['data'])):
              """
              needs birectional checks
              """
              expr1 = bool((float(message['data'][k]['lat']) >= lat) and \
                    (float(message['data'][k]['lat']) <= lat_plus) and \
                    (float(message['data'][k]['lng']) >= lng) and \
                    (float(message['data'][k]['lng']) <= lng_plus)) 
              expr2 = bool((float(message['data'][k]['lat']) <= lat) and \
                      (float(message['data'][k]['lat']) >= lat_minus) and \
                      (float(message['data'][k]['lng']) <= lng) and \
                      (float(message['data'][k]['lng']) >= lng_minus))
              expr3 = bool((float(message['data'][k]['lat']) >= lat) and \
                      (float(message['data'][k]['lng']) <= lat_plus)
                      (float(message['data'][k]['lng']) <= lng) and \
                      (float(message['data'][k]['lng']) >= lng_minus))
              expr4 = bool((float(message['data'][k]['lat']) <= lat) and \
                      (float(message['data'][k]['lat']) >= lat_minus) and \
                      (float(message['data'][k]['lng']) >= lng) and \
                      (float(message['data'][k]['lng']) <= lng_plus))
              
              if expr1 or expr2 or expr3 or expr4:
                  if not 'confidence' in message['data'][k].keys():
                      message['data'][k]['confidence'] = 1
                  else:
                      message['data'][k]['confidence'] += 1
              else:
                      message['data'][k]['confidence'] = 0

            return message['data']                  




"""
sound object must satisfy the following
conditions:
1. All low level I/O is handled on the client end
2. One descriptor must be attached to the sound object
3. All queries must 'partially' match the full expression
"""
class sound(object):
    def __init__(self):
        self.errors = []

    def log(self):
        name = self.__str__()

        for i in self.errors:
            self.logger.append(dict(object=name, message=i))

    def run(self):
        _OL_DB = self.storage.get()['db']
        _OL_TABLE = self.storage.get()['table']

        descriptor = str(message['packet']['sound']['description'])
        field = str(message['packet']['sound']['field'])

        if len(message['data']) == 0:

            if not field in getattr(_OL_TABLE, 'fields'):
                self.errors.append('This table did not have a: ' + field + ' field')
                raise NameError('ONELINE: this table does not have a ' + field + ' field')

            """
            rows should be structured like
            [ {'id': 1, 'score': 19} ]
            """
            data = []
            olen = len(descriptor)
            step = float(1) / float(olen)

            for i in descriptor:
                queries = []

                queries.append(getattr(getattr(_OL_DB, _OL_TABLE), field).like('%' + i + '%'))

                query = reduce(lambda a,b:(a&b),queries)
                rows = _OL_DB(query).select()   

                """
                add its id to the rows list
                """
                for i in rows:
                    if not i.id in rows.keys():
                        data.append(dict(id=rows.id, score=1))
                    else:
                        for i in data:
                            if data[i]['id'] == i.id:
                                data[i]['score'] += step
                
            for i in data:
                pass
        else:
            if not field in message['data'].keys():
                self.errors.append('This table did not have a: ' + field + ' field')
                raise NameError('ONELINE: this table does not have a ' + field + ' field')

            for i in message['data']:
                confidence = 0
                olen = len(descriptor)
                step = float(1) / float(olen)

                for j in descriptor: 
                    if len(re.findall('.*' + j + '.*', message['data'][i][field])) > 0:
                        confidence += step

                if not 'confidence' in message['data'][i].keys():
                    message['data'][sel]['confidence'] = step
                else:
                    message['data'][sel]['confidence'] += step

            return message['data']

class random(object):
    def __init__(self):
        self.errors = []

    def log(self):
        name = self.__str__()

        for i in self.errors:
            self.logger.append(dict(object=name, message=i))

    def run(self, message):
        amount = int(message['packet']['random']['amount'])
        _OL_DB = self.storage.get()['db']
        _OL_TABLE = self.storage.get()['table']
        log_message("Entering random module with:")
        log_message(message.__str__())
        log_message("Database is: " + _OL_DB  +  ", " + _OL_TABLE)
        if len(message['data']) == 0:
            queries = []
            queries.append(getattr(_OL_DB, _OL_TABLE))

            query = reduce(lambda a,b:(a&b),queries)
            rows = _OL_DB(query).select(orderby='<random>', limitby=(0, amount))    

            log_message("Leaving random module with:")
            log_message( rows.as_list().__str__())
            return rows.as_list()
        else:
            found = len(message['data'])

            if found > 0:
              for i in range(0, amount):
                  sel = _random.randint(0, found - 1)

                  if not 'confidence' in message['data'][sel].keys():
                      message['data'][sel]['confidence'] = 1
                  else:
                      message['data'][sel]['confidence'] += 1

            log_message("Leaving random module with:")
            log_message(message['data'].__str__())
            return message['data']
            

class time(object):
    def __init__(self):
        self.errors = []

    def log(self):
        name = self.__str__()

        for i in self.errors:
            self.logger.append(dict(object=name, message=i))

    def run(self, message):
        start = int(message['packet']['time']['start'])
        end = int(message['packet']['time']['end'])
        if 'start_field'  in message['packet']['time'].keys():
          sfield =  message['packet']['time']['start_field']
        else:
          sfield =  "stime"
        if 'end_field' in message['packet']['time'].keys():
          efield = message['packet']['time']['efield'] 
        else:
          efield = "etime"
        _OL_DB = self.storage.get()['db']
        _OL_TABLE = self.storage.get()['table']

        if start > end:
            self.errors.append('Start time must be lower than end time ' + ' received (start: ' + start + ')')
            raise NameError('ONELINE: start time higher than end time in time')

        if len(message['data']) == 0:
            if not sfield in getattr(_OL_DB, _OL_TABLE).fields:
                self.errors.append('This table does have a stime column')
                raise NameError('ONELINE: This table does have a stime column')

            if not efield in getattr(_OL_DB, _OL_TABLE).fields:
                self.errors.append('This table does have a etime column')
                raise NameError('ONELINE: This table does have a etime column')

            if getattr(getattr(getattr(_OL_DB, _OL_TABLE), sfield), 'type') != 'integer':
                setattr(getattr(getattr(_OL_DB, _OL_TABLE), sfield), 'type', 'integer')

            if getattr(getattr(getattr(_OL_DB, _OL_TABLE), efield), 'type') != 'integer':
                setattr(getattr(getattr(_OL_DB, _OL_TABLE), efield), 'type', 'integer')

            queries = []

            queries.append(getattr(getattr(_OL_DB, _OL_TABLE), sfield) >= start)
            queries.append(getattr(getattr(_OL_DB, _OL_TABLE), efield) <= end)
            queries.append(getattr(getattr(_OL_DB, _OL_TABLE), sfield) <= \
                           getattr(getattr(_OL_DB, _OL_TABLE), efield))

            query = reduce(lambda a,b:(a&b),queries)
            rows = _OL_DB(query).select()

            return rows.as_list()
            
        else:
            for k in range(0, len(message['data'])):
                if int(message['data'][k][sfield]) >= start and \
                   int(message['data'][k][efield]) <= end and \
                   int(message['data'][k][sfield]) <= int(message['data'][k][efield]):
                    if not 'confidence' in message['data'][k].keys():
                        message['data'][k]['confidence'] = 1
                    else:
                        message['data'][k]['confidence'] += 1
                else:
                        message['data'][k]['confidence'] = 0

            return message['data']                  


""" db writing support ?"""
class writer(object):
    pass

"""
the event object should find any key value constraints that are 
in the packet's event object
"""
class event(object):
    global OPS 

    def __init__(self):
        self.errors = []
        self.limit = 12
        self.page = 0
        self.btype = "AND"

    def log(self):
        name = self.__str__()

        for i in self.errors:
            self.logger.append(dict(object=name, message=i)) 
    """
    dynamic queries implementation 'borrowed' from
    http://thadeusb.com/weblog/2010/1/3/web2py_dynamic_queries
    """
    def run(self, message):
        opts = []
        queries = []

        _OL_DB = self.storage.get()['db']
        _OL_TABLE = self.storage.get()['table']

        self.btype = "AND"
        if 'limit' in message['packet']['event'].keys():
          self.limit = int(message['packet']['event']['limit'])
        page = 0

        log_message("entering: event module with:")
        log_message(message.__str__())
        delta_start = _time.time()
        reserved = ['limit', 'page', 'type']

        for k,v in message['packet']['event'].iteritems():
            if not k in reserved:
              if not k in getattr(_OL_DB, _OL_TABLE).fields:
                  self.errors.append('This table does not have: ' + k + ' field in: ' + _OL_TABLE + ' table')

            ## reserveed keyword type
            ## needs to specify what operand we're going for
            if k == "type":
              self.btype = v
              continue
            if k == "limit":
              self.limit = int(v)
              continue
            if k == "page":
              self.page = int(v)
              continue
         

            if type(v) is list:
                for i in v:
                    opts.append(dict(key=k, value=i['value'], op=i['op']))
            else:
                opts.append(dict(key=k, value=v['value'], op=v['op']))

        if not len(message['data'])>0:

            for i in opts:

                op = i['op']


                if op == '==':
                    queries.append(getattr(getattr(_OL_DB, _OL_TABLE), i['key']) == i['value'])
                elif op == '>':
                    queries.append(getattr(getattr(_OL_DB, _OL_TABLE), i['key']) > i['value'])
                elif op == '<':
                    queries.append(getattr(getattr(_OL_DB, _OL_TABLE), i['key']) < i['value'])
                elif op == '>=':
                    queries.append(getattr(getattr(_OL_DB, _OL_TABLE), i['key']) >= i['value'])
                elif op == '<=':
                    queries.append(getattr(getattr(_OL_DB, _OL_TABLE), i['key']) <= i['value'])
                elif op == '!=':
                    queries.append(getattr(getattr(_OL_DB, _OL_TABLE), i['key']) != i['value'])
                elif op == 'like':
                    queries.append(getattr(getattr(_OL_DB, _OL_TABLE), i['key']).like('%' + i['value'] + '%'))
                else: 
                    queries.append(getattr(getattr(_OL_DB, _OL_TABLE), i['key']) == i['value'])

            if self.btype == 'AND':
              query = reduce(lambda a,b:(a&b),queries)
            else: 
              query = reduce(lambda a,b:(a|b),queries)
        
            if self.limit != 12:
              if page != 0:
                rows = _OL_DB(query).select(limitby=(0, page + self.limit))
              else: 
                rows = _OL_DB(query).select(limitby=(0, self.limit))
            else:
              rows = _OL_DB(query).select(limitby=(0, self.limit))

            delta_end  =_time.time()
            log_message("Request took " + str(delta_end - delta_start) + " seconds")
            return rows.as_list()

        else:

            if  len(message['data']) > 0:
              for k in range(0, len(message['data']) -1):

                  """
                  whenever a match is met
                  increase by the step which
                  is 1 divided by the number of options
                  """
                  olen = len(opts)
                  step = float(1) / float(olen)

                  if not 'confidence' in message['data'][k].keys():
                          message['data'][k]['confidence'] = 1

                  for i in opts:
                      op = i['op']

                      if op == 'like':
                          if len(re.findall('.*' + i['value'] + '.*', message['data'][k][i['key']])) > 0:
                              message['data'][k]['confidence'] += step
                      else:
                          if OPS[op](message['data'][k][i['key']], i['value']):
                              message['data'][k]['confidence'] += step

            return message['data']  

globals()['geo'] = globals()['geolocation']
