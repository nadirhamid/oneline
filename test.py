import os
import re
dirs = os.listdir("./conf")
for i in dirs:
  if re.findall(".conf", i):
    os.system("git rm -rf --cached {0}".format(i))

