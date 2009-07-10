import unittest
import sys, logging
import freebase
import random
import time

import getlogindetails

from freebase.api import HTTPMetawebSession, MetawebError
from freebase.schema import dump_type, dump_base, restore

USERNAME = 'username'
PASSWORD = 'password'
API_HOST = 'sandbox.freebase.com'

s = freebase.api.HTTPMetawebSession(API_HOST)

if USERNAME == "username" and PASSWORD == "password":
    USERNAME, PASSWORD = getlogindetails.main()

s.login(USERNAME, PASSWORD)

# Sorry, this is just so annoying to type.
f = lambda x: x["id"]

class TestHardcoreSchemaManipulation(unittest.TestCase):
 
    def test_copy_an_entire_domain(self):
        domain_id = _create_domain()
        ex_domain_id = "/base/contractbridge" # example domain id
        ex_domain_type = "bridge_player"
        ex_domain_type_id = ex_domain_id + "/" + ex_domain_type
        
        graph = dump_base(s, ex_domain_id)
        restore(s, graph, domain_id)
        
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
        
        self.assertEqual(len(realtypes), len(newtypes))
        for i in range(len(realtypes)):
            self.assertEqual(realtypes[i].rsplit("/", 1)[-1], newtypes[i].rsplit("/", 1)[-1])
        
        # - check the properties are the same
        
        def get_properties(types):
            properties = set()
            for i in s.mqlreadmulti([{"id" : id, "/type/type/properties" : [{"id" : None}]} for id in types]):
                properties.update(map(lambda x: x["id"], i["/type/type/properties"]))
            return properties
        
        realproperties = sorted(list(get_properties(realtypes)))
        newproperties  = sorted(list(get_properties(newtypes)))
        
        def ignore_base(id): return id.rsplit("/", 1)[-1]
        
        self.assertEqual(len(realproperties), len(newproperties))
        self.assertEqual([ignore_base(prop_id) for prop_id in realproperties], [ignore_base(prop_id) for prop_id in newproperties])
        
        # - check the properties and type's attributes are the same
        
        
        
    
    def test_try_copying_a_cvt(self):
        
        # if follow_types is True, everything is kosher.
        domain_id = _create_domain()
        graph = dump_type(s, "/film/actor", follow_types=True)
        restore(s, graph, domain_id)
        
        newactor, realactor = s.mqlreadmulti([{"id" : domain_id + "/actor", "/type/type/properties" : {"return" : "count" }}, 
                                              {"id" : "/film/actor", "/type/type/properties" : {"return" : "count" }}])
        self.assertEqual(newactor["/type/type/properties"], realactor["/type/type/properties"])
        
        # if follow_types is False, if we try to upload a cvt, it should whine
        from freebase.schema import CVTError
        self.assertRaises(CVTError, lambda: dump_type(s, "/film/actor", follow_types=False))
        
        

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


    
