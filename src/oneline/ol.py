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

DEFAULTS = dict(host='127.0.0.1', port=9000, path=os.path.abspath(os.path.join(os.path.dirname(__file__), 'static')))
SETTINGS = dict(table='', agent=[], nodes=[])
SERVERS = dict(host='server.socket_host', port='server.socket_port', path='tools.staticdir.root')
TABLE = ''
MODULES = []
_OL_SERVER = {}
_OL_DB = []
_OL_DBS = []
_OL_AGENT = {}
_OL_TABLE = ''

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

class settings(object):
    global SETTINGS
    
    def init(*arguments, **keywords):
        pass

@cherrypy.expose
def proto(self):
    cherrypy.log("Handler created: %s" % repr(cherrypy.request.ws_handler))

@cherrypy.expose
def proto_():
    cherrypy.log("Handler created: %s" % repr(cherrypy.request.ws_handler))


"""
downstream packets
are sent in BSON
"""
def downstream():
    global MODULES

    for i in MODULES:
        """
        get a downstream
        request for this
        """

        config = scan_config(i + '.conf')

        if 'downstream' in config.keys():
            if config['downstream']:
                if 'dispatcher' in config.keys():
                    sock = socket.socket()
                    sock.connect((config['dispatcher_address'], config['dispatcher_port']))
                    packet = sock.recv(2048)
                    db = storage(caller=caller_name())
                    pipeline = pipeline(pline, db, {}, config)

                    message = pipeline.run(packet)
                    sock.send(message)

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
    stack = inspect.stack()
    start = 0 + skip
    if len(stack) < start + 1:
      return ''
    parentframe = stack[start][0]    

    name = []
    module = inspect.getmodule(parentframe)
    # `modname` can be None when frame is executed directly in console
    # TODO(techtonik): consider using __main__
    if module:
        name.append(module.__name__)
    # detect classname
    if 'self' in parentframe.f_locals:
        # I don't know any way to detect call from the object method
        # XXX: there seems to be no way to detect static method call - it will
        #      be just a function call
        name.append(parentframe.f_locals['self'].__class__.__name__)
    codename = parentframe.f_code.co_name
    if codename != '<module>':  # top level usually
        name.append( codename ) # function or a method
    del parentframe
    return ".".join(name)

