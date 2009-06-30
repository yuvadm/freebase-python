try:
    import simplejson as json
except ImportError:
    import json

import urllib
from freebase.api import HTTPMetawebSession, MetawebError

from freebase.api import LITERAL_TYPE_IDS

mss = HTTPMetawebSession( 'sandbox.freebase.com', USERNAME, PASSWORD )
mss.login()

def key_exists( s, k ):
   q = {
       "id" : k,
       "guid" : None }
   return not None == s.mqlread( q )

def create_type( s, name, key, ns, cvt=None, tip=None, enum=None, included=[]):
   if key_exists( s, ns + "/" + key ):
       return
   q = {
       "create" : "unconditional",
       "type" : "/type/type",
       "/type/type/domain" : { "connect" : "insert", "id" : ns },
       "name" : {"connect" : "insert", "value" : name, "lang" : "/lang/en" },
       "key" : {
           "connect" : "insert",
           "value" : key,
           "namespace" : ns }
      }
   
   if included:
       q['/freebase/type_hints/included_types'] = \
          [ {"connect":"insert",
             "id":included_id}
             for included_id in included ]
   
   if enum:
      pass # TODO. What is enumerator?
   
   if cvt:
       q['/freebase/type_hints/mediator'] = { "connect" : "update", "value" : True }
   if tip:
       q['/freebase/documented_object/tip'] = { "connect" : "update", "value" : tip, "lang" : "/lang/en" }
   s.mqlwrite( q )

def create_property( s, name, key, schema, expected, unique, disambig=False, tip=None, extra=None ):
    if key_exists( s, schema + "/" + key ):
        return
    q = {
        "create" : "unconditional",
        "type" : "/type/property",
        "name" : name,
        "key" : {
            "connect" : "insert",
            "value" : key,
            "namespace" : { "id" : schema },
        }, 
        "schema" : { "connect" : "insert", "id" : schema },
        "expected_type" : { "connect" : "insert", "id" : expected }
    }
    if unique:
         q['unique'] = { "connect" : "update", "value" : unique }
    if tip:
         q['/freebase/documented_object/tip'] = { "connect" : "update", "value" : tip, "lang" : "/lang/en" }
    if disambig:
         q['/freebase/property_hints/disambiguator'] = { "connect" : "update", "value" : True }
    if extra:
         q.update(extra)
    #print json.dumps(q, indent=2)
    s.mqlwrite(q)

def delegate_property( s, p, schema, name=None, key=None, expected=None, tip=None):
   q = {
       "id" : p,
       "type" : "/type/property",
       "name" : None,
       "unique" : None,
       "expected_type" : {"id" : None},
       "key" : None,
       "/freebase/documented_object/tip" : None,
       "/freebase/property_hints/disambiguator" : None }
   r = s.mqlread(q)
   
   # If the expected_type of the delegator(master) is a primitive, the delegated's
   # expected_type must be the same
   if r["expected_type"]["id"] in LITERAL_TYPE_IDS:
      if expected:
         print "You can't set the expected_type if the expected_type of the delegated(master) is a primitive"
      expected = r["expected_type"]["id"]
   # If the expected_type of the delegator(master) is not a primitive, the delegated's
   # expected_type can be different
   elif expected is None:
      expected = r["expected_type"]["id"]

      
   if not tip and r["/freebase/documented_object/tip"]:
       tip = r["/freebase/documented_object/tip"]

   if name is None:
      name = r["name"]
   if key is None:
      key = r["key"]
   
   create_property(s, name, key, schema, expected, r['unique'],
       r["/freebase/property_hints/disambiguator"],
       tip,
       { "/type/property/delegated" : p } )
       

def reciprocate_property( s, name, key, master, unique, disambig=False, tip=None, extra=None ):
   """ We're creating a reciprocate property of the master property. Let's illustrate
   the idea behind the function with an example.
   
   Say we examine the /visual_art/art_period_movement/associated_artworks property.
   An example of an art_period_movement is the Renaissance, and once associated_artworks
   could be the /en/mona_lisa. In this example, /visual_art/art_period_movement/associated_artworks
   will be the master property, and /visual_art/artwork/period_or_movement will be the reciprocal.
   
   In order to determine the characterists of the reciprocal property, we must examine the master.
   associated_artworks property's schema is /visual_art/art_period_movement and its expected
   type is /visual_art/artwork. Notice the similarity to /visual_art/artwork/period_or_movement.
   period_or_movement's schema is /visual_art/artwork -- art_period_movement's expected type.
   period_or_movement's expected type is /visual_art/art_period_movement -- art_period_movement's
   schema!
   
   So, given a master, the reciprocal's schema is the master's expected type and the reciprocal's
   expected type is the master's schema. """
   
   
   q = {
       "id" : master,
       "/type/property/expected_type" : None,
       "/type/property/schema" : None }
   r = s.mqlread(q)
   ect = r["/type/property/expected_type"]
   schema = r["/type/property/schema"]
   create_property(s, name, key, ect, schema, unique, disambig, tip,
       extra = { "master_property" : master })

def make_subclass(s, sub, super):
   q = {
       "id" : super,
       "type" : "/type/type",
       "properties" : [{"id" : None}] }
   r = s.mqlread( q )
   for p in map(lambda x: x['id'], r['properties'] ):
       delegate_property(s, p, sub)
   w = {
       "id" : sub,
       "/freebase/type_hints/included_types" : { "connect" : "insert", "id" : super }}
   s.mqlwrite(w)

def gogo(s, base="/base/bingbase"):
   
   create_type(s, "Bridge Player", "bridge_player", base, tip="A bridge player", included=["/people/person", "/common/topic", base+"/topic"])
   create_type(s, "Bridge Tournament", "bridge_tournament", base, tip="A bridge tournament", included=["/event/event", "/common/topic", base+"/topic"])
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
   delegate_property(mss, "/people/person/date_of_birth", player, "Date of Birth", "db")
   
   # for cvt: expected_type: cvt, reciprocated property is the property on the cvt



def create_chapter( s ):
   create_type( s, "Chapter", "chapter", "/base/testy", True, "A chapter in one of the books" )
   print "created book!"
   create_property( s, "Book", "book", "/base/testy/chapter",
       "/base/testy/book", True, True, "The book of which this chapter is a part" )
   print "created property!"
   reciprocate_property( s, "/base/testy/chapter/book",
       "Chapters", "chapters", "/base/testy/book", False, False, "Chapters in this book" )

def create_edition( s ):
   create_type( s, "Edition", "edition", "/base/testy", True, "An edition of the Aubrey-Maturin series" )
   create_property( s, "Examples", "examples", "/base/testy/edition",
       "/book/book_edition", False, False, "Book editions in this series" )
   w = {
       "id" : "/base/testy/edition",
       "/freebase/type_hints/enumeration" : { "value" : True, "connect" : "update" }}
   s.mqlwrite( w )
   w = {
       "create" : "unless_exists",
       "type" :"/base/testy/edition",
       "name" : "W. W. Norton Paperback" }
   s.mqlwrite( w )

def create_page_ref( s ):
   create_type( s, "Page Reference", "page_ref", "/base/testy", True,
       "A reference to a page in a particular edition" )
   t = "/base/testy/page_ref"
   create_property( s, "Page Number", "page", t, "/type/int", True, True )
   create_property( s, "Edition", "edition", t, "/base/testy/edition", True, True )

def create_mention_properties( s, t ):
   create_property( s, "Circumstances", "circumstances", t, "/type/text", True, True,
       "Describe the circumstances of the mention" )
   create_property( s, "Quote", "quote", t, "/type/text", True, True,
       "A short quote from the mentioned location" )
   create_property( s, "Chapter", "chapter", t, "/base/testy/chapter", True, True,
       "The chapter in which the mention takes place" )
   create_property( s, "Page", "page", t, "/base/testy/page_ref", False, True,
       "Page number and Edition" )
   create_property( s, "What", "what", t, "/base/testy/topic", True, True,
       "What is being mentioned" )

#def delegate_mention_properties( s ):
#    t = '/base/testy/mention'
#    delegate_property( s, '/base/testy/character_mention/character', t )
#    delegate_property( s, '/base/testy/dish_mention/dish', t )
#    delegate_property( s, '/base/testy/historical_event_mention/event', t )
#    delegate_property( s, '/base/testy/place_mention/place', t )
#    delegate_property( s, '/base/testy/ship_mention/ship', t )
#    delegate_property( s, '/base/testy/species_mention/species', t )
#    delegate_property( s, '/base/testy/written_work_mention/written_work', t )
   # nothing for surgical instruments


'''
create_type( s, "Brew Pub", "brew_pub", "/base/brew_pubs", False, "A brew pub is a pub which brews its own beer on the premises" )
delegate_property( s, '/food/brewery_brand_of_beer/beers_produced', '/base/brewpubs/brew_pub', None, 'Beers produced on the premises' )
'''
