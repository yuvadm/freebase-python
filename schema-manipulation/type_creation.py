try:
    import simplejson as json
except ImportError:
    import json

import urllib
from freebase.api import HTTPMetawebSession, MetawebError

from freebase.api import LITERAL_TYPE_IDS
s = HTTPMetawebSession('sandbox.freebase.com', username, password)
s.login()

def key_exists(s, k):
    q = {
        "id" : k,
        "guid" : None
    }
    return not None == s.mqlread(q)


# Object helpers
def create_object(s, name="", path=None, key=None, namespace=None, included_types=[], create="unless_exists", extra=None):
    if type(included_types) is str:
        included_types = [included_types]
    
    if path and (key or namespace):
        raise Exception("You can't specify both the path and a key and namespace.")
    
    if path:
        key, namespace = get_key_namespace(path)
    
    its = set(included_types)
    if included_types:
        q = [{
            "id|=" : included_types,
            "/freebase/type_hints/included_types" : [{"id" : None}]
        }]
        for res in s.mqlread(q):
            its.update(map(lambda x: x["id"], res["/freebase/type_hints/included_types"]))
    
    wq = {
        "id" : None,
        "name" : name,
        "key" : {
            "namespace" : namespace,
            "value" : key,
        },
        "create" : create
    }
    
    if included_types:
        wq.update(type = [{ "id" : it, "connect" : "insert" } for it in its])
    
    if extra: 
        wq.update(extra)
    
    return s.mqlwrite(wq)


def connect_object(s, id, newpath, extra=None):
    
    key, namespace = get_key_namespace(newpath)
    
    wq = {
        "id" : id,
        "key" : {
            "namespace" : namespace,
            "value" : key,
            "connect" : "insert"
        }
    }
    
    if extra: wq.update(extra)
    
    return s.mqlwrite(wq)


def unconnect_object(s, id, extra=None):
    
    key, namespace = get_key_namespace(id)
    
    wq = {
        "id" : id,
        "key" : {
            "namespace" : namespace,
            "value" : key,
            "connect" : "delete"
        }
    }
    if extra: wq.update(extra)
    return s.mqlwrite(wq)

def move_object(s, oldpath, newpath):
    a = connect_object(s, oldpath, newpath)
    b = unconnect_object(s, oldpath)
    return a, b

def type_object(s, id, type_id):
    q = {
        "id" : type_id,
        "/freebase/type_hints/included_types" : [{"id" : None}]
    }
    included_types = map(lambda x: x["id"], s.mqlread(q)["/freebase/type_hints/included_types"])
    
    wq = {
        "id" : id,
        "type" : [{
            "id" : it,
            "connect" : "insert"
        } for it in included_types + [type_id]]
    }
    return s.mqlwrite(wq)

def get_key_namespace(path):
    split = path.split("/")
    return split[-1], "/".join(split[:-1]) or "/"


# type moving


# property moving

def connect_property(s, id, newid, **extra):
    split = newid.split("/")
    newschema = "/".join(split[:-1])
    newname = split[-1]
    
    info = get_property_info(s, id)
    info["__raw"].update(extra)
    create_property(s, info["name"], newname, newschema, info["expected_type"], info["unique"], info["/freebase/property_hints/disambiguator"],
        info["/freebase/documented_object/tip"], info["__raw"])  

def move_property(s, id, newid, **extra):
    connect_property(s, id, newid, **extra)
    disconnect_schema = {"type" : "/type/property", "schema" : {"connect" : "delete", "id" : "/".join(id.split("/")[:-1]) }}    
    unconnect_object(s, id, extra = disconnect_schema)

PROPERTY_QUERY = {
        "optional" : True,
        "type" : "/type/property",
        "delegated" : {},
        "enumeration" : {}, 
        "expected_type" : {}, 
        "id" : {},
        "key" : [{
            "namespace" : None, 
            "value" : None
        }],
        #"link" : [{}], 
        "master_property" : {},
        "name" : {"value" : None, "lang" : "/lang/en", "optional":True}, 
        "schema" : {"id" : None, "name" : None},
        "unique" : {}, 
        "unit" : {},
        "/freebase/documented_object/tip" : {"value" : None, "limit":1, "optional" : True},
        "/freebase/property_hints/disambiguator" : {},
        "/freebase/property_hints/display_none" : {},
        "/freebase/property_hints/display_orientation" : {},
        "/freebase/property_hints/enumeration" : {},
        "/freebase/property_hints/dont_display_in_weblinks" : {},
        "/freebase/property_hints/inverse_description" : {},
    }

TYPE_QUERY = {
        "type" : "/type/type",
        "domain" : {},
        "key" : [{"namespace" : None, "value" : None}],
        "name" : {"value" : None, "lang" : "/lang/en", "optional":True},
        "/freebase/type_hints/included_types" : [{}],
        "/freebase/type_hints/mediator" : None,
        "/freebase/type_hints/enumeration" : None,
        "/freebase/type_hints/minor" : None,
        "/freebase/documented_object/tip" : {"value" : None, "limit":1, "optional":True},
        "properties" : {"optional" : True}
        }
TYPE_QUERY.update(properties=[PROPERTY_QUERY])


def get_property_info(s, prop_id):
    q = PROPERTY_QUERY
    q.update(id=prop_id)
    res = s.mqlread(q)
    info = {}

    info["name"] = res["name"]["value"]
    if res["schema"]:
        info["schema"] = res["schema"]["id"]
    else: info["schema"] = None
    
    if res["key"]:
        info["keys"] = map(lambda x: (x["value"], x["namespace"]), res["key"])
    else: info["key"] = None
    
    if res["/freebase/documented_object/tip"]:
        info["/freebase/documented_object/tip"] = res["/freebase/documented_object/tip"]["value"]
    else: info["/freebase/documented_object/tip"] = None

    for i in ["delegated", "enumeration", "expected_type", "id", "master_property", "unique", "unit",
     "/freebase/property_hints/disambiguator", "/freebase/property_hints/display_none",
     "/freebase/property_hints/display_orientation","/freebase/property_hints/enumeration",
      "/freebase/property_hints/dont_display_in_weblinks", "/freebase/property_hints/inverse_description"]:

        if res[i]:
            if isinstance(res[i], basestring):
                info[i] = res[i]
            elif res[i].has_key("id"):
                info[i] = res[i]["id"]
            elif res[i].has_key("value"):
                info[i] = res[i]["value"]
            else:
                raise Exception("There is a problem with getting the property value.")
        else: info[i] = None

    # delete the properties that are going to be asked for in create_property
    del res["name"]
    del res["schema"]
    del res["key"]
    del res["expected_type"]
    del res["unique"]
    del res["/freebase/property_hints/disambiguator"]
    del res["/freebase/documented_object/tip"]

    # delete other useless things...
    del res["id"]

    for i in [k for k, v in res.items() if v is None]:
        del res[i]

    info["__raw"] = res
    return info


# Create Type
def create_type(s, name, key, ns, cvt=None, tip=None, enum=None, included=[]):
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
            "namespace" : ns
        }
    }
   
    if included:
        if isinstance(included, basestring):
            included = [included]
        q = {
            "id|=" : included,
            "/freebase/type_hints/included_types" : [{"id" : None}]
        }
        r = s.mqlread(q)
        included_types = set()
        for i in r:
            included_types.append(map(lambda x: x["id"], i["/freebase/type_hints/included_types"]))
        
        q['/freebase/type_hints/included_types'] = \
           [ {"connect":"insert",
                "id":included_id}
                for included_id in included_types]
   
    if enum:
        pass # TODO. What is enumerator?
   
    if cvt:
        q['/freebase/type_hints/mediator'] = { "connect" : "update", "value" : True }
    if tip:
        q['/freebase/documented_object/tip'] = { "connect" : "update", "value" : tip, "lang" : "/lang/en" }
    return s.mqlwrite(q, use_permission_of=ns)


# Create Property
def create_property(s, name, key, schema, expected, unique, disambig=False, tip=None, extra=None):
    if key_exists(s, schema + "/" + key):
        raise Exception("The key \"%s\" already exists!", schema + "/" + key)
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
    return s.mqlwrite(q, use_permission_of=schema)

def delegate_property(s, p, schema, name=None, key=None, expected=None, tip=None):
    q = {
        "id" : p,
        "type" : "/type/property",
        "name" : None,
        "unique" : None,
        "expected_type" : {"id" : None},
        "key" : None,
        "/freebase/documented_object/tip" : None,
        "/freebase/property_hints/disambiguator" : None
    }
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
   
    return create_property(s, name, key, schema, expected, r['unique'],
        r["/freebase/property_hints/disambiguator"],
        tip,
        { "/type/property/delegated" : p})

def reciprocate_property(s, name, key, master, unique, disambig=False, tip=None):
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
    return create_property(s, name, key, ect, schema, unique, disambig, tip,
        extra = { "master_property" : master })


# ?
def make_subclass(s, sub, super):
    q = {
        "id" : super,
        "type" : "/type/type",
        "properties" : [{"id" : None}]
    }
    r = s.mqlread( q )
    for p in map(lambda x: x['id'], r['properties'] ):
        delegate_property(s, p, sub)
    w = {
        "id" : sub,
        "/freebase/type_hints/included_types" : { "connect" : "insert", "id" : super }
    }
    s.mqlwrite(w)

def gogo(base="/base/bingbase"):
   
    
   
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


# another test... not sure it works
def create_chapter(s):
    create_type( s, "Chapter", "chapter", "/base/testy", True, "A chapter in one of the books" )
    print "created book!"
    create_property( s, "Book", "book", "/base/testy/chapter",
        "/base/testy/book", True, True, "The book of which this chapter is a part" )
    print "created property!"
    reciprocate_property( s, "/base/testy/chapter/book",
        "Chapters", "chapters", "/base/testy/book", False, False, "Chapters in this book" )

def create_edition(s):
    create_type( s, "Edition", "edition", "/base/testy", True, "An edition of the Aubrey-Maturin series" )
    create_property( s, "Examples", "examples", "/base/testy/edition",
        "/book/book_edition", False, False, "Book editions in this series" )
    w = {
        "id" : "/base/testy/edition",
        "/freebase/type_hints/enumeration" : { "value" : True, "connect" : "update" }
    }
    s.mqlwrite( w )
    w = {
        "create" : "unless_exists",
        "type" :"/base/testy/edition",
        "name" : "W. W. Norton Paperback"
    }
    s.mqlwrite( w )

def create_page_ref(s):
    create_type( s, "Page Reference", "page_ref", "/base/testy", True,
        "A reference to a page in a particular edition" )
    t = "/base/testy/page_ref"
    create_property( s, "Page Number", "page", t, "/type/int", True, True )
    create_property( s, "Edition", "edition", t, "/base/testy/edition", True, True )

def create_mention_properties(s, t):
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

