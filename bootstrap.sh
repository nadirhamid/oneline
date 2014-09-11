#########################################################################
## Oneline baseline setup this will install all the dependencies for
## the project. To run in conjunction with other databases
## please documentation at:  

#########################################################################
## This scaffolding model makes your app work on Google App Engine too
## File is released under public domain and you can use without limitations
#########################################################################

#########################################################################
## Setup all the Database drivers and third party
## libraries.
########################################################################

ONELINE_BASE=$(pwd)
CHERRYPY_LATEST='https://pypi.python.org/packages/source/C/CherryPy/CherryPy-3.2.4.tar.gz#md5=e2c8455e15c39c9d60e0393c264a4d16'
WS4PY_LATEST='https://pypi.python.org/packages/source/w/ws4py/ws4py-0.3.4.tar.gz#md5=6b47e33cbd13f5c134b04f2a44a480ad'
SETUP_TOOLS='https://bitbucket.org/pypa/setuptools/raw/bootstrap/ez_setup.py'
rm -rf $ONELINE_BASE/lib/cherrypy
rm -rf $ONELINE_BASE/lib/websocket

cd $ONELINE_BASE/lib
wget $CHERRYPY_LATEST
tar xvf CherryPy*.tar.gz
rm CherryPy*.tar.gz
mv CherryPy* cherrypy
chmod 755 cherrypy

wget $WS4PY_LATEST
tar xvf ws4py*.tar.gz
rm ws4py*.tar.gz
mv ws4py* websocket

wget $SETUP_TOOLS -O - | sudo python
rm $ONELINE_BASE/lib/setuptools*.zip

cd $ONELINE_BASE/lib/bson/
python ./setup.py build
python ./setup.py install
cd $ONELINE_BASE/lib/database/mysql-connector/
python ./setup.py build
python ./setup.py install
cd $ONELINE_BASE/lib/database/postgres/
python ./setup.py build
python ./setup.py install 
cd $ONELINE_BASE/lib/database/mongodb/
python ./setup.py build
python ./setup.py install
cd $ONELINE_BASE/lib/websocket/
python ./setup.py build
python ./setup.py install
cd $ONELINE_BASE/lib/mock/
python ./setup.py build
python ./setup.py install
cd $ONELINE_BASE/lib/memcache/
python ./setup.py build
python ./setup.py install
cd $ONELINE_BASE/lib/cherrypy 
python ./setup.py build 
python ./setup.py install

########################################################################
## Setup Oneline  
## Assuming the location is at $ONELINE_BASE/src/
########################################################################

cd $ONELINE_BASE/src/
python ./setup.py build
python ./setup.py install

# some cleanup before initial run
cd $ONELINE_BASE/logs/
rm -f *.log

cd $ONELINE_BASE/modules/
rm -f *.pyc

cd $ONELINE_BASE/socket/
rm -f *.pid


########################################################################
## Finally start  
## the server 
########################################################################
cd $ONELINE_BASE
export ONELINE_BASE=$(pwd)

cd $ONELINE_BASE/bin/
rm -f /usr/bin/onelined
cp ./onelined /usr/bin/
./onelined --start