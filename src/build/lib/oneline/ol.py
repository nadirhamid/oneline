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
import datetime
import os
import re
import sys
import cherrypy
import uuid
import random as _random
import time as _time

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
			"time",
			"writer"
	   ]

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

	if len(proto) > 0:
		config['module'] = proto[0]
		config_name = proto[0] + '.conf'
	else:
		config_name = ''

	curr = os.getcwd()

	try:
		if os.path.exists('../../conf/'):
			os.chdir('../../conf')
			prefix = '../../conf'

			if os.path.isfile(config_name):
				has_config = True
				f = open(config_name, 'r+').read()

		elif os.path.exists('../conf/'):
			os.chdir('../conf')
			prefix = '../conf'

			if os.path.isfile(config_name):
				has_config = True
				f = open(config_name, 'r+').read()

		elif os.path.exists('./conf/'):
			os.chdir('./conf')
			prefix = './conf'
			if os.path.isfile(config_name):
				has_config = True
				f = open(config_name, 'r+').read()
		else:
			os.chdir('../../conf')
			prefix = '../../conf'

			if os.path.isfile(config_name):
				has_config = True
				f = open(config_name, 'r+').read()
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
		try:
			config['broadcast'] = re.findall("ol_broadcast\s+\=\s+\'(.*)\'", f)[0]
			frequency = re.findall("ol_freq\s+\=\s+\'(.*)\'", f)

			if frequency:
				config['freq'] = frequency[0]

			logging = re.findall("ol_logging\s+\=\s+\'(.*)\'", f)

			if logging:
				config['logging'] = logging[0]

			mc = re.findall("ol_memcache\s+\=\s+\'(.*)\'", f)

			if mc:
				config['memcache'] = True
				try:
					config['memcache_client'] = memcache.Client(['127.0.0.1:11211'], debug=0)
				except:
					config['memcache'] = False
					config['memcache_client'] = False
			else:
				config['memcache'] = False

		except:
			pass

	os.chdir(curr)

	print config
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
    ##    	cherrypy.log("Handler created: %s" % repr(cherrypy.request.ws_handler))

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

		self.host = host 
		self.port = int(port)
		self.path = path 
		self.ssl = False

		cherrypy.config.update({SERVERS['host']: host,
				        SERVERS['port']: port,
					SERVERS['path']: path})	

		if os.path.exists('../../socket/'):
			piddir = '../../socket/'
		elif os.path.exists('../socket/'):
			piddir = '../socket/'
		elif os.path.exists('./socket/'):
			piddir = './socket/'
		else:
			piddir = '../../socket/'

		plugin(cherrypy.engine).subscribe()
		cherrypy.process.plugins.PIDFile(cherrypy.engine, piddir + 'oneline.pid.txt').subscribe()

		cherrypy.tools.websocket = WebSocketTool()

	def start(self):
		global _OL_SERVER

		curr = os.getcwd()

		if os.path.exists('../../modules/'):
			os.chdir('../../modules')
			files = os.listdir('./')
		elif os.path.exists('../modules/'):
			os.chdir('../modules')
			files = os.listdir('./')		
		elif os.path.exists('./modules/'):
			os.chdir('./modules')
			files = os.listdir('./')
		else:
			os.chdir('../../modules')
			files = os.listdir('./')		

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

			module = __import__(cname, globals(), locals())

			"""
			open the file and determine its class
			"""

			f = open(i, 'r+').read()

			m = re.findall('class\s+([\w\_]+)\([\w\_\.]+\):', f)

			if not len(m) > 0:
				continue

			module_name = m[0]
		

			setattr(_server, cname, proto)	

			config['/' + cname] = { 'tools.websocket.on': True,
							  	    'request.module_md5': hashlib.md5(f).hexdigest(),
							  	    'request.module_ctime': os.path.getmtime(i),
							  	    'request.module_object': module,
							  	    'request.module_logger': logger(module_name),
							  	    'request.module_uuid': uuid.uuid4().__str__(),
				              		'tools.websocket.handler_cls': getattr(module, module_name) }


			setattr(_server, module_name, proto)	

			config['/' + module_name] = { 'tools.websocket.on': True,
										  'request.module_md5': hashlib.md5(f).hexdigest(),
										  'request.module_ctime': os.path.getmtime(i),
										  'request.module_object': module,
							  	    	  'request.module_logger': logger(module_name),
								  	      'request.module_uuid': uuid.uuid4().__str__(),
				              		   	  'tools.websocket.handler_cls': getattr(module, module_name) }

		os.chdir(curr)

		print 'ONELINE CONFIG: ' 
		print config
	 	
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
				 conf=''):
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
		curr = os.getcwd()

		print "ONELINE: " +  caller + "'s " + "config file: " + config_name

		if table == '':
			try:
				if os.path.exists('../../conf/'):
					os.chdir('../../conf')
					prefix = '../../conf'

					if os.path.isfile(config_name):
						has_config = True
						f = open(config_name, 'r+').read()

				elif os.path.exists('../conf/'):
					os.chdir('../conf')
					prefix = '../conf'

					if os.path.isfile(config_name):
						has_config = True
						f = open(config_name, 'r+').read()

				elif os.path.exists('./conf/'):
					os.chdir('./conf')
					prefix = './conf'
					if os.path.isfile(config_name):
						has_config = True
						f = open(config_name, 'r+').read()
				else:
					os.chdir('../../conf')
					prefix = '../../conf'

					if os.path.isfile(config_name):
						has_config = True
						f = open(config_name, 'r+').read()
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
				db_type = re.findall("db_type\s+\=\s+\'(.*)\'", main)[0]
				database = re.findall("db_database\s+\=\s+\'(.*)\'", main)[0]
				username = re.findall("db_user\s+\=\s+\'(.*)\'", main)[0]
				password = re.findall("db_pass\s+\=\s+\'(.*)\'", main)[0]
				table = re.findall("db_table\s+\=\s+\'(.*)\'", main)[0]
			except:
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
				try:
					db_type = re.findall("db_type\s+\=\s+\'(.*)\'", f)[0]
					table = re.findall("db_table\s+\=\s+\'(.*)\'", f)[0]
					database = re.findall("db_database\s+\=\s+\'(.*)\'", f)[0]
					username = re.findall("db_user\s+\=\s+\'(.*)\'", f)[0]
					password = re.findall("db_pass\s+\=\s+\'(.*)\'", f)[0]
					host = re.findall("db_host\s+\=\s+\'(.*)\'", f)[0]
					port = re.findall("db_port\s+\=\s+\'(.*)\'", f)[0]
				except:
					pass

		if db_type in ['mongodb']:
			host = host + ':' + port

		print "ONELINE: using table: " + table

		"""
		do we already have a storage object for this?
		"""

		if db_type in ['couchdb']:
			_OL_DB = self.db = DAL(db_type + '://' + host + ':5984/')
		else:
			_OL_DB = self.db = DAL(db_type + '://' + username + ':' + password + '@' + host + '/' + database, pool_size=1, migrate_enabled=False)

		_OL_TABLE = table

		print "ONELINE: connected to " + db_type
		

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



		elif db_type in ['postgres']:

			tables = self.db.executesql("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE';")

		if not db_type in ['mongodb', 'couchdb']:

			for i in tables:
				table_name = i[0]

				args = []
				args.append(table_name)

				if db_type in ['mysql']:
					schema = self.db.executesql('explain ' + i[0])
				elif db_type in ['postgres']:
					schema = self.db.executesql("select column_name, data_type, character_maximum_length from INFORMATION_SCHEMA.COLUMNS where table_name = '" + i[0] + "';")

				for j in schema:
					"""
					structure is as follows:
					{0 -> field_name, 1 -> type, 2 -> type, 3 ->, 4 -> default, 5 ->}
					"""

					args.append(Field(j[0]))

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
		os.chdir(curr)


	"""
	get a storage object	
	"""
	def get(self):

		self.db.commit()
		return dict(db=self.db, table=self.table)

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

		if 'memcache' in self.config.keys():
			if 'memcache_client' in self.config.keys():
				self.memcache = self.config['memcache_client'] if self.config['memcache_client'] \
															   else None

			else:
				self.memcache = None
		else:
			self.memcache = None

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

				for i in client:
					i.send(bytes)

				try:
					inspect.currentframe().f_back.f_locals['self'].provider(bytes)
				except:
					pass				

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

		if self._objs == '':
			self._objs = [globals()[i]() for i in m['packet'] if i in OBJS]

		p = m['packet']

		"""
		if no limit is set
		set the limit to the default
		"""
		if not 'limit' in dir(p):
			m['limit'] = 20
		else:
			m['limit'] = p['limit']

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
			if type(m) is list:
				m = self._filter(m)

		except:
			pass

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
	
		if is_json:
			bytes = json.dumps(m)
		else:
			bytes = map(ord, bsonlib.dumps(m)).__str__()


		for i in client:
			i.send(bytes)

		if not self.memcache is None:
			salt = hashlib.md5(message.__str__()).hexdigest()
			self.memcache.set(salt, bytes)

		try:
			inspect.currentframe().f_back.f_locals['self'].provider(bytes)
		except:
			pass

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

		if os.path.exists('../../logs/'):
			self.prefix = '../../logs/'
			os.chdir('../../logs')
		elif os.path.exists('../logs/'):
			self.prefix = '../logs/'
			os.chdir('../logs/')
		elif os.path.exists('./logs/'):
			self.prefix = './logs/'
			os.chdir('./logs')
		else:
			self.prefix = '../../logs/'
			os.chdir('../../logs')

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
		if os.path.exists('../../logs/'):
			os.chdir('../../logs')
		elif os.path.exists('../logs/'):
			os.chdir('../logs/')
		elif os.path.exists('./logs/'):
			os.chdir('./logs')
		else:
			os.chdir('../../logs')

		if not 'time' in data.keys():
			today = datetime.datetime.today()
			data['time'] = today.strftime('%m/%d/%y %I:%M:%S')

		if not 'addr' in data.keys():
			data['addr'] = '127.0.0.1'

		f = open(self.file_name, 'a+')

		line = "[" + data['time']  + ']' + ' - ' + data['addr'] + ' - ' + data['object'] + ' - ' + data['message'] + "\r\n"
		f.write(line)

		os.chdir(curr)

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
		self.last = 0
		self.errors = []

	def log(self):
		name = self.__str__()

		for i in self.errors:
			self.logger.append(dict(object=name, message=i))

	def run(self, message):

		lat = float(message['packet']['geo']['lat'])
		lng = float(message['packet']['geo']['lng'])
		range_ = message['packet']['geo']['range']
		_OL_DB = self.storage.get()['db']
		_OL_TABLE = self.storage.get()['table']

		lat_ = float(lat) + float(range_)
		lng_ = float(lng) + float(range_)
	
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

		if not 'lat' in getattr(_OL_DB, _OL_TABLE).fields:
			self.errors.append('This table does have a latitude column')
			raise NameError('ONELINE: This table does have a latitude column')

		if not 'lng' in getattr(_OL_DB, _OL_TABLE).fields:
			self.errors.append('This table does have a longitude column')
			raise NameError('ONELINE: This table does have a longitude column')

		if not 'data' in message.keys():
			queries = []

			queries.append(getattr(getattr(_OL_DB, _OL_TABLE), 'lat') >= lat)
			queries.append(getattr(getattr(_OL_DB, _OL_TABLE), 'lat') <= lat_)
			queries.append(getattr(getattr(_OL_DB, _OL_TABLE), 'lng') >= lng)
			queries.append(getattr(getattr(_OL_DB, _OL_TABLE), 'lng') <= lng_)

			query = reduce(lambda a,b:(a&b),queries)
			rows = _OL_DB(query).select()

			return rows.as_list()

		else:
			for k in range(0, len(message['data'])):
				if float(message['data'][k]['lat']) >= lat and \
				   float(message['data'][k]['lat']) <= lat_ and \
				   float(message['data'][k]['lng']) >= lng and \
				   float(message['data'][k]['lng']) <= lng_:
					if not 'confidence' in message['data'][k].keys():
						message['data'][k]['confidence'] = 1
					else:
						message['data'][k]['confidence'] += 1
				else:
						message['data'][k]['confidence'] = 0

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


class writer(object):
	pass

class echo(object):
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

		for k,v in message['packet']['event'].iteritems():
			if not k in getattr(_OL_DB, _OL_TABLE).fields:
				self.errors.append('This table does not have: ' + k + ' field in: ' + _OL_TABLE + ' table')

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

			query = reduce(lambda a,b:(a&b),queries)
			rows = _OL_DB(query).select()

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