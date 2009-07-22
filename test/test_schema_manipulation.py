import unittest
import sys, logging
import freebase
import random
import time

import getlogindetails

from freebase.api import HTTPMetawebSession, MetawebError
from freebase.schema import create_type, reciprocate_property, delegate_property
from freebase.schema import create_property, add_type_to_object, copy_property, move_property
from freebase.schema import create_object, connect_object, disconnect_object
from freebase.schema import move_object

USERNAME = 'username'
PASSWORD = 'password'
API_HOST = 'http://sandbox-freebase.com'

s = freebase.api.HTTPMetawebSession(API_HOST)
domain_id = None

if USERNAME == "username" and PASSWORD == "password":
    USERNAME, PASSWORD = getlogindetails.main()

s.login(USERNAME, PASSWORD)

r = s.create_private_domain("test" + str(int(random.random() * 1e10)), "test")["domain_id"]
domain_id = s.mqlread({"id" : r, "a:id" : None})["a:id"]

# Sorry, this is just so annoying to type.
f = lambda x: x["id"]

class TestSchemaManipulation(unittest.TestCase):
    
    def test_make_and_type_object(self):
        a = create_object(s, "A", path=domain_id + "/a")
        self.assertEqual(a.create, "created")
        
        b = create_object(s, "B", path=domain_id + "/b", included_types=["/people/person"])
        
        q = { "id" : b.id, "type" : [{"id" : None}] }
        types = [x["id"] for x in s.mqlread(q)["type"]]
        self.assertEqual("/common/topic" in types, True)
        self.assertEqual("/people/person" in types, True)
        self.assertEqual("/film/actor" in types, False)
        
        add_type_to_object(s, b.id, "/film/film_genre")
        
        types = [x["id"] for x in s.mqlread(q)["type"]]
        
        self.assertEqual("/film/film_genre" in types, True)
        self.assertEqual("/media_common/media_genre" in types, True)

    def test_move_object(self):
        old = create_object(s, "old", domain_id + "/old")
        move_object(s, domain_id + "/old", domain_id + "/new")
        is_old = { "id" : domain_id + "/old", "key" : [{"value" : None}]}
        is_new = { "id" : domain_id + "/new", "key" : [{"value" : None}]}
        s.touch()
        o = s.mqlread(is_old)
        n = s.mqlread(is_new)
        # we don't just check to see if the id exists, as freebase caches id -> guid lookups
        if o:
            self.assertEqual(len([b for b in o["key"] if b["value"] == "old"]), 0)
        self.assertEqual(len([b for b in n["key"]]), 1)
    
    def test_property_moving(self):
        person = create_type(s, "Person", "person", domain_id)
        date_of_birth = create_property(s, "DB", "db", domain_id + "/person", "/type/datetime", False, tip="Date of Birth of a Person")
        
        goblin = create_type(s, "Goblin", "goblin", domain_id)
        self.assertEqual(s.mqlread({"id" : domain_id + "/goblin/db"}), None)
        copy_property(s, domain_id + "/person/db", domain_id + "/goblin/db")
        self.assertNotEqual(s.mqlread({"id" : domain_id + "/goblin/db"}), None)

        self.assertEqual(s.mqlread({"id" : domain_id + "/goblin/db", "/freebase/documented_object/tip" : None})["/freebase/documented_object/tip"], "Date of Birth of a Person")
        
        # But we don't actually want that to be the tip, we should be able to change it
        dragon = create_type(s, "Dragon", "dragon", domain_id)
        copy_property(s, domain_id + "/person/db", domain_id + "/dragon/db", **{"/freebase/documented_object/tip": "Date of Birth of a Dragon!"})
        self.assertEqual(s.mqlread({"id" : domain_id + "/dragon/db", "/freebase/documented_object/tip" : None})["/freebase/documented_object/tip"], "Date of Birth of a Dragon!")

        # let's test with a slightly move obtuse property, unit!
        create_property(s, "Magnetic Moment", "mmoment", domain_id + "/person", "/type/float", True, 
                        extra={"unit" : {"connect" : "insert", "id" : "/en/nuclear_magneton"}})
        copy_property(s, domain_id + "/person/mmoment", domain_id + "/goblin/mmoment")
        self.assertEqual(s.mqlread({"id" : domain_id + "/goblin/mmoment", "/type/property/unit" : {"id" : None}})["/type/property/unit"]["id"], "/en/nuclear_magneton")


    def test_rename_property(self):
        grendel = create_type(s, "Grendel", "grendel", domain_id)
        # a mistake
        date_of_bbirth = create_property(s, "Date of Bbirth", "dbb", domain_id + "/grendel", "/type/datetime", False, tip="Date of Bbirth of Grendel")
        self.assertEqual(s.mqlread({"id" : domain_id + "/grendel/dbb", "name" : None})["name"], "Date of Bbirth")
        
        # let's fix it
        move_property(s, domain_id + "/grendel/dbb", domain_id + "/grendel/db", name="Date of Birth", **{"/freebase/documented_object/tip":"Date of Birth of Grendel"})
        self.assertEqual(s.mqlread({"id" : domain_id + "/grendel/db", "name" : None})["name"], "Date of Birth")
        # sometimes freebase still thinks /grendel/dbb exists... i hate id -> guid caches.
        self.assertEqual(s.mqlread({"id" : domain_id + "/grendel/dbb", "key" : [{"value" : None}]}), None)

    def test_recreate_contractbridge_base(self):
        
        base = domain_id
        
        create_type(s, "Bridge Player", "bridge_player", base, tip="A bridge player", included=["/people/person", "/common/topic"])
        create_type(s, "Bridge Tournament", "bridge_tournament", base, tip="A bridge tournament", included=["/event/event", "/common/topic"])
        create_type(s, "Bridge Tournament Standings", "bridge_tournament_standings", base, cvt=True, tip="Bridge Tournamen Results")

        player = base + "/bridge_player"
        tourney = base + "/bridge_tournament"
        standing = base + "/bridge_tournament_standings"

        # tournament standings
        # ideas: create a cvt could be a function, disambig always True, same schema, iono, whatever
        create_property(s, "Year", "year", standing, "/type/datetime", True, disambig=True, tip="Year")
        create_property(s, "First Place", "first_place", standing, player, False, disambig=True)
        create_property(s, "Second Place", "second_place", standing, player, False, disambig=True)
        create_property(s, "Tournament", "tournament", standing, tourney, True, disambig=True)


        # tournament
        reciprocate_property(s, "Standing", "standing", standing + "/tournament", False, disambig=True)
        create_property(s, "Location", "location", tourney, "/location/citytown", False, disambig=True)

        # bridge player
        # standings must be reverses!
        reciprocate_property(s, "First Place Finish", "first_place_finish", standing + "/first_place", False, False)
        reciprocate_property(s, "Second Place Finish", "second_place_finish", standing + "/second_place", False, False)

        #delegator property test
        delegate_property(s, "/people/person/date_of_birth", player, "Date of Birth", "db")

    def test_create_over_created(self):
        """ No creating a property on top of an already created one..."""
        create_type(s, "Rapper", "rapper", domain_id)
        create_property(s, "Styles", "styles", domain_id+"/rapper", "/music/genre")
        
        # now we mistakenly create the same prop
        # it should just exit as if it finished successfully... but, it shouldn't actually do anything
        create_property(s, "Styles", "styles", domain_id+"/rapper", "/music/genre")
        # we also mistakenly create the same type, again
        create_type(s, "Rapper", "rapper", domain_id)
    
    def test_reciprocating_reciprocated(self):
        """ You can't reciprocate an already reciprocated property"""
        create_type(s, "Master", "master", domain_id)
        create_type(s, "Servant", "servant", domain_id)
        
        create_property(s, "Servants", "servants", domain_id + "/master", domain_id + "/servant", unique=False)
        reciprocate_property(s, "Masters", "masters", domain_id + "/master/servants", unique=False)
        
        self.assertRaises(MetawebError, lambda: reciprocate_property(s, "Buddies", "buddies", domain_id + "/master/servants", unique=False))

if __name__ == '__main__':
    unittest.main()
  
