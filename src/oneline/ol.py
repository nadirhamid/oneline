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
     
            rows = _OL_DB(finalQuery).select(limitby=(0,12))
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
          sfield =  sfield
        if 'end_field' in message['packet']['time'].keys():
          efield = message['packet']['time']['efield'] 
        else:
          efield = efield
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

        btype = "AND"
        limit = 12 
        page = 0

        log_message("entering: event module with:")
        log_message(message.__str__())
        reserved = ['limit', 'page', 'type']

        for k,v in message['packet']['event'].iteritems():
            if not k in reserved:
              if not k in getattr(_OL_DB, _OL_TABLE).fields:
                  self.errors.append('This table does not have: ' + k + ' field in: ' + _OL_TABLE + ' table')

            ## reserveed keyword type
            ## needs to specify what operand we're going for
            if k == "type":
              btype = v
              continue
            if k == "limit":
              limit = int(v)
              continue
            if k == "page":
              page = limit * int(page)
              continue
         

            if type(v) is list:
                for i in v:
                    opts.append(dict(key=k, value=i['value'], op=i['op']))
            else:
                opts.append(dict(key=k, value=v['value'], op=v['op']))

        if not len(message['data']>0):

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

            if btype == 'AND':
              query = reduce(lambda a,b:(a&b),queries)
            else: 
              query = reduce(lambda a,b:(a|b),queries)
        
            if limit != 12:
              if page != 0:
                rows = _OL_DB(query).select(limitby=(0, page + limit))
              else: 
                rows = _OL_DB(query).select(limitby=(0, limit))
            else:
              rows = _OL_DB(query).select(limitby=(0, limit))

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
