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

#######################################################################


########################################################################
## Finally start  
## the server 
########################################################################

cd $ONELINE_BASE/bin/
./onelined --start