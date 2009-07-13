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
import sys, logging
import freebase
import random

import getlogindetails

from freebase.api import HTTPMetawebSession, MetawebError


USERNAME = 'username'
PASSWORD = 'password'
API_HOST = 'http://sandbox-freebase.com'
TEST_QUERY = {'id': 'null', 'name': 'Sting'}

s = HTTPMetawebSession(API_HOST)

if USERNAME == "username" and PASSWORD == "password":
    USERNAME, PASSWORD = getlogindetails.main()

s.login(USERNAME, PASSWORD)

class TestFreebase(unittest.TestCase):
    def test_freebase_dot_login_logout(self):
        freebase.login(username=USERNAME, password=PASSWORD)
        self.assertNotEqual(freebase.user_info(), None)
        self.assertEqual(freebase.loggedin(), True)
        freebase.logout()
        self.assertRaises(MetawebError, freebase.user_info)
        self.assertEqual(freebase.loggedin(), False)
    
    def test_login_logout(self):
        mss = HTTPMetawebSession(API_HOST, username=USERNAME,
                                 password=PASSWORD)
        mss.login()
        
        user_info = mss.user_info()
        self.assertNotEqual(None, user_info)
        self.assertEqual(user_info.code, "/api/status/ok")
        self.assertEqual(mss.loggedin(), True)
        
        mss.logout()
        self.assertRaises(MetawebError, mss.user_info)
        self.assertEqual(mss.loggedin(), False)

    
    def test_freebase_dot_read(self):
        query = {'type':'/music/artist','guid':[{}],'name':'Sting', 'album':[{}]}
        
        result = freebase.mqlread(query)
        
        self.assertNotEqual(None, result)
        self.assert_(result.has_key('guid'))
        self.assert_(result.has_key('type'))
        self.assert_(result.has_key('name'))
        self.assert_(result.has_key('album'))
        self.assertEqual(type([]), type(result['album']))
        self.assert_(len(result['album']) > 0)
        self.assertEqual( 'Sting', result['name'])
        self.assertEqual('#9202a8c04000641f8000000000092a01', result['guid'][0]['value'])
    
    def test_freebase_dot_write(self):
        read_query = {'type':'/music/artist','name':'Yanni\'s Cousin Tom', 'id':{}}
        
        freebase.sandbox.login(username=USERNAME, password=PASSWORD)
        result = freebase.sandbox.mqlread(read_query)
        self.assertEqual(None, result)
        
        write_query = {'create':'unless_exists', 'type':'/music/artist','name':'Yanni'}
        
        write_result = freebase.sandbox.mqlwrite(write_query)
        self.assertNotEqual(None, write_result)
        self.assert_(write_result.has_key('create'))
        self.assert_(write_result.has_key('type'))
        self.assert_(write_result.has_key('name'))
        self.assertEqual('existed', write_result['create'])
        self.assertEqual('Yanni', write_result['name'])
        self.assertEqual('/music/artist', write_result['type'])
    
    def test_read(self):
        query = {'type':'/music/artist','guid':[{}],'name':'Sting', 'album':[{}]}
        
        mss = HTTPMetawebSession(API_HOST)
        
        result = mss.mqlread(query)
        
        self.assertNotEqual(None, result)
        self.assert_(result.has_key('guid'))
        self.assert_(result.has_key('type'))
        self.assert_(result.has_key('name'))
        self.assert_(result.has_key('album'))
        self.assertEqual(type([]), type(result['album']))
        self.assert_(len(result['album']) > 0)
        self.assertEqual( 'Sting', result['name'])
        self.assertEqual('#9202a8c04000641f8000000000092a01', result['guid'][0]['value'])
   
    
    def test_mqlreaditer(self):
        filmq = [{'id': None,
                    'initial_release_date>=': '2009',
                    'name': None,
                    'type': '/film/film'
                    }]
        r0 = freebase.mqlreaditer(filmq)
        r1 = freebase.mqlreaditer(filmq[0]) # The difference between [{}] and []. mqlreaditer should be able to handle both
        self.assertNotEqual(r0, None)
        self.assertEqual([a for a in r0], [b for b in r1])
        
        # and let's test it for mqlread, just in case
        # actually, for mqlread, it must be [{}], because there are lots of elements
        m0 = freebase.mqlread(filmq)
        m1 = lambda : freebase.mqlread(filmq[0])
        self.assertRaises(MetawebError, m1)
        self.assertNotEqual(m0, None)
         
   
    def test_ridiculously_long_write(self):
        
        q = [{
         "id":None,
         "id|=":["/guid/9202a8c04000641f80000000000" + str(a) for a in range(10000,10320)]
        }]

        self.assert_(len(str(q)), 1024)
        self.assertNotEqual(len(freebase.mqlread(q)), 0)

    
    def test_write(self):
        read_query = {'type':'/music/artist','name':'Yanni\'s Cousin Tom', 'id':{}}
        mss = HTTPMetawebSession(API_HOST, username=USERNAME, password=PASSWORD)
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
    
    def test_trans_blurb(self):
        kurt = "/en/kurt_vonnegut"
        
        blurb = freebase.blurb(kurt)
        self.assert_(blurb.startswith("Kurt Vonnegut"))
        self.assertNotEqual(len(blurb), 0)
        
        blurb14 = freebase.blurb(kurt, maxlength=14)
        blurb57 = freebase.blurb(kurt, maxlength=57)
        self.assertNotEqual(len(blurb14), len(blurb57))
        
        blurbpar = freebase.blurb(kurt, break_paragraphs=True, maxlength=20000)
        blurbnopar = freebase.blurb(kurt, break_paragraphs=False, maxlength=20000)
        # self.assertNotEqual(blurbpar, blurbnopar) this doesn't work unless I get a good example
        # of an article with paragraphs.
    
    def test_trans_raw(self):
        kurt = "/en/kurt_vonnegut"
        
        self.assertRaises(MetawebError, lambda: freebase.raw(kurt))
        
        r = freebase.mqlread({"id":kurt, "/common/topic/article":[{"id":None, "optional":True, "limit":1}]})
        raw = freebase.raw(r["/common/topic/article"][0].id)
        self.assertNotEqual(len(raw), 0)

        # trans should also work
        trans = freebase.trans(r["/common/topic/article"][0].id)
        self.assertEqual(trans, raw)
    
    def test_unsafe(self):
        kurt = "/en/kurt_vonnegut"
        
        self.assertRaises(MetawebError, lambda: freebase.unsafe(kurt))
        
        r = freebase.mqlread({"id":kurt, "/common/topic/article":[{"id":None, "optional":True, "limit":1}]})
        unsafe = freebase.unsafe(r["/common/topic/article"][0].id)
        self.assertNotEqual(len(unsafe), 0)
        
        # we need an example of getting unsafe data
        # ...
        
    
    def test_trans_image_thumb(self):
        kurt = "/en/kurt_vonnegut"
        
        r = freebase.mqlread({"id":kurt, "/common/topic/image":[{"id":None, "optional":True, "limit":1}]})
        imageid = r["/common/topic/image"][0].id
        rawimage = freebase.raw(imageid)
        
        thumbedimage = freebase.image_thumb(imageid, maxheight=99)
        self.assertNotEqual(rawimage, thumbedimage)
    
    def test_upload(self):
        my_text = "Kurt Vonnegut was an author! " + str(random.random())
        
        freebase.sandbox.login(USERNAME, PASSWORD)
        response = freebase.sandbox.upload(my_text, "text/plain")
        
        self.assertEqual(freebase.sandbox.raw(response.id), my_text)
        # since it's text/plain, blurb should also be equal
        self.assertEqual(freebase.sandbox.blurb(response.id), my_text)
    
        
    def is_kurt_there(self, results):
        for result in results:
            if result.name == "Kurt Vonnegut":
                return True
        return False
    
    
    def test_search(self):
        r0 = freebase.search("Kurt V")
        self.assertEqual(self.is_kurt_there(r0), True)
        
        r1 = freebase.search("Kurt V", type=["/location/citytown"])
        self.assertEqual(self.is_kurt_there(r1), False)
        
        r2 = freebase.search("Kurt V", type=["/location/citytown", "/music/artist"])
        self.assertEqual(self.is_kurt_there(r2), False)
        
        self.assertNotEqual(len(r0), len(r1))
        self.assertNotEqual(len(r0), len(r2))
        self.assertNotEqual(len(r1), len(r2))
    
    def test_touch(self):
        # this one's hard to test... let's just make sure it works.
        freebase.touch()

    
    def test_geosearch(self):
        
        self.assertRaises(Exception, freebase.geosearch)
        
        r0 = freebase.geosearch(location="/en/california")
        self.assertNotEqual(len(r0), 0)
        
        json = freebase.geosearch(location="/en/san_francisco", format="json")
        kml = freebase.geosearch(location="/en/san_francisco", format="kml")
        self.assertNotEqual(json, kml)
        
    
    def test_uri_submit(self):
        # test a pdf
        r = freebase.sandbox.uri_submit("http://www.jcbl.or.jp/game/nec/necfest07/nec2007_data/HayashiMiyake.pdf", content_type="application/pdf")
        self.assertEqual(r['/type/content/media_type'], 'application/pdf')
        
        # test an image
        r = freebase.sandbox.uri_submit("http://datamob.org/media/detail_freebase.png")
        self.assertEqual(r['/type/content/media_type'], 'image/png')
        
    def test_version(self):
        r = freebase.version()
        self.assertNotEqual(len(r), 0)
       
    def test_status(self):
        r = freebase.status()
        self.assertNotEqual(len(r), 0)
        self.assertEqual(r["status"], u"200 OK")

    
    def test_private_domains(self):
        freebase.sandbox.login(username=USERNAME, password=PASSWORD)
        r = freebase.sandbox.create_private_domain("superfly" + str(int(random.random() * 1e10)), "Superfly!")
        
        q = {"id" : r["domain_id"], "*" : None}
        info = freebase.sandbox.mqlread(q)
        self.assertEqual(info["type"], ["/type/domain"])
        self.assertNotEqual(len(info["key"]), 0)
        self.assertEqual(info["attribution"], info["creator"])
        
        freebase.sandbox.delete_private_domain(info["key"][0])
        deleted = freebase.sandbox.mqlread(q)
        self.assertEqual(len(deleted["key"]), 0)
        self.assertEqual(len(deleted["type"]), 0)
        self.assertEqual(deleted["name"], None)
        self.assertEqual(deleted["creator"], info["attribution"])
        

if __name__ == '__main__':
    unittest.main()