"""
scan the whole config aside from the
database settings.
"""
def scan_config(caller):

    config = dict()
    proto = re.findall(r'([\w\_]+)\.', caller)
    conf = False
    has_config = False

    if len(proto) > 0:
        config['module'] = proto[0]
        config_name = proto[0] + '.conf'
    else:
        config_name = ''

    curr = os.getcwd()

    try:

        if os.path.exists('/usr/local/oneline/conf/'):
            os.chdir('/usr/local/oneline/conf')
            prefix = '/usr/local/oneline/conf'
            if os.path.isfile(config_name):
                has_config = True
                f = open(os.path.realpath(config_name), 'r+').read()
    
    except:
        pass
    pass

    if not has_config:
        """
        if we couldn't find a config file
        resort to properties in default config
        """
        if conf:
            pass    
        pass
    else:
        broadcast = re.findall("ol_broadcast\s+\=\s+\'(.*)\'", f)
        if len(broadcast) > 0:
            config['broadcast'] = broadcast[0]
        else:
            config['broadcast'] = 'multiple'

        frequency = re.findall("ol_freq\s+\=\s+\'(.*)\'", f)

        if len(frequency) > 0:
            config['freq'] = frequency[0]

        logging = re.findall("ol_logging\s+\=\s+\'(.*)\'", f)

        if len(logging) > 0:
            config['logging'] = logging[0]
        else:
            config['logging'] = True


        peers = re.findall("ol_peers\s+\=\s+(\d+)", f)
        
        if len(peers) > 0:
            config['peers'] = peers[0]

        mc = re.findall("ol_memcache\s+\=\s+\'(.*)\'", f)

        if len(mc) > 0:
            config['memcache'] = True
            try:
                config['memcache_client'] = memcache.Client(['127.0.0.1:11211'], debug=0)
            except:
                config['memcache'] = False
                config['memcache_client'] = False
        else:
            config['memcache'] = False

        multi = re.findall("ol_multiplex\s+\=\s+\'(.*)\'", f)

        if len(multi) > 0:
            config['multiplex'] = True
            config['multiplex'] = multi[0]

        upstream = re.findall("ol_upstream\s+\=\s+\'(.*)\'", f)

        if len(upstream) > 0:
            if upstream[0] == 'yes':
                config['upstream'] = True
            else:
                config['upstream'] = False
        else:
            config['upstream'] = False

        ## now find
        ## its cluster
        cluster = re.findall("ol_cluster\s+\=\s+\'(.*)\'", f)
        if len(cluster) > 0:
            clusterblob = re.findall("ol_cluster\s+\=\s+(.*)", f)[0]
            config['cluster'] = re.findall("'([\w\d\.]+)'", clusterblob)
        else:
            config['cluster'] = False

        downstream = re.findall("ol_downstream\s+\=\s+\'(.*)\'", f)
        if len(downstream) > 0:
            if downstream[0] == 'yes':
                config['downstream'] = True
            else:
                config['downstream'] = False
        else:
            config['downstream'] = False

        """
        dispacher = re.findall("ol_dispatcher\s+\=\s+\'(.*)\'", f)
        if len(dispatcher) > 0:
            config['dispatcher'] = dispatcher[0]
        else:
            config['dispatcher'] = False

        dispatcher = re.findall("ol_dispatcher_address\s+\=\s+\'(.*)\'", f)
        if dispatcher:
            config['dispatcher_address'] = dispatcher[0]
        else:
            config['dispatcher_address'] = False

        dispatcher = re.findall("ol_dispatcher_port\s+\=\s+\'(.*)\'", f)
        if dispatcher:
            config['dispatcher_port'] = dispatcher[0]
        else:
            config['dispatcher_port'] = False

        dispatcher = re.findall("ol_dispatcher_timeout\s+\=\s+\'(.*)\'", f)
        if dispatcher:
            config['dispatcher_timeout'] = dispatcher[0]
        else:
            config['dispatcher_timeout'] = 10
        """

        stream = re.findall("ol_stream_into\s+\=\s+\'(.*)\'", f)
        if len(stream) > 0:
            stream[0] = re.sub("stream:\/\/", "/usr/local/oneline/streams/", stream[0])
            config['stream_into'] = stream[0]
        else:
            config['stream_into'] = False 


        """ parse any other key value values """
        kv = re.findall("([\w_]+)\s+\=\s+\'(.*)\'", f)
        if len(kv) > 0: 
          ## tuples
          for i in kv:
            config[i[0]] = i[1]



    os.chdir(curr)
    return config


"""
start the streaming
process
"""
def stream(agent='', pline='', db=''):
    obj = inspect.currentframe().f_back.f_locals['self']

    if db == '':
        db = storage(caller=caller_name())

    return pipeline(pline, db, obj, scan_config(caller_name()))


def parse_message(message):
  literal = ast.literal_eval(message.__str__())
  return bsonlib.loads(bytearray(literal).__str__())

## opposite parse_message
def pack_message(message):
  bytes = map(ord, bsonlib.dumps(message)).__str__()
  return bytes

"""
parse the config
and provide a key value structure
"""
def config():
  return scan_config(caller_name())

class _server(object):
    def __init__(self, host, port, ssl=False):
        self.host = host
        self.port = port
        self.scheme = 'wss' if ssl else 'ws'
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

    def _make_new(self, name):
        setattr(self, name, proto_)

    def _object_handler(self):
        pass

    ##@cherrypy.expose
    ##def ws(self):
    ##      cherrypy.log("Handler created: %s" % repr(cherrypy.request.ws_handler))

"""
plugin for ws4py. defines
some basic methods to add, delete 
and get method
"""
class plugin(WebSocketPlugin):
    def __init__(self, bus):
        WebSocketPlugin.__init__(self, bus)
        self.clients = {}
 
    def start(self):
        WebSocketPlugin.start(self)
        self.bus.subscribe('add-client', self.add_client)
        self.bus.subscribe('get-client', self.get_client)
        self.bus.subscribe('del-client', self.del_client)
 
    def stop(self):
        WebSocketPlugin.stop(self)
        self.bus.unsubscribe('add-client', self.add_client)
        self.bus.unsubscribe('get-client', self.get_client)
        self.bus.unsubscribe('del-client', self.del_client)
 
    def add_client(self, name, websocket):
        if not name in self.clients.keys():
            self.clients[name] = []

        self.clients[name].append(websocket)
 
    def get_client(self, name):
        return self.clients[name]
 
    def del_client(self, name):
        del self.clients[name]

