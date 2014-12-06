# -*- coding: utf-8 -*-

#########################################################################
## Oneline baseline setup this install all the dependancies for
## the project. To run in conjection with

#########################################################################
## This scaffolding model makes your app work on Google App Engine too
## File is released under public domain and you can use without limitations
#########################################################################

import os, os.path
from glob import iglob
import sys

try:
	from setuptools import setup
except ImportError:
	from distutils.core import setup

from distutils.command.build_py import build_py

class buildsetup(build_py):
    def find_package_modules(self, package, package_dir):
        """
        Lookup modules to be built before install. Because we
        only use a single source distribution for Python 2 and 3,
        we want to avoid specific modules to be built and deployed
        on Python 2.x. By overriding this method, we filter out
        those modules before distutils process them.

        This is in reference to issue #123.
        """
        modules = build_py.find_package_modules(self, package, package_dir)
        amended_modules = []
        for (package_, module, module_file) in modules:
            if sys.version_info < (3,):
                if module in ['async_websocket', 'tulipserver']:
                    continue
            amended_modules.append((package_, module, module_file))

        return amended_modules
 

setup(name="oneline",
      version="0.2.6",
      description="",
      maintainer="Nadir Hamid",
      maintainer_email="matrix.nad@gmail.com",
      url="https://",
      download_url = "https://pypi.python.org/pypi/",
      license="MIT",
      long_description="",
      packages=["oneline"],
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'Framework :: CherryPy',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: BSD License',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.3',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: Implementation :: CPython',
          'Programming Language :: Python :: Implementation :: PyPy',
          'Topic :: Communications',
          'Topic :: Internet :: WWW/HTTP :: WSGI :: Middleware',
          'Topic :: Internet :: WWW/HTTP :: WSGI :: Server',
          'Topic :: Software Development :: Libraries :: Python Modules'
      ],
      cmdclass=dict(build_py=buildsetup))


fpath = '/usr/bin/'
lpath = '/usr/local/'
ffpath = '/usr/'
path = os.getcwd()
bpath = os.path.abspath('../')
bin_path = os.path.abspath('../bin/')
mod_path = os.path.abspath('../modules/')
conf_path = os.path.abspath('../conf/')
stream_path = os.path.abspath('../streams/')
socket_path = os.path.abspath('../socket/')
logs_path = os.path.abspath('../logs/')
etc_path = os.path.abspath('../etc/')
js_path = os.path.abspath('../js/')
os.chdir(fpath)
os.system('sudo ln -s ' + path + "/oneline/ol.py > /dev/null 2>&1 &")
os.system('sudo ln -s ' + path + "/oneline/dal.py > /dev/null 2>&1 &")
os.system('sudo ln -s ' + path + "/oneline/odict.py > /dev/null 2>&1 &")
os.system('sudo ln -s ' + path + "/oneline/oneline-cli.py > /dev/null 2>&1 &")
os.system('sudo ln -s ' + path + "/oneline/oneline-updater.py > /dev/null 2>&1 &")
os.system('sudo ln -s ' + bin_path + "/oneline > /dev/null 2>&1 &")
os.system('sudo ln -s ' + bin_path + "/oneline.pid.txt > /dev/null 2>&1 &")
os.system('sudo ln -s ' + bin_path + "/onelined > /dev/null 2>&1 &")
os.system('sudo ln -s ' + bin_path + "/oneline-client > /dev/null 2>&1 &")
os.system('sudo ln -s ' + bin_path + "/oneline-server > /dev/null 2>&1 &")

""" link the modules and configs """
os.system('mkdir ' + lpath + "oneline/")
os.chdir(lpath + "oneline/")
os.system("rm -rf " + lpath + "oneline/*")
os.system('sudo ln -s ' + mod_path + " > /dev/null 2>&1 &")
os.system('sudo ln -s ' + mod_path + "/* > /dev/null 2>&1 &")
os.system('sudo ln -s ' + conf_path + " > /dev/null 2>&1 &")
os.system('sudo ln -s ' + conf_path + "/* > /dev/null 2>&1 &")
os.system('sudo ln -s ' + stream_path + " > /dev/null 2>&1 &")
os.system('sudo ln -s ' + stream_path + "/* > /dev/null 2>&1 &")
os.system('sudo ln -s ' + logs_path + "/ > /dev/null 2>&1 &")
os.system('sudo ln -s ' + logs_path + "/* > /dev/null 2>&1 &")
os.system('sudo ln -s ' + socket_path + " > /dev/null 2>&1 &")
os.system('sudo ln -s ' + etc_path + " > /dev/null 2>&1 &")
os.system('sudo ln -s ' + js_path +  "/oneline.min.js > /dev/null 2>&1 &")

os.chdir(path)
os.system('sudo cp ' + bpath + '/service /etc/init.d/oneline > /dev/null 2>&1 &')
os.system('sudo chkconfig --add oneline')
os.system('sudo chkconfig oneline on')

os.chdir(path)

print """
Oneline binaries stored in: {0} \n
Oneline modules and configs stored in {1} \n
""".format(fpath, lpath + "oneline/")


print """Available oneline commands: \n
oneline (same as server)
oneline-server
oneline-client
"""
