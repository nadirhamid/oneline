## This file is part of the oneline Framework
## Copyrighted by Nadir Hamid <matrix.nad@gmail.com>
## License BSD-Clause 2

import uuid
import os
import cherrypy
from dal import DAL, Field
from ws4py.server.cherrypyserver import WebSocketPlugin, WebSocketTool
from ws4py.websocket import WebSocket
from ws4py.messaging import TextMessage

class IO(object):
	pass

class server(IO):

	"""
	This will start the oneline server. If no
	arguments are given it will default to its standard
	params.
	@param host -> [string] host
	@param port -> [string] port
	@param path -> [string] path
	"""
	def __init__(self, host='127.0.0.1', port='9000', path=''):
		cherrypy.config.update({'server.socket_host': host,
					'server.socket_port': args.port,
					'tools.staticdir.root': path })

		WebSocketPlugin(cherrypy.engine).subscribe()
		cherrypy.tools.websocket = WebSocketTool()
		
