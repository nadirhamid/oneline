"""
Detect any changes to the oneline configuration
and restart accordingly.

Changes include new files, updates, and deletes
"""

import hashlib
import subprocess
import platform
import os
import re
import ctypes
import time

def kill(pid):
    """kill function for Win32"""
    kernel32 = ctypes.windll.kernel32
    handle = kernel32.OpenProcess(1, 0, pid)
    return (0 != kernel32.TerminateProcess(handle, 0))

class update(object):
	def start(self):
		prefix = ''
		salt = ''
		_dir = os.getcwd()
		ctimes = dict() 

		if os.path.exists('../../modules/'):
			prefix = '../../'
			os.chdir('../../modules')
			files = os.listdir('./')
		elif os.path.exists('../modules/'):
			prefix = '../'
			os.chdir('../modules')
			files = os.listdir('./')		
		elif os.path.exists('./modules/'):
			prefix = './'
			os.chdir('./modules')
			files = os.listdir('./')
		else:
			prefix = '../../'
			os.chdir('../../modules')
			files = os.listdir('./')

		for i in files:
			if len(re.findall('\.pyc$', i)) > 0:
				continue

			if not len(re.findall('\.py$', i)) > 0:
				continue

			salt += '_' + i

			ctimes[i] = os.path.getmtime(i)

		salt = hashlib.md5(salt).hexdigest()

		while True:

			os.chdir(_dir)

			if os.path.exists('../../modules/'):
				prefix = '../../'
				os.chdir('../../modules')
				files = os.listdir('./')
			elif os.path.exists('../modules/'):
				prefix = '../'
				os.chdir('../modules')
				files = os.listdir('./')		
			elif os.path.exists('./modules/'):
				prefix = './'
				os.chdir('./modules')
				files = os.listdir('./')
			else:
				prefix = '../../'
				os.chdir('../../modules')
				files = os.listdir('./')

			newsalt = ''
			restart = False

			for i in files:
				if len(re.findall('\.pyc$', i)) > 0:
					continue

				if not len(re.findall('\.py$', i)) > 0:
					continue

				try:
					if not i in ctimes.keys():
						ctimes[i] = os.path.getmtime(i)
						restart = True

					if not ctimes[i] == os.path.getmtime(i):
						restart = True
						ctimes[i] = os.path.getmtime(i)
				except:
					restart = True
					ctimes[i] = time.time()


				newsalt += '_' + i

			newsalt = hashlib.md5(newsalt).hexdigest()

			os.chdir(_dir)

			if newsalt != salt or restart:
				print 'oneline config has changed'

				if os.path.exists('../../socket/'):
					prefix = '../../'
					os.chdir('../../socket')
				elif os.path.exists('../socket/'):
					prefix = '../'
					os.chdir('../socket')
				elif os.path.exists('./socket/'):
					prefix = './'
					os.chdir('./socket')
				else:
					prefix = '../../'
					os.chdir('../../socket')

				try:
					pid = open('./oneline.pid.txt', 'r+').read()

					if len(re.findall(r'Linux|Cygwin|Mac', platform.system(), re.IGNORECASE)) > 0:
						os.system("kill " + str(pid))
					else:
						kill(pid)

					subprocess.Popen(["python", prefix + "server.py"])
				except:
					print "Couldn't stop process"

				restart = False
				salt = newsalt

			time.sleep(1)


u = update()
u.start()
