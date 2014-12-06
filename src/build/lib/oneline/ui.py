import cherrypy
import os
import re

"""
	UI For Oneline. Starts the user interface
	on a local port

	i.e

	online-ui --start-ui

	goto: localhost:991/

	directories should be formatted as:

	localhost:991/pipeline

"""
SERVERS = dict(host='server.socket_host', port='server.socket_port', path='tools.staticdir.root')

class OnelineUI(object):
	def __init__(self, host, port):
		self.host = host
		self.port = port
		self.filepath = "/usr/local/oneline/etc/ui/"

	"""
	other files are to implement
	index should get the main ui file and load..


	edit the status of oneline as per
	calling:
	oneline --status

	show modules:
	oneline --list
	"""
	@cherrypy.expose
	def index(self):
		module_text = ''
		ms = os.listdir('/usr/local/oneline/modules/')
		for i in ms:
			r = re.findall("\.py$", i)
			if not len(r) > 0:
				continue

			module_text += """
				<tr>
					<td>{0}</td>
				</tr>
			""".format(i)

		
		f = open(self.filepath + "main").read()

		f = re.sub("{status_code}", "", f)
		f = re.sub("{status_msg}", "", f)
		f = re.sub("{status_caption}", "", f)
		f = re.sub("{modules}", module_text, f)

		return f


	@cherrypy.expose
	def pipeline(self, **params):
		pass 

	@cherrypy.expose
	def client(self):
		pass

	@cherrypy.expose

	def module(self):
		pass
