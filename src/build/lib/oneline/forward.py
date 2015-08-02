import sys
import os
import shutil
import re
import bsonlib
import cherrypy
import time

"""
native support for XHR forwarding to WebSocket via
Cherrypy and WS4py

THIS should run on port 9091 accepting HTTP 1/1
requests it will then use the ws protocol with
python and upstream requests to the running
oneline server which usually runs on port
9090
"""


from ws4py.client.threadedclient import WebSocketClient

class ForwardClient(WebSocketClient):
    def opened(self):
        """
        wait 5 seconds for a reply before cancelling
        """
        self.ready = False
        self.reply = "Error:"
        now = time.time()
        try:
          self.send(self.msg)
        except:
          self.reply = "Error: "   
          self.ready = True
          self.close()

    def closed(self, code, reason):
        print(("Closed down", code, reason))

    def get_reply(self):
      return self.reply

    def is_ready(self):
      return self.ready

    def received_message(self, m):
      """ respond with the same message to our """
      self.ready = True 
      self.reply = m
      self.close()

class Forwarder(object):
  def __init__(self):
    self.clients = dict() 
  """ 
  receive requests by xhr and handle them
  using our websocket client
 
  check if our user has a connection with a client if he does
  use that
  """
  @cherrypy.expose
  def run(self, **params):
    ## mod_url should be the url we are trying to connect
    ## with
    mod = cherrypy.request.params['mod_url']
    ## data exposes our data
    data = cherrypy.request.params['data']
    key = cherrypy.request.params['key']
    if key in self.clients.keys():
      ws = self.clients[key]
      ws.ready = False
      ws.send(data)
    else:
      ws = ForwardClient(mod)
      ws.msg = data
      ws.ready = False
      ws.daemon = False
      ws.msg = mod
      ws.connect()

    """
    wait for a reply
      
    this should be analagous to comet type
    ajax
    
    did we exit prematuraly
    """
    now = time.time()
    t = time.time()
    while not ws.is_ready() and t - now <= 5:
      t = time.time() 

    """
    one of oneline's interop formats
    """
    reply = ws.get_reply()
    return reply

def start_forwarder(ip, port):    
  cherrypy.config.update({
    "server.socket_host": ip,
    "server.socket_port":  port 
  })
  piddir = "/usr/local/oneline/socket/"
   
  cherrypy.process.plugins.PIDFile(cherrypy.engine, piddir + "/oneline.forwarder.pid.txt")
  cherrypy.quickstart(Forwarder())
