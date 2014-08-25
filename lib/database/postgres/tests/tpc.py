#!/usr/bin/env python
# simple test cases for two phase commit extensions for postgresql 
# (originally for psycopg2 -pyreplica/alerce-, now for pg8000)
#
# Copyright (C) 2008-2011 Mariano Reingart <reingart@gmail.com>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
# * Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
# * The name of the author may not be used to endorse or promote products
# derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

# REMEMBER enable TPC on postgresql.conf: 
# max_prepared_transactions = 10

import unittest

import pg8000
from pg8000 import ProgrammingError
from .connection_settings import db_connect


class TwoPhaseTests(unittest.TestCase):

    def setUp(self):
        self.connect()
        # close current transaction and start auto-commit mode for CREATE TABLE
        self.conn.autocommit = True
        self.conn.rollback()
        # create permanent test table
        self.curs.execute("CREATE TABLE IF NOT EXISTS tpc_test_table_1 ( "
                          "      data TEXT "
                          ");")
        self.conn.autocommit = False
        self.clean()
        # set pg8000 default auto-commit mode
        self.conn.autocommit = False
        
    def tearDown(self):
        self.clean()
        self.conn.close()
            
    def connect(self):    
        dbapi = pg8000.DBAPI
        gid = 'test-gid-1234'
        self.conn = dbapi.connect(**db_connect)
        self.xid = self.conn.xid(0,gid,'')
        self.curs = self.conn.cursor()

    def clean(self):
        self.assertEqual(self.conn.autocommit, False) 
        # clean table 1
        self.conn.autocommit = True
        # rollback any prepared transaction
        err = False
        for xid in self.conn.tpc_recover():
            print "rolling back xid[1]"
            self.curs.execute("ROLLBACK PREPARED '%s'" % (xid[1],))
            err=True
        if err:
            raise RuntimeError("Unhandled prepared TPC transaction")
        self.curs.execute("DELETE FROM table1")
       
    def insert(self):
        self.curs.execute("INSERT INTO table1 (data) VALUES (%s)", ('1234', ))
        
    def rowcount(self):
        self.curs.execute("SELECT * FROM table1 ")
        return self.curs.rowcount
        
    def test_one_phase_commit(self):
        "Test to commit a one phase transaction"
        self.conn.tpc_begin(self.xid)
        self.insert()
        self.conn.tpc_commit()
        self.assertEqual(self.rowcount(), 1) 
        
    def test_one_phase_rollback(self):
        "Test to rollback a one phase transaction"
        self.conn.tpc_begin(self.xid)
        self.insert()
        self.conn.tpc_rollback()
        self.assertEqual(self.rowcount(), 0) 

    def test_two_phase_commit(self):
        "Test to commit a complete two phase transaction"
        self.conn.tpc_begin(self.xid)
        self.insert()
        self.conn.tpc_prepare()
        self.conn.tpc_commit()
        self.assertEqual(self.rowcount(), 1) 

    def test_two_phase_rollback(self):
        "Test to rollback a complete two phase transaction"
        self.conn.tpc_begin(self.xid)
        self.conn.tpc_prepare()
        self.conn.tpc_rollback()
        self.assertEqual(self.rowcount(), 0)
        
    def test_recovered_commit(self):
        "Test to commit a recovered transaction"
        self.conn.tpc_begin(self.xid)
        self.insert()
        self.conn.tpc_prepare()
        self.conn.close()
        self.connect() # reconnect
        self.assertEqual(self.conn.tpc_recover(), [self.xid])
        self.conn.tpc_commit(self.xid)
        self.assertEqual(self.rowcount(), 1) 

    def test_recovered_rollback(self):
        "Test to rollback a recovered transaction"
        self.conn.tpc_begin(self.xid)
        self.insert()
        self.conn.tpc_prepare()
        self.conn.close()
        self.connect() # reconnect
        self.assertEqual(self.conn.tpc_recover(), [self.xid])
        self.conn.tpc_rollback(self.xid)
        self.assertEqual(self.rowcount(), 0) 

    def test_single_phase_commit(self):
        "Test to commit a single phase (normal) transaction"
        self.insert()
        self.conn.commit()
        self.assertEqual(self.rowcount(), 1) 

    def test_single_phase_rollback(self):
        "Test to rollback a single phase (normal) transaction"
        self.insert()
        self.conn.rollback()
        self.assertEqual(self.rowcount(), 0)
        
    def test_dbapi20_tpc(self):
        "Test basic dbapi 2.0 conformance"
        self.assertEqual(len(self.conn.tpc_recover()),0)
    
        # tpc_commit outside tpc transaction 
        self.assertRaises(ProgrammingError, self.conn.tpc_commit)

        # commit or rollback inside tpc transaction 
        self.conn.tpc_begin(self.xid)
        self.assertRaises(ProgrammingError, self.conn.commit)
        self.assertRaises(ProgrammingError, self.conn.rollback)
        self.conn.tpc_rollback()

        # transaction not prepared
        self.assertRaises(ProgrammingError, self.conn.tpc_commit,self.xid)
        self.assertRaises(ProgrammingError, self.conn.tpc_rollback,self.xid)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TwoPhaseTests)
    #suite.debug()
    unittest.TextTestRunner(verbosity=2).run(suite)


