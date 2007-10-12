#!/usr/bin/python
# ========================================================================
# Copyright (c) 2007, Metaweb Technologies, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above
#       copyright notice, this list of conditions and the following
#       disclaimer in the documentation and/or other materials provided
#       with the distribution.
# 
# THIS SOFTWARE IS PROVIDED BY METAWEB TECHNOLOGIES ``AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL METAWEB TECHNOLOGIES BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN
# IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# ========================================================================


import unittest
import sys
from freebase.api import HTTPMetawebSession


USERNAME = 'username'
PASSWORD = 'password'
API_HOST = 'sandbox.freebase.com'
TEST_QUERY = {'id': 'null', 'name': 'Sting'}

class TestFreebase(unittest.TestCase):
    
    def test_login(self):
        mss = HTTPMetawebSession(API_HOST, username=USERNAME,
                                 password=PASSWORD)
        mss.login()

        # check mss._cookies?

    def test_read(self):
        query = {'type':'/music/artist','id':[{}],'name':'Sting', 'album':[{}]}

        mss = HTTPMetawebSession(API_HOST)

        result = mss.mqlread(query)
        self.assertNotEqual(None, result)
        self.assert_(result.has_key('id'))
        self.assert_(result.has_key('type'))
        self.assert_(result.has_key('name'))
        self.assert_(result.has_key('album'))
        self.assertEqual([].__class__, result['album'].__class__)
        self.assert_( result['album'].__len__() > 0)
        self.assertEqual( 'Sting', result['name'])
        self.assertEqual( '/guid/9202a8c04000641f8000000000092a01', result['id'][0]['value'], str(result['id']))
   
    def test_write(self):
        read_query = {'type':'/music/artist','name':'Yanni\'s Cousin Tom', 'id':{}}
        mss = HTTPMetawebSession(API_HOST, username=USERNAME,
                                 password=PASSWORD)
        result = mss.mqlread(read_query)
        self.assertEqual(None, result)

        write_query = {'create':'unless_exists', 'type':'/music/artist','name':'Yanni'}

        mss.login()
        write_result = mss.mqlwrite(write_query)
        self.assertNotEqual(None, write_result)
        self.assert_(write_result.has_key('create'))
        self.assert_(write_result.has_key('type'))
        self.assert_(write_result.has_key('name'))
        self.assertEqual('existed', write_result['create'])
        self.assertEqual('Yanni', write_result['name'])
        self.assertEqual('/music/artist', write_result['type'])
   
if __name__ == '__main__':
  unittest.main()
  