class server(object):
    global SERVERS
    global MODULES
    global DEFAULTS
    global _OL_SERVER

    def __init__(self, 
             host=DEFAULTS['host'], 
             port=DEFAULTS['port'],
             path=DEFAULTS['path']):

        """
        first obtain the 
        basic values found
        in the master config at: ../conf/Main.conf
        """

        curr = os.getcwd()

        if os.path.exists('/usr/local/oneline/conf'):
            os.chdir('/usr/local/oneline/conf')
            f = open('/usr/local/oneline/conf/Main.conf').read()    

        try:
            host = re.findall("ol_host\s+\=\s+\'(.*)\'", f)[0]
        except:
            pass

        try:
            port = int(re.findall("ol_port\s+\=\s+\'(.*)\'", f)[0])
        except:
            pass

        os.chdir(curr)

        self.host = host 
        self.port = int(port)
        self.path = path 
        self.ssl = False

        cherrypy.config.update({SERVERS['host']: host,
                        SERVERS['port']: port,
                    SERVERS['path']: path}) 

        if os.path.exists('/usr/local/oneline/socket/'):
            piddir = '/usr/local/oneline/socket/'

        plugin(cherrypy.engine).subscribe()
        cherrypy.process.plugins.PIDFile(cherrypy.engine, piddir + 'oneline.pid.txt').subscribe()
        cherrypy.process.plugins.Monitor(cherrypy.engine, downstream, frequency=5).subscribe()

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
        else:
            if os.path.exists('../../modules/'):
                prefix = os.path.abspath('../../modules')
                os.chdir('../../modules')
                files = os.listdir('./')
            elif os.path.exists('../modules/'):
                os.chdir('../modules')
                prefix = os.path.abspath('../modules')
                files = os.listdir('./')        
            elif os.path.exists('./modules/'):
                os.chdir('./modules')
                prefix = os.path.abspath('./modules')
                files = os.listdir('./')
            else:
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
            if len(re.findall('\.pyc', i)) > 0:
                continue

            if not len(re.findall('\.py', i)) > 0:
                continue

            cname = re.sub('\.ol|\.py', '', i)
            salt += '_' + i

            if not os.path.isfile(os.path.realpath(i)):
                continue

            os.chdir(os.path.split(os.path.realpath(i))[0]) 
            module = __import__(cname, globals(), locals())

            """
            open the file and determine its class
            """

            f = open(i, 'r+').read()

            os.chdir(prefix)

            m = re.findall('class\s+([\w\_]+)\([\w\_\.]+\):', f)

            if not len(m) > 0:
                continue

            module_name = m[0]
        

            setattr(_server, cname, proto)  

            config['/' + cname] = { 'tools.websocket.on': True,
                                    'request.module_md5': hashlib.md5(f).hexdigest(),
                                    'request.module_ctime': os.path.getmtime(os.path.realpath(i)),
                                    'request.module_object': module,
                                    'request.module_logger': logger(module_name),
                                    'request.module_uuid': uuid.uuid4().__str__(),
                                    'tools.websocket.handler_cls': getattr(module, module_name) }


            setattr(_server, module_name, proto)    

            config['/' + module_name] = { 'tools.websocket.on': True,
                                          'request.module_md5': hashlib.md5(f).hexdigest(),
                                          'request.module_ctime': os.path.getmtime(os.path.realpath(i)),
                                          'request.module_object': module,
                                          'request.module_logger': logger(module_name),
                                          'request.module_uuid': uuid.uuid4().__str__(),
                                          'tools.websocket.handler_cls': getattr(module, module_name) }

            MODULES.append(module_name)
            MODULES.append(cname)

        os.chdir(curr)

        print 'ONELINE CONFIG: ' 
        
        cherrypy.config.update({ 'request.modules_md5_snapshot': hashlib.md5(salt).hexdigest() })

        _OL_SERVER = _server(self.host, self.port, self.ssl)
        cherrypy.quickstart(_OL_SERVER, '', config=config)  


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

    def __init__(self, 
                 db_type='mysql', 
                 table='', 
                 host='localhost', 
                 username='root', 
                 password='', 
                 database='', 
                 port='',
                 caller='',
                 conf='',
                 silent=False,
                 custom=False
                ):
        global _OL_DB
        global _OL_TABLE
        import ol

        if conf == '':
            if caller == '':
                caller = caller_name()

            proto = re.findall(r'([\w\_]+)\.', caller)

            if len(proto) > 0:
                config_name = proto[0] + '.conf'
            else:
                config_name = ''
        else:
            config_name = conf
            caller = config_name

        has_config = False
        join_table = self.join_table = False
        join_on = self.join_on =False
        union_table = self.union_table = False
        union_on = self.union_on = False
        omitlist = self.omitlist = False
        no_table_set = False
        proto = False
        
        curr = os.getcwd()

        print "ONELINE: " +  caller + "'s " + "config file: " + config_name

        if table == '':
            try:

                """
                for custom loads use the current directory
                """
                if custom: 
                  file = os.path.abspath(curr) + "/" + conf
                  if os.path.isfile(file):
                    f = open(file, "r+").read()
                    has_config = True
          
                else:
                  if os.path.exists('/usr/local/oneline/conf'):
                      os.chdir('/usr/local/oneline/conf')
                      prefix = '/usr/local/oneline/conf'

                      if os.path.isfile(os.path.realpath(config_name)):
                          has_config = True
                          f = open(os.path.realpath(config_name), 'r+').read()

            except:
                pass

            try:
                main = open(prefix + '/Main.conf', 'r+').read()
            except:
                try:
                    main = open('./Main.conf', 'r+').read()
                except:
                    pass
            
            try:
                db_type = re.findall("db_type\s+\=\s+\'(.*)\'", main)

                ## priminitive check for db_type
                if len(db_type) > 0:
                  db_type = db_type[0]
                else:
                  no_table_set = 1
                database = re.findall("db_database\s+\=\s+\'(.*)\'", main)[0]
                username = re.findall("db_user\s+\=\s+\'(.*)\'", main)[0]
                password = re.findall("db_pass\s+\=\s+\'(.*)\'", main)[0]
                table = re.findall("db_table\s+\=\s+\'(.*)\'", main)[0]
            except:
                pass



            ## when a db type is not provided
            ## we should not use the storage object
            ## TODO:
            ## provide a mock function  
            if no_table_set: 
              return None
            
            if not has_config:
                """
                if we couldn't find a config file
                resort to properties in default config
                """
                if conf:
                    pass    
                pass
            else:
                try:
                    db_type = re.findall("db_type\s+\=\s+\'(.*)\'", f)
                    if len(db_type) > 0:
                      db_type = db_type[0]
                    else:
                      no_table_set = True
              
                    table = re.findall("db_table\s+\=\s+\'(.*)\'", f)[0]
                    database = re.findall("db_database\s+\=\s+\'(.*)\'", f)[0]
                    username = re.findall("db_user\s+\=\s+\'(.*)\'", f)[0]
                    password = re.findall("db_pass\s+\=\s+\'(.*)\'", f)[0]
                    host = re.findall("db_host\s+\=\s+\'(.*)\'", f)[0]
                    port = re.findall("db_port\s+\=\s+\'(.*)\'", f)[0]
                    join_table = re.findall("db_join_table\s+\=\s+\'(.*)\'", f)[0]
                    join_on = re.findall("db_join_on\s+\=\s+\'(.*)\'", f)[0]
                except:
                    pass

               

                if no_table_set: 
                  return 

                try:
                    join_table = re.findall("db_join_table\s+\=\s+\'(.*)\'", f)[0]
                    join_on = re.findall("db_join_on\s+\=\s+\'(.*)\'", f)[0]
                except:
                    pass

                try:
                    union_table = re.findall("db_union\s+\=\s+\'(.*)\'", f)[0]
                    union_on = re.findall("db_union_on\s+\=\s+\'(.*)\'", f)[0]
                except:
                    pass

                try:
                    omitblob = re.findall("db_omit\s+\=\s+(.*)", f)[0]
                    omitlist = re.findall("'([\w]+)'", omitblob)
                except:
                    pass

                try:
                    dbfolder = re.findall("db_omit\s+\=\s+(.*)", f)[0] # for sqlite
                except:
                    dbfolder = "/usr/bin/"

        if proto:
          logger = cherrypy.config['/' + proto[0]]['request.module_logger']
        else:
          logger = None

        """ treat mariadb as mySQL """
        if db_type in ['mariadb']:
            db_type = 'mysql'   

        if db_type in ['mongodb']:
            host = host + ':' + port

        print "ONELINE: using table: " + table

        """
        do we already have a storage object for this?
        """

        if db_type in ['couchdb']:
            _OL_DB = self.db = DAL(db_type + '://' + host + ':5984/')
        else:
            if db_type == 'sqlite':
                _OL_DB = self.db = DAL('sqlite://' + database + '.db', migrate_enabled=False, folder=dbfolder, auto_import=True)    
            else:   
                if silent:
                  _OL_DB = self.db = DAL(db_type + '://' + username + ':' + password + '@' + host + '/' + database, pool_size=1)
                else:
                  _OL_DB = self.db = DAL(db_type + '://' + username + ':' + password + '@' + host + '/' + database, pool_size=1, migrate_enabled=False)


        _OL_TABLE = table

        print "ONELINE: connected to " + db_type

        """
        when silent mode is on do not further check
        """
      
        self.table = table
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

        elif db_type in ['mongodb', 'couchdb']:

            try:
                fieldsblob = re.findall("db_fields\s+\=\s+(.*)", f)[0]
                fields = re.findall("'([\w]+)'", fieldsblob)
            except:
                pass

        elif db_type in ['sqlite']:
            tables = self.db.executesql('SELECT name FROM sqlite_master WHERE type = "table"') 

        elif db_type in ['postgres']:

            tables = self.db.executesql("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE';")


        if not db_type in ['mongodb', 'couchdb']:

            for i in tables:
                table_name = i[0]

                args = []
                args.append(table_name)

                if db_type in ['mysql']:
                    schema = self.db.executesql('explain ' + i[0])

                elif db_type in ['sqlite']:
                    schema = self.db.executesql('PRAGMA table_info({0});'.format(i[0]))
                    
                elif db_type in ['postgres']:
                    schema = self.db.executesql("select column_name, data_type, character_maximum_length from INFORMATION_SCHEMA.COLUMNS where table_name = '" + i[0] + "';")

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
                          args.append(Field(j[0]))

                

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


            if not table in self.db.tables:
                raise NameError('ONELINE: This table does not exist in the database')

        else:
            args = []

            args.append(table)

            for i in fields:
                args.append(Field(i))

            self.db.define_table(*args)

        _OL_TABLE = table
        _OL_DB = self.db
        self.table = table

        if join_table:
            self.join_table = join_table
        else:
            self.join_table = False

        if join_on:
            self.join_on = join_on

        if union_table:
            self.union_table = union_table
        else:
            self.union_table = False

        if union_on:
            self.union_on = union_on

        if omitlist:
            self.omitlist = omitlist
        else:
            self.omitlist = False

        os.chdir(curr)


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
        if 'start' in dir(self):
            return self.start()

    def closed(self, *args):
        if 'end' in dir(self):
            return self.end()

    def received_message(self, m):
        if 'receiver' in dir(self):
            return self.receiver(m)

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

    def __init__(self, objects, storage, caller, config):
        self._objs = objects        
        self.storage = storage
        self.caller = caller
        self.config = config
        self.blob = []

        if not 'broadcast' in self.config.keys() or self.config['broadcast'] == 'singular':
            self.caller.unique = uuid.uuid4().__str__()
        else:
            """ use the same unique id as the modules registered one """
            self.caller.unique = cherrypy.config['/' + config['module']]['request.module_uuid']

        if not 'freq' in self.config.keys():
            self.caller.freq = 0
        else:
            self.caller.freq = int(self.config['freq'])

        if self.config['memcache']:
            if 'memcache_client' in self.config.keys():
                self.memcache = self.config['memcache_client'] if self.config['memcache_client'] \
                                                               else None

            else:
                self.memcache = None
        else:
            self.memcache = None


        if 'multiplex' in self.config.keys():
            if self.config['multiplex']:
                self.multiplex = True 
                self.multiplex_amount = int(self.config['multiplex'])
                self.multiplex_current = 0
                self.multiplex_container = []

            else:
                self.multiplex = False
        else:
            self.multiplex = False


        self.caller.config = self.config
        self.logger = cherrypy.config['/' + config['module']]['request.module_logger']

        self.setup()

    def setup(self):
        cherrypy.engine.publish('add-client', self.caller.unique, self.caller)


    """
    broadcast a message to all connections
    """
    def broadcast(self, message):
        if not isinstance(message, dict):
            message = dict(message=unicode(message))

        bytes = map(ord, bsonlib.dumps(message)).__str__()
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

    
        """
        check if we need to update the config
        """
        message = TextMessage(message.__str__())
        """ first check memcache """
        if not self.memcache is None:
            salt = hashlib.md5(message.__str__()).hexdigest()
            m = self.memcache.get(salt)

            if m:
                bytes = m

                if self.multiplex:
                    if self.multiplex_current == self.multiplex_amount:
                        """ send the message """

                        message = dict(message=self.multiplex_container)
                        bytes = map(ord, bsonlib.dumps(message)).__str__()

                        for i in client:
                            i.send(bytes)

                        try:
                            inspect.currentframe().f_back.f_locals['self'].provider(bytes)
                        except:
                            pass

                        self.multiplex_current = 0
                        self.multiplex_container = []

                    else:
                        """ store the message """
                        #self.multiplex_container.append(m)
                        self.multiplex_current += 1

                else:
                    for i in client:
                        i.send(bytes)

                    try:
                        inspect.currentframe().f_back.f_locals['self'].provider(bytes)
                    except:
                        pass                

                _time.sleep(self.caller.freq)
                return


        if len(re.findall(r'interop', message.__str__())) > 0:
            m = json.loads(message.__str__())
            is_json = True

        else:
            literal = ast.literal_eval(message.__str__())

            """
            ensure the message fits in
            """

            m = bsonlib.loads(bytearray(literal).__str__())
            is_json = False

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
        ## any existing data we need to copy
        ## this is for when the module appends
        ## data. we need to just return it to the client
        d = []
        if 'data' in m.keys():
          d = m['data']
        else:
          d = []

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

        for i in self._objs:
            try:
                i.storage = self.storage
                i.logger = self.logger

                if c == 0:
                    m = i.run(m)
                else:
                    m = i.run(self._append(m, p))
            except:
                i.log()
                c += 1

            c += 1

        if self.storage.union_table:
            mp = m
            m = i_m

            _OL_DB = self.storage.get()['db']
            _OL_TABLE = self.storage.get()['table']
            self.storage.set('table', self.storage.union_table)

            c = 0
            for i in self._objs:
                try:
                    i.storage = self.storage
                    i.logger = self.logger

                    if c == 0:
                        m = i.run(m)
                    else:
                        m = i.run(self._append(m, p))
                except:
                    i.log()
                    c += 1

                c += 1

            m = list(set(m + mp))
        else:
            pass

        """
        if we dont have a confidence value by now 
        append one to all before filtering
        """
        try:
            if not 'confidence' in m[0].keys():
                m = [dict(i.items() + [('confidence', 1)]) for i in m]

            """
            by now m should be a nodecollection.
            we must filter this to only the needed
            amount of node:ws
            """
            if isinstance(m, list):
                m = self._filter(m)

        except:
            pass


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
        omit any fields
        that need to be
        erased
        """
        if self.storage.omitlist:
            for i in range(0, len(m)):
                for j in self.storage.omitlist:
                    if j == 'confidence':
                        continue

                    del m[i][j]

        """
        if this is a downstream
        request simply return it
        """
        if self.config['downstream']:
            return m

        """
        is this an upstream
        request?
        then bind a socket
        to the request, 
        and listen for
        the responses
        when all responses
        are fulfilled, return
        """
        if self.config['upstream']:
            faddrs = []
            cluster = self.config['cluster']
            addr = self.config['dispatcher_address']
            timeout = int(self.config['dispatcher_timeout']);
            port = int(self.config['dispatcher_port'])
            print "Upstreaming to other servers"

            sock = socket.socket()
            sock.bind((addr, port))
            sock.listen(5)

            try:
                start = time_.time()
                while True:
                    now = time_.time()

                    if now - start > timeout:
                        break

                    if len(faddrs) == len(cluster):
                        break

                    client, addr = sock.accept()

                    if not addr in self.config.cluster:
                        continue

                    ## dont do it twice
                    if addr in faddrs:
                        continue

                    faddrs.append(addr)
                    client.send(m['packet'])

                    message_ = client.recv(20024)

                    literal = ast.literal_eval(message_.__str__())

                    """
                    ensure the message fits in
                    """

                    m_ = bsonlib.loads(bytearray(literal).__str__())

                    """
                    now merge both m_ and m
                    """
            except:
                self.logger.append(dict(message="Unable to bind socket to upstream", object=self.__str__()))


        """
        if results are met
        we need to run the
        provider. First get the client
        this message was received from
        """

        client = cherrypy.engine.publish('get-client', self.caller.unique).pop()

        try:
            for k in range(0, len(m)):
                if isinstance(m[k], dict):
                    for k1, v1 in m[k].iteritems():
                        if isinstance(m[k][k1], str):
                            m[k][k1] = unicode(m[k][k1])    

            m = dict(data=m, status=u'ok')
        except:
            m = dict(data=[], status=u'empty')

        if d:

          ## d just needs to by a list
          ## with dictionaries
          for i in d:
            i['confidence'] = 1
            m['data'].append(i)


        if is_json:
            bytes = json.dumps(m)
        else:
            bytes = map(ord, bsonlib.dumps(m)).__str__()

        if self.multiplex:
            if self.multiplex_current == self.multiplex_amount:
                """ send the message """

                message = dict(message=self.multiplex_container)
                bytes = map(ord, bsonlib.dumps(message)).__str__()

                for i in client:
                    i.send(bytes)

                try:
                    inspect.currentframe().f_back.f_locals['self'].provider(bytes)
                except:
                    pass

                self.multiplex_current = 0
                self.multiplex_container = []

            else:
                """ store the message """
                self.multiplex_container.append(m)
                self.multiplex_current += 1

        else:
            for i in client:
                i.send(bytes)   

            try:
                inspect.currentframe().f_back.f_locals['self'].provider(bytes)
            except:
                pass


        """ stream output into another file """
        """ we recognize the following file types: """
        """ .php, .py, .pl, .rb, and .txt """
        """ first four will invoke their interpreter. .txt will """
        """ merely dump contents """
        """ fix for subprocess """
        """ NOTE: interop data in this case should always be JSON to  """
        """ let ease of integration. For this cause it is best to use 'JSON' as """
        """ interop when using stream_into """
        if self.config['stream_into']:
            type = re.findall("\.(\w+)$", self.config['stream_into'])
            if len(type) > 0:
                inter = type[0]

            try:
                if inter == 'php':
                    os.system("php {0} '{1}'".format(os.path.abspath(self.config['stream_into']), json.dumps(m)))

                elif inter == 'py':
                    os.system("python {0} '{1}'".format(self.config['stream_into'], json.dumps(m)))

                elif inter == 'pl':
                    os.system("perl {0} '{1}'".format(self.config['stream_into'], json.dumps(m)))

                elif inter == 'rb':
                    os.system("ruby {0} '{1}'".format(self.config['stream_into'], json.dumps(m)))

                elif inter == 'java':
                    ##os.system("javac {0}".format(self.config['stream_into']) 
                    os.system("java {0} {1}".format(self.config['stream_into'], json.dumps(m)))

                elif inter == 'jar':
                    os.system("java -jar {0} {1}".format(self.config['stream_into'], json.dumps(m)))
                

            except:
                self.logger.append(dict(message="Unable to call ScriptingEngine for {1}".format(inter), object=self.__str__()))



        if not self.memcache is None:
            salt = hashlib.md5(message.__str__()).hexdigest()
            self.memcache.set(salt, bytes)

        _time.sleep(self.caller.freq)

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

        if os.path.isfile(file_name):
            self.file_name = file_name
        else:
            f = open(file_name, 'w+')
            f.close()
            self.file_name = file_name

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
        if not 'data' in message.keys():
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
          self.limit = message['packet']['geo']['limit']

        
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

        if not 'data' in message.keys():
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
            q2.append(getattr(getattr(_OL_DB, _OL_TABLE), "lat") >= lat) 
            q2.append(getattr(getattr(_OL_DB, _OL_TABLE), "lat") <= lat_plus)
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
            testings = [dict(
              minlat=lat,
              maxlat=lat_plus,
              minlng=lng,
              maxlng=lng_plus,
              operand1='>=',
              operand2='<='
            ),
            dict(
              minlat=lat,
              maxlat=lat_plus,
              minlng=lng,
              maxlng=lng_minus,
              operand1='>=',
              operand2='<='
      
            ),
            dict(
              minlat=lat,
              maxlat=lat_minus,
              minlng=lng,
              maxlng=lng_plus,
              operand1='<=',
              operand2='>='
            )
            ]
            print testings
            for i in testings:
               print i
               print "minlat: {0}, maxlat: {1},  minlng: {2}, maxlng: {3}\n operands: {4}, {5}".format(i['minlat'], i['maxlat'], i['minlng'],i['maxlng'], i['operand1'], i['operand2'])
            
          
            q1f = reduce(lambda a,b:(a&b), q1)
            q2f = reduce(lambda a,b:(a&b), q2)
            q3f = reduce(lambda a,b:(a&b), q3)
            queriesf.append(q1f)
            queriesf.append(q2f)
            queriesf.append(q3f)
            finalQuery = reduce(lambda a,b:(a|b), queriesf)
            print "limit is:"
            print self.limit

            
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
              expr2 = bool((float(message['data'][k]['lat']) >= lat) and \
                      (float(message['data'][k]['lat']) <= lat_minus) and \
                      (float(message['data'][k]['lng']) >= lng) and \
                      (float(message['data'][k]['lng']) <= lng_minus))
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

        if not 'data' in message.keys():

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

        if not 'data' in message.keys():
            queries = []
            queries.append(getattr(_OL_DB, _OL_TABLE))

            query = reduce(lambda a,b:(a&b),queries)
            rows = _OL_DB(query).select(orderby='<random>', limitby=(0, amount))    

            return rows.as_list()
        else:
            found = len(message['data'])

            for i in range(0, amount):
                sel = _random.randint(0, found)

                if not 'confidence' in message['data'][sel].keys():
                    message['data'][sel]['confidence'] = 1
                else:
                    message['data'][sel]['confidence'] += 1

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
        _OL_DB = self.storage.get()['db']
        _OL_TABLE = self.storage.get()['table']

        if start > end:
            self.errors.append('Start time must be lower than end time ' + ' received (start: ' + start + ')')
            raise NameError('ONELINE: start time higher than end time in time')

        if not 'data' in message.keys():
            if not 'stime' in getattr(_OL_DB, _OL_TABLE).fields:
                self.errors.append('This table does have a stime column')
                raise NameError('ONELINE: This table does have a stime column')

            if not 'etime' in getattr(_OL_DB, _OL_TABLE).fields:
                self.errors.append('This table does have a etime column')
                raise NameError('ONELINE: This table does have a etime column')

            if getattr(getattr(getattr(_OL_DB, _OL_TABLE), 'stime'), 'type') != 'integer':
                setattr(getattr(getattr(_OL_DB, _OL_TABLE), 'stime'), 'type', 'integer')

            if getattr(getattr(getattr(_OL_DB, _OL_TABLE), 'etime'), 'type') != 'integer':
                setattr(getattr(getattr(_OL_DB, _OL_TABLE), 'etime'), 'type', 'integer')

            queries = []

            queries.append(getattr(getattr(_OL_DB, _OL_TABLE), 'stime') >= start)
            queries.append(getattr(getattr(_OL_DB, _OL_TABLE), 'etime') <= end)
            queries.append(getattr(getattr(_OL_DB, _OL_TABLE), 'stime') <= \
                           getattr(getattr(_OL_DB, _OL_TABLE), 'etime'))

            query = reduce(lambda a,b:(a&b),queries)
            rows = _OL_DB(query).select()

            return rows.as_list()
            
        else:
            for k in range(0, len(message['data'])):
                if int(message['data'][k]['stime']) >= start and \
                   int(message['data'][k]['etime']) <= end and \
                   int(message['data'][k]['stime']) <= int(message['data'][k]['etime']):
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

        if not 'data' in message.keys():

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

            for k in range(0, len(message['data'])):

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
