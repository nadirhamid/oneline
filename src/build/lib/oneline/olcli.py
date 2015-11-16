import re
import sys 
import os
import shutil
import cherrypy
import psutil
from oneline import ol
import imp

statusTrans = {
    psutil.STATUS_DEAD: "Dead",
    psutil.STATUS_ZOMBIE: "Zombie",
    psutil.STATUS_RUNNING: "Running",
    psutil.STATUS_SLEEPING: "Sleep",
    psutil.STATUS_LOCKED: "Locked",
    psutil.STATUS_TRACING_STOP: "Tracing Stop",
    psutil.STATUS_DISK_SLEEP: "Disk Sleep",
    psutil.STATUS_WAKING: "Waking",
    psutil.STATUS_IDLE: "Idle",
    psutil.STATUS_WAITING: "Waiting"
}
    


class Runtime(object):
    def __init__(self, args):
        global statusTrans
        
        self.args = args
        self.status  = False
        self.type = 'SERVER'
        self.controllerOpt = False
        self.controller = False
        self.file =False
        self.remove = False
        self.removeOpt = False
        self.port = None
        self.ip = None
        self.defport = 9000
        self.defip = "127.0.0.1"
        self.serveropts = ['start', 'stop', 'restart', 'start_server', 'stop_server', 'start_forwarder']
        self.clientopts =['init', 'pack', 'remove', 'controller','list', 'edit']
        self.controlleractions =['init', 'restart','stop', 'clean']
        a = self.args
        if len(a) == 1:
          return self._help()
        self.secondopt =a[1]
        for _i in range(0, len(a)):
            i = a[_i]
            try:
                j = a[_i + 1]
            except:
                j = a[_i]
            try:
                k = a[_i + 2]
            except:
                k = a[_i]
                
            if i in ['-h', '--help']:
                self.help = True
            if i in ['-g', '--graceful']:
                self.graceful = True
            if i in ['-r', '--restart']:
                self.restart = True
            if i in ['-s', '--start']:
                self.start = True
            if i in ['-st', '--stop']:
                self.stop = True
            if i in ['-p', '--pack']:
                self.pack = True
                if j != i:
                  self.file = j
            if i in ['init', '--init'] and not self.controllerOpt:
                self.init = j 
            if i in ['remove', '--remove']:
                self.removeOpt = True
                if j != i:
                  self.remove = j
            if i in ['info', '--info']:
                self.info = j
            if i in ['-p', '--port']:
                self.port = j
            if i in ['--f', '--forward']:
                self.forward = True
            if i in ['--start_server']:
                self.start_server = True
            if i in ['--start_forwarder']:
                self.start_forward = True
            if i in ['-i', '--ip']:
                self.ip = j
            if i in ['settings']:
                self.settings = j 
            if i in ['init-stream']:
                self.initstream = j 
            if i in ['-d', '--daemon']:
                self.daemon = True
            if i in ['-l', '--list']:  
                self.list = True
            if i in ['-e', '--edit']:
                self.edit = True
                self.module = j
            if i in ['-v', '--version']:
                self.version = True
            if i  in ['--controller']:
                self.controllerOpt = True

                if j in self.controlleractions:
                  self.controllerAction = j 
                else:
                  self.controller = j
                  self.controllerAction =k
            if i in ['--start-ui', '--init-ui', '--ui']:
                self.ip = '127.0.0.1'
                self.port = 991
                self.ui = True
            if i in ['--status']:
                self.status = True
       

        if (self.ip and not self.port) or (self.port and not self.ip):
            print "When you supply --ip or --port  please supply both. oneline --ip {AN_IP} --port {A_PORT}"
            return
            
        if 'help' in dir(self):
            self._help()
            return

        self.perform()
  
    """ based on second option """
    def get_type(self):
      
      opt = self.secondopt
      withouthyphen = re.sub("\-\-", "", opt)
      if withouthyphen in self.serveropts:
        return "SERVER"
      return "CLIENT"

    def get_seed(self):
      
      if os.path.isfile(os.getcwd()+"/.oneline.seed"): 
        seedFile = open(os.getcwd() +"/.oneline.seed", "r").read()
        contents = re.findall("ONELINE_MODULE=(.*)", seedFile)
        if contents:
          return contents[0]
      return ""
    def get_mod_dir(self, modulename):
      if os.path.isfile("/usr/local/oneline/seeds/" +modulename):
        file =open("/usr/local/oneline/seeds/" +modulename).read()
        return file
      return False
      
    def perform(self):
        global statusTrans
        if 'settings' in dir(self):
            print "Loading default settings"
            if os.path.isfile("/usr/local/oneline/conf/{0}.conf".format(self.settings)):
                os.system("vim /usr/local/oneline/conf/{0}.conf".format(self.settings))
            else:
                os.system("vim /usr/local/oneline/conf/Main.conf")
            
        if 'ui' in dir(self):
            print "Attempting to start Oneline WebUI"

            if not self.ip or not self.port:
              print "Could not start the UI, you need to supply the --port and --ip options"
            else:
              SERVERS = dict(host='server.socket_host', port='server.socket_port', path='tools.staticdir.root')
              from oneline import ui
              cherrypy.config.update({ SERVERS['host']: self.ip,
              SERVERS['port']: self.port})

              SERVER = ui.OnelineUI(self.ip, self.port)
              cherrypy.quickstart(SERVER, '')

              print "Oneline UI running on {0}:{1}".format(self.ip, self.port)
             
        if 'edit' in dir(self):
          path = "/usr/local/oneline/modules/" +self.module + ".py"
          os.system("vim {0}".format(path))

        if 'list' in dir(self):
            
            print "List of all modules"
            modpath = "/usr/local/oneline/modules/"
            mods = os.listdir(modpath)
            for i in mods:
               if i == '__init__.py':
                    continue
               if len(re.findall(".*\.py$", i)) > 0:
                    print "Module: {0}".format(i)


        """ returns the status of oneline """
        """ where the status can be one of following """
        """ running, stopped, waiting """
        if 'status' in dir(self):
            pass
            

        """
        pack needs to get the current directory
        take the name provided to the command 
        and perform the needed symbolic links
        so
        oneline --pack "wikipedia-module" 
        looks at:

        wikipedia-module.html
        wikipedia-module.py
        wikipedia-module.conf
        """
        if 'pack' in dir(self):
           print("Packing Oneline Module.. please wait")
           cwd = os.getcwd()
           if self.file:
             module= self.file
           else:
             seed = self.get_seed()
           files = [module + ".py", module + ".html", module + ".conf"]
           for i in files:
              if not os.path.isfile(os.path.abspath(i)):
                print "Couldn\'t find: %s, exiting"  % (i)
                return

           ## now we can make 
           ## the symbolic
           ## links

           os.chdir("/usr/local/oneline/modules/")
           os.system("rm -rf ./" + (module + "*"))

           print "Making Symbolic links.."
           print "Linking: " + module+".py"
           os.system("ln -s " + os.path.abspath(cwd + "/" + (module+".py")))

           os.chdir("/usr/local/oneline/conf/")
           print "Linking: " + module + ".conf"
           os.system("ln -s " + os.path.abspath(cwd + "/" + (module + ".conf")))
         
           os.chdir("/usr/local/oneline/controllers/")
           print "Linking: "  + module + "_controller.py"
           os.system("ln -s " + os.path.abspath(cwd + "/" + (module + "_controller.py")))

           os.chdir(cwd)
           print "All done! you can use " + module + " as a Oneline module now"

        if 'initstream' in dir(self):
            f = open(os.path.abspath(self.initstream), "w+")
            os.system("ln -s /usr/local/oneline/streams/ {0}".format(self.initstream))
            print "Linked a new stream successfully!"
            print "Use like: stream://{0}".format(self.initstream)

        if self.get_type() == 'CLIENT':
            if 'init' in dir(self):
                print os.getcwd()
                """ initialize a new module """

                print "Starting an empty module.. "

                path_of_mod = os.getcwd()

                module_name = self.init


                """ navigate to conf, make a link """
                """ navigat to modules, make a link """

                path = os.getcwd()

                localpath = "/usr/local/oneline/"
                confpath = "/usr/local/oneline/conf/"
                modpath = "/usr/local/oneline/modules/"
                controllerpath = "/usr/local/oneline/controllers/"
                seedpath = "/usr/local/oneline/seeds/"
                os.chdir(confpath)
  
                
                if os.path.isfile(path_of_mod +"/" +".oneline.seed"):
                  print "You already have a module in this directory. Either remove it or choose another directory"
                  currentseed = open(path_of_mod +"/" + ".oneline.seed", "r").read()
                  matches = re.findall("ONELINE_MODULE=(.*)", currentseed)
                  if matches:
                    print "Module name is: %s" % (matches[0])
                  else:
                    print "Module is corrupt, please remove.."

                seed = open(path_of_mod +"/" + ".oneline.seed", "w+")
                seed.write("""ONELINE_MODULE={0}""".format(module_name))
                seed.close()
                print "Writing seed contents"
                seeddir = open(seedpath +"/" + module_name,"w+")
                seeddir.write(path_of_mod)

                f = open(path_of_mod + "/" + module_name + ".conf", "w+")

                print "Linking " + module_name + "'s config..."

                f.write("""
Config for {0} Module
===========================================

db_type = 'mysql'
db_table = 'example'
db_user = 'root'
db_pass = '__test__'
db_database = '__example_edit_me__'
db_host = '127.0.0.1'
ol_broadcast = 'singular'

==========================================
                """.format(module_name))

                os.system('sudo ln -s {0}/{1}.conf > /dev/null 2>&1 &'.format(path_of_mod, module_name))
                f.close()

                os.chdir(modpath)
                f = open(path_of_mod + "/" + module_name + ".py", "w+")

                f.write("""

##############################################################################
# Factory created module. Edit 
# as you like 
# @author Your Name
# @package Example Module
# @does Shows an example
##############################################################################

from oneline import ol

class {0}(ol.module):
    def start(self):
        self.pipeline = ol.stream()
    
    def receiver(self, message):
        self.pipeline.run(message)
""".format(module_name))
                print "Linking " + module_name + "'s module..."
                os.system('sudo ln -s {0}/{1}.py > /dev/null 2>&1 &'.format(path_of_mod, module_name))
                f.close()
                #os.chdir(controllerpath)
                f =  open(path_of_mod +"/" + module_name +  "_controller.py","w+")
                f.write("""
## example controller, controls your app           
import ol
def {0}_init(startserver=True,sql='{0}.sql'):
  print "starting new module named {0}"
  return ol.controller_init(startserver=startserver,sql=sql)
def {0}_stop(stopserver=True):
  print "Stopping server"
  return ol.controller_stop(stopserver=stopserver)
def {0}_clean(cleansql=True):
  print "Cleaning app contents"
  return ol.controller_clean(cleansql=cleansql)
def {0}_restart():
  print "Restarting application"
  return ol.controller_restart()
                """.format(module_name,module_name,module_name,module_name,module_name,module_name))
                f.close()
                os.chdir(controllerpath)
                print "Linking "  + module_name + "'s Controller" 
                os.system("sudo ln -s {0}/{1}_controller.py > /dev/null 2>&1 &".format(path_of_mod, module_name))

                f = open(path_of_mod + "/" + module_name + ".html", "w+")
                f.write("""
<!DOCTYPE html>
<!-- By default I run on public IP, to change, add flag: 'host' in Oneline.setup -->
<!-- -->
<html class="no-js" lang="en-US"> <!--<![endif]-->
    <head>
        <title>Oneline client -- demo</title>
    </head>
    <body>
      <h2>Hi, this is the data:</h2>
      <div id="fill">
      </div>
      <br />
      <small>
      If this is working it should be a JSON structure
      </small>
      <script type='application/javascript' src='./oneline.min.js'></script>
      <script type='application/javascript'>
      Oneline.setup({ 
            module: '{0}', 
            host: document.location.host, 
            freq: 1000
      });
      Oneline.echo({
           "limit": 10
      });
      Oneline.pipeline(function(res) {
          document.getElementById('fill').innerHTML = JSON.stringify(res.data);
      }).run();
    </script>
  </body>
        </html>
                """.replace("{0}", module_name))
                f.close()

                """ move a javascript client relative to this directory. """
                """ if we already have one, skip """

                if not os.path.isfile(path_of_mod + "/oneline.min.js"):
                    print "copying javascript client to this directory.."
                    shutil.copy(localpath + "oneline.min.js", path_of_mod + "/oneline.min.js")

                
                print "All done! you can now start writing code"
                #os.system("sudo ln -s " + 

            if self.removeOpt:
             
                if not self.remove:    
                  module = self.get_seed()
                else:
                  module = self.remove
                moddir =self.get_mod_dir(module)
              
                print "Permantly deleting module {0}".format(module)

                try: 
                    os.remove(moddir + "/" + module + '.py')  
                    os.remove(moddir + "/"  + module + '.conf')    
                    os.remove(moddir + "/" + module + '.html')    
                    os.remove(moddir + "/" + module  + "_controller.py")
                    os.remove(moddir +"/"  +".oneline.seed")
                    os.remove(moddir + "/" + "oneline.min.js")

                    os.remove("/usr/local/oneline/modules/" + module + '.py')
                    os.remove("/usr/local/oneline/conf/" + module  + '.conf')
                    os.remove("/usr/local/oneline/controllers/" + module + "_controller.py")
                    os.remove("/usr/local/oneline/seeds/" + module)
            
                    print "Done all files for: {0} module have been removed".format(module)
                except:
                    print "One or more files could not be deleted.. please make sure the files are on path.."
            if self.controllerOpt:
                if self.controller:
                  module = self.controller
                else:
                  module = self.get_seed() 

                sys.path.append("/usr/local/oneline/controllers/")
                moduleFile = __import__(module + "_controller")

                fn = getattr(moduleFile, module +"_" + self.controllerAction)
                knownControllers =  ['init', 'clean', 'restart', 'stop']
                if fn:
                  status = fn()
                  _OL_CURRENT_APP = module
                  if status:
                    print module + " was " + self.controllerAction + " !"
                  else:
                    print "Could not " + self.controllerAction
                else:
                  print "You have either not implemented this or it is not a valid controller function.. " + " please use: " + self.controlleractions.join(",")
          
 
            if 'info' in dir(self):
                if self.info:
                  module = self.info
                else:
                  module =self.get_seed()
                print "Info for module: {0}".format(module)
                print "-------------------------------------------"
                f = open("/usr/local/oneline/modules/" + module + ".py").read()

                p = re.findall(r"package(.*)", f)
                if len(p) > 0:
                    print "Package name: {0}".format(p[0])

                a = re.findall("author(.*)", f)
                if len(a) > 0:
                    print "Author of package: {0}".format(p[0])

                p = re.findall("does(.*)", f)
                if len(p) > 0:
                    print "Does: {0}".format(p[0])
            
            if 'version' in dir(self):
                print "You are running Oneline v " + self.get_version_string()


        if 'forward' in dir(self):
          from oneline import forward

        if self.get_type() == 'SERVER':
            if 'start' in dir(self):
                """ start as daemon or regular? """
                os.system("oneline --start_forwarder > /dev/null 2>&1 &")
                #os.system("oneline --start_server")
                status = ol.server(self.ip,self.port).start()
                self.status = status
                """ start the forwarder as well """
                #from oneline import forward
                #start_forwarder(self.ip, (self.port + 1))
            if 'start_server' in dir(self):
                if self.port and self.ip:
                  print "Starting oneline-websockets on port, ip: " + str(self.port) + ", " + self.ip
                else:
                  print "Starting oneline-websockets on port, ip: " + str(self.defport) + ", " + self.defip
                self.status = ol.server(self.ip, self.port).start()
                 
            if 'start_forward' in dir(self): 
                
                from oneline import forward
                if self.port and self.ip:
                  print "Starting oneline-xhr forwarder on port, ip: " + str(self.port+1) + ", " + self.ip
                  forward.start_forwarder(self.ip, (self.port+1))
                else:
                  print "Starting oneline-xhr forwarder on port, ip: " +str(self.defport+1)+", "  + self.defip
                  forward.start_forwarder(self.defip, (self.defport+1))

            if 'stop' in dir(self):
                
                if os.path.isfile("/usr/local/oneline/socket/oneline.pid.txt"):
                  try:
                    processId = int(open("/usr/local/oneline/socket/oneline.pid.txt").read())
                    process = psutil.Process(processId)
                    process.kill()
                  #try:
                    time.sleep(3)
                    process = psutil.Process(processId)
                    print "Could not stop Oneline server"
                    print "status is " +  statusTrans[process.status()]
                      
                  except:
                    print "Stopped oneline"
                    
                    if os.path.isfile("/usr/local/oneline/socket/oneline.forwarder.pid.txt"):
                      processIdForwarder = int(open("/usr/local/oneline/socket/oneline.forwarder.pid.txt").read())
                      processOfForwarder = psutil.Process(processIdForwarder)
                      try: 
                        time.sleep(3) 
                        processOfForwarder = psutil.Process(processIdForwarder)
                        print "Could not stop process for oneline-forwarder"
                        status = statusTrans[processOfForwarder.status()]
                        print "Status is: " + status
                      except:
                        print "Stopped oneline forwarder"
                else:
                  print "Oneline is not running.."
    
                ## todo  needs to check
                ## if the server was stopped
            if 'restart' in dir(self):
                """ TODO add graceful shutdown """
                print "Stopping server.."
                #os.system("pkill -f 'python /usr/bin/olcli.py'")
                #os.system("pkill -f '/usr/bin/python /usr/bin/olcli.py'")
                #os.system("oneline --start")
                r1 = Runtime(['olcli.py', '--stop'])

                print "Starting server"
                r2 = Runtime(['olcli.py', '--start'])
                self.status = r2.status
                #time.sleep(1)
                #self.status = ol.server(self.ip, int(self.port)).start()

                #quit()
 
                #exit()
            if 'graceful' in dir(self):
                print "Stopping Oneline server"
                os.system("pkill -f 'python ./ol.py --server'")
                os.system("pkill -f '/usr/bin/python /usr/bin/olcli.py'")
                os.system("pkill -f 'python /usr/bin/ol.py --server'")
                exit()



    def get_version_string(self):
        import pkg_resources
        return pkg_resources.get_distribution("oneline").version

    def _help(self):
        print """
usage: oneline [options] required_input required_input2
options:
-c, --client     Run a command as a client
-s, --server     Initiate a server
-v, --version    Get the verison of Oneline


CLIENT SPECIFIC
init, --init     Create a new module
init-stream      Link a stream to the home of streams (makes it accessible via: stream://)
-i, --info       Info on a module
-r, --remove     Permantly delete a module  
-l, --list       List of all available modules
-e, --edit       Edit a module by name
-p, --pack       Pack an existant module for use in oneline
--controller Control your oneline application
    options:
      oneline --controller stop
      oneline --controller start
      oneline --controller restart



SERVER SPECIFIC
-g, --graceful  Perform a graceful shutdown
-re, --restart  Restart the server
-st, --start    Start the server
-sp, --stop     Force a shutdown
-st, --status   Is the server running or stopped
-ip, --ip       Add custom ip to init
-port, --port   Add custom port to init

UI SPECIFIC
--init-ui      starts the oneline ui at the default port
"""

def restartserver():
    runtime = Runtime(['olcli.py', '--restart'])
    return runtime.status
    
def startserver():
    runtime =Runtime(['olcli.py','--start_server'])
    return runtime.status
  
def stop():
    runtime = Runtime(['olcli.py','--stop'])
    return runtime.status




if __name__ == '__main__':
    Runtime(sys.argv)
