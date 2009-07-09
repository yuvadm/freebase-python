import unittest
import sys, logging
import freebase
import random
import time

from freebase.api import HTTPMetawebSession, MetawebError

from get_type import dump_type, dump_base, upload_type

USERNAME = 'username'
PASSWORD = 'password'
API_HOST = 'sandbox.freebase.com'

s = freebase.api.HTTPMetawebSession(API_HOST)

# Sorry, this is just so annoying to type.
f = lambda x: x["id"]

class TestHardcoreSchemaManipulation(unittest.TestCase):
 
    def test_copy_an_entire_domain(self):
        domain_id = _create_domain()
        ex_domain_id = "/film" # example domain id
        ex_domain_type = "actor"
        ex_domain_type_id = ex_domain_id + "/" + ex_domain_type
        
        graph = dump_base(s, ex_domain_id)
        upload_type(s, graph, domain_id)
        
        newperson, realperson = s.mqlreadmulti([{"id" : domain_id + "/" + ex_domain_type, "/type/type/properties" : {"return" : "count" }}, 
                                                {"id" : ex_domain_type_id, "/type/type/properties" : {"return" : "count" }}])
        self.assertEqual(newperson["/type/type/properties"], realperson["/type/type/properties"])
        
        # let's try and check everything.
        # - check all the types are there
        realtypes = s.mqlread([{"id" : None, "type" : "/type/type", "domain" : ex_domain_id}])
        newtypes = s.mqlread([{"id" : None, "type" : "/type/type", "domain" : domain_id}])
        
        l = lambda q: sorted(map(f, q))
        
        realtypes = l(realtypes)
        newtypes  = l(newtypes)
        print realtypes
        print newtypes
        self.assertEqual(len(realtypes), len(newtypes))
        for i in range(len(realtypes)):
            self.assertEqual(realtypes[i].lsplit("/", 1), newtypes[i].lsplit("/", 1))
        
        # - check the properties are the same
        
        def get_properties(types):
            properties = set()
            for i in s.mqlreadmulti([[{"id" : id, "/type/type/properties" : {"id" : None}}] for id in types]):
                properties.update(map(f, i["/type/type/properties"]))
            return properties
        
        realproperties = sorted(list(get_properties(realtypes)))
        newproperties  = sorted(list(get_properties(newtypes)))
        
        self.assertEqual(realproperties, newproperties)
        for i in range(len(realproperties)):
            self.assertEqual(realtypes[i].lsplit("/", 1), newtypes[i].lsplit("/", 1))
            
        # - check the properties and type's attributes are the same 
        
        
    
    def test_try_copying_a_cvt(self):
        
        # if follow_types is True, everything is kosher.
        domain_id = _create_domain()
        graph = dump_type(s, "/film/actor", follow_types=True)
        upload_type(s, graph, domain_id)
        
        newactor, realactor = s.mqlreadmulti([{"id" : domain_id + "/actor", "/type/type/properties" : {"return" : "count" }}, 
                                    {"id" : "/film/actor", "/type/type/properties" : {"return" : "count" }}])
        self.assertEqual(newactor["/type/type/properties"], realactor["/type/type/properties"])
        
        # if follow_types is False, if we try to upload a cvt, it should whine
        self.assertRaises(Exception, lambda: dump_type(s, "/film/actor", follow_types=False))
        
        

def _create_domain():
    domain_id = s.create_private_domain("test" + str(int(random.random() * 1e10)), "test")["domain_id"]
    domain_id = s.mqlread({"id" : domain_id, "a:id" : None})["a:id"]
    return domain_id

if __name__ == '__main__':
    if USERNAME == "username" and PASSWORD == "password":
        try:
            passwordfile = open(".password.txt", "r")
            fh = passwordfile.read().split("\n")
            USERNAME = fh[0]
            PASSWORD = fh[1]
            passwordfile.close()
            s.login(USERNAME, PASSWORD)

        except Exception, e:
            print "In order to run the tests, we need to use a valid freebase username and password"
            USERNAME = raw_input("Please enter your username: ")
            PASSWORD = raw_input("Please enter your password (it'll appear in cleartext): ")
            s.login(USERNAME, PASSWORD)
            print "Thanks!"

    else:
        s.login(USERNAME, PASSWORD)

    unittest.main()


    
