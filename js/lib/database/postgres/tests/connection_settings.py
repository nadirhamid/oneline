db_joy_connect = {
        "host": "joy",
        "user": "pg8000-test",
        "database": "pg8000-test",
        "password": "pg8000-test",
        "socket_timeout": 5,
        "ssl": False,
        }

db_local_connect = {
        "unix_sock": "/tmp/.s.PGSQL.5432",
        "user": "mfenniak"
        }

db_local_win_connect = {
        "host": "localhost",
        "user": "postgres",
        "password": "pg",
        "database": "pg8000"
        }

db_oracledev2_connect = {
        "host": "oracledev2",
        "user": "mfenniak",
        "password": "password",
        "database": "mfenniak"
        }

import getpass
import os
import sys

if "PG8000_TEST" in os.environ:
    db_connect = eval(os.environ["PG8000_TEST"])
else:
    db_connect = {}
    
    # get current username
    db_connect['user'] = getpass.getuser()
    db_connect['database'] = getpass.getuser()

    # discover installer postgresql server:
    # test common unix sockets:
    if sys.platform in ('linux2', ):
        for path in ("/tmp/.s.PGSQL.5432", "/var/run/postgresql/.s.PGSQL.5432"):
            if os.path.exists(path):
                db_connect['unix_sock'] = path
                print "Unix socket found:", path
                break

    if not 'unix_sock' in db_connect:
        db_connect["host"] = "localhost"

