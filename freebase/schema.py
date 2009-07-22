from copy import deepcopy

from freebase.api.session import HTTPMetawebSession, MetawebError
from freebase.api.session import LITERAL_TYPE_IDS

"""
NOTE
----
graph is used freely in this file. Some information:
 - It refers to an internal representation of a group of types.
 - It resembles a mqlread result, but it is not a mqlread result
 - It also has some helper variables like __requires and __related.
 - All helper variables start with __ since that's not valid MQL
 - It is produced by _get_graph
 - It can be converted into valid json (json.dumps(graph, indent=2))
 
Its structure is as follows:

    "type_id" : {
      "name" : "My Type",
      "id" : "/base_id/type_id"
      ...
      "__requires" : ["/base_id/type_id2"]
      "properties" : [
        {
          "id" : "/base_id/type_id/my_prop"
          ...
        },
        {
          ...
        }
      ]
    },
    "type_id2" : {...}
    ...
    
"""

class DelegationError(Exception):
    """You can't set the expected_type if the expected_type of the delegated (master) is a primitive"""

class CVTError(Exception):
    """You can't set follow_types to False if there's a cvt. A cvt requires you get all the relevant types. Set follow_types to true."""

def key_exists(s, k):
    q = {
        "id" : k,
        "guid" : None
    }
    return not None == s.mqlread(q)

### SCHEMA MANIPULATION ###
# Object helpers
def create_object(s, name="", path=None, key=None, namespace=None, 
                    included_types=None, create="unless_exists",
                    extra=None, use_permission_of=None, attribution=None):
    """
    Create object with name, a path or a key and namespace, included_types.
    You can also specify how it is created (unless_exists, unconditional..)
    as well as use_permission_of and attribution
    """
    if type(included_types) is str:
        included_types = [included_types]

    if path and (key or namespace):
        raise ValueError("You can't specify both the path and a key and namespace.")

    if path:
        key, namespace = get_key_namespace(path)

    if (key and not namespace) or (not key and namespace):
        raise ValueError("You must either specify both a key and a namespace, or neither.")

    if included_types:
        its = set(included_types)
        q = [{
            "id|=" : included_types,
            "/freebase/type_hints/included_types" : [{"id" : None}]
        }]
        for res in s.mqlread(q):
            its.update([x["id"] for x in res["/freebase/type_hints/included_types"]])

    wq = {
        "id" : None,
        "name" : name,
        "create" : create
    }

    # conditionally add key creation
    if key:
        wq.update({"key" : { 
            "namespace" : namespace,
            "value" : key,
        }})

    if included_types:
        wq.update(type = [{ "id" : it, "connect" : "insert" } for it in its])

    if extra: 
        wq.update(extra)

    return s.mqlwrite(wq, use_permission_of=use_permission_of, attribution_id=attribution)


def connect_object(s, id, newpath, extra=None, use_permission_of=None, attribution=None):
    """ connect object at id to a newpath.
    Example:
    connect_object(s, "/guid/002", "/en/the_beatles")
    """
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

    return s.mqlwrite(wq, use_permission_of=use_permission_of, attribution_id=attribution)


def disconnect_object(s, id, extra=None, use_permission_of=None, attribution=None):
    """ disconnect objects, as in removing their keys
    Example:
    disconnect_object(s, "/en/the_beatles")
    would remove the `the_beatles` key from /en """
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
    return s.mqlwrite(wq, use_permission_of=use_permission_of, attribution_id=attribution)

def move_object(s, oldpath, newpath, use_permission_of=None, attribution=None):
    """ move object from one key to another."""
    a = connect_object(s, oldpath, newpath, use_permission_of=use_permission_of, attribution=attribution)
    b = disconnect_object(s, oldpath, use_permission_of=use_permission_of, attribution=attribution)
    return a, b


def get_key_namespace(path):
    """ get (key, namespace) from a path
    get_key_namespace("/common") -> ("common", "/")
    get_key_namespace("/food/drinks") -> ("drinks", "/food")
    """
    # be careful with /common
    namespace, key = path.rsplit("/", 1)
    return (key, namespace or "/")


def add_type_to_object(s, id, type_id):
    """
     given an object (id) give it the type, type_id and all of its included types.
    """
    q = {
        "id" : type_id,
        "/freebase/type_hints/included_types" : [{"id" : None, "optional" : True}]
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


def copy_property(s, id, newid, **extra):
    """ create a new property with the same information as the starting property """
    newname, newschema = get_key_namespace(newid)
    
    info = get_property_info(s, id)
    info["__raw"].update(extra)
    
    unique = None
    if info.has_key(unique):
        unique = info["unique"]
    disambig = None
    if info.has_key("/freebase/property_hints/disambiguator"):
        disambig = info["/freebase/property_hints/disambiguator"]
    create_property(s, info["name"], newname, newschema, info["expected_type"], unique=unique, disambig=disambig,
        tip=info["/freebase/documented_object/tip"], extra=info["__raw"])

def move_property(s, id, newid, **extra):
    """ create an identical property and delete the old one """
    copy_property(s, id, newid, **extra)
    disconnect_schema = {"type" : "/type/property", "schema" : {"connect" : "delete", "id" : "/".join(id.split("/")[:-1]) }}  
    disconnect_object(s, id, extra = disconnect_schema)

def get_property_info(s, prop_id):
    """
    get_property_info returns a valid json dictionary object that has all the information
    required to describe a property. This is only used by copy_property, but could be used
    by whoever.
    
    Ideally, all the required information by create_property is in the root of the dictionary
    while all the extra information is in result["__raw"]
    """
    q = deepcopy(PROPERTY_QUERY)
    q.update(id=prop_id)
    q.update(schema={"id" : None, "name" : None})
    res = s.mqlread(q)
    info = {}
    
    info["name"] = res["name"]["value"]
    if res["schema"]:
        info["schema"] = res["schema"]["id"]
    else: info["schema"] = None
    
    if res["key"]:
        info["key"] = [(x["value"], x["namespace"]) for x in res["key"]]
    else: info["key"] = None

    if res["/freebase/documented_object/tip"]:
        info["/freebase/documented_object/tip"] = res["/freebase/documented_object/tip"]["value"]
    else: info["/freebase/documented_object/tip"] = None
    
    ignore = ("optional", "type", "key", "/freebase/documented_object/tip")
    for prop in PROPERTY_QUERY.iterkeys():
        if prop not in ignore:
            if not info.has_key(prop):
                info[prop] = None

    info.update(_generate_extra_properties(res, ignore))
    
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

    for i in [k for k, v in res.iteritems() if v is None]:
        del res[i]

    info["__raw"] = res
    return info


# Create Type
def create_type(s, name, key, ns, cvt=False, tip=None, included=None, extra=None):
    """
    creates a type and takes care of associating it to its domain and attaching
    a key.
    """
    # TODO: CREATE SYNTHETIC VIEW
    if key_exists(s, ns + "/" + key ):
        return
    
    # assert isinstance(name, basestring) # name could be mqlish
    assert isinstance(key, basestring)
    assert isinstance(ns, basestring)
    
    assert tip is None or isinstance(tip, basestring)    
    assert included is None or isinstance(included, (basestring, list, tuple))
    assert extra is None or isinstance(extra, dict)

    wq = {
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
        its_q = [{
            "id|=" : included,
            "/freebase/type_hints/included_types" : [{"id" : None}]
        }]
        r = s.mqlread(its_q)
        included_types = set(included)
        if r:
            for i in r:
                included_types.update(map(lambda x: x["id"], i["/freebase/type_hints/included_types"]))

        its = [{"connect" : "insert", "id" : t} for t in included_types]
        wq['/freebase/type_hints/included_types'] = its

    # TODO: enum

    if cvt:
        wq['/freebase/type_hints/mediator'] = { "connect" : "update", "value" : True }
    if tip:
        wq['/freebase/documented_object/tip'] = { "connect" : "update", "value" : tip, "lang" : "/lang/en" }
    
    if extra: wq.update(extra)
    return s.mqlwrite(wq, use_permission_of=ns)


# Create Property
def create_property(s, name, key, schema, expected, unique=False, disambig=False, tip=None, extra=None):
    """
    create a property with ect, unique, etc, and make schema and key links
    """
    if key_exists(s, schema + "/" + key):
        return

    # validate parameters
    # assert isinstance(name, basestring) # could be mql
    assert isinstance(key, basestring)
    assert isinstance(schema, basestring)
    assert isinstance(expected, basestring)
    assert tip is None or isinstance(tip, basestring)    
    assert extra is None or isinstance(extra, dict)
    
    wq = {
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
         wq['unique'] = { "connect" : "update", "value" : unique }
    if tip:
         wq['/freebase/documented_object/tip'] = { "connect" : "update", "value" : tip, "lang" : "/lang/en" }
    if disambig:
         wq['/freebase/property_hints/disambiguator'] = { "connect" : "update", "value" : True }
    if extra:
         wq.update(extra)
    return s.mqlwrite(wq, use_permission_of=schema)

def delegate_property(s, p, schema, name=None, key=None, expected=None, tip=None, extra=None):
    """
    create a property with a delegate
    """
    assert isinstance(p, basestring)
    assert isinstance(schema, basestring)
    assert key is None or isinstance(key, basestring)
    assert expected is None or isinstance(expected, basestring)
    assert tip is None or isinstance(tip, basestring)
    
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
            if expected != r["expected_type"]["id"]:
                raise DelegationError("You can't set the expected_type if the expected_type of the delegated (master) is a primitive")
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
    
    delegate = { "/type/property/delegated" : p}
    if extra: delegate.update(extra)
    
    return create_property(s, name, key, schema, expected, r['unique'],
        r["/freebase/property_hints/disambiguator"],
        tip,
        delegate)

def reciprocate_property(s, name, key, master, unique=False, disambig=False, tip=None, extra=None):
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

    # assert isinstance(name, basestring) # name could be mqlish
    assert isinstance(key, basestring)
    assert isinstance(master, basestring)
    
    assert tip is None or isinstance(tip, basestring)
    assert extra is None or isinstance(extra, dict)
    
    # get master information
    q = {
        "id" : master,
        "/type/property/expected_type" : None,
        "/type/property/schema" : None,
        "/type/property/reverse_property" : None }
    r = s.mqlread(q)
    ect = r["/type/property/expected_type"]
    schema = r["/type/property/schema"]

    # check to see if a master existed
    if r["/type/property/reverse_property"]:
        raise MetawebError("You can't reciprocate property %s who \
                            already has a reverse property %s",
                            (master, r["/type/property/reverse_property"]))


    master = {"master_property" : master}
    if extra: master.update(extra)

    # NOTE: swapping ect and schema; see comment above
    return create_property(s, name, key, ect, schema, unique, disambig, tip,
        extra = master)

# dump / restore types
def dump_base(s, base_id):
    """ dump a base into a `graph` object. See information at the top of the file for more
    information on the graph file """
    types = [add_type_to_object["id"] for type_object in s.mqlread({"id" : base_id, "/type/domain/types":[{"id" : None}]})["/type/domain/types"]]
    graph = _get_graph(s, types, True)
        
    return graph

def dump_type(s, type_id, follow_types=True):
    """ dump a type (similar to dump_base) and has an argument follow_types that determines
    if it should dump types that are neccessary or just rely on them """
    types = [type_id]
    graph = _get_graph(s, types, follow_types)
    
    return graph

def restore(s, graph, new_location, ignore_types=None):
    """ given a `graph` object and a another location, we can upload our graph output
    into a new location in the freebase graph """
    follow_types = graph.get("__follow_types", True)
    
    # We assume the new_location is empty. if it isn't, we bail.
    # well, ...
    
    
    # create type dependencies
    type_requires_graph = {}
    
    # create prop dependencies
    prop_requires_graph = {}
    prop_to_type_map = {}
        
    for type_id, type_information in graph.iteritems():
        if not type_id.startswith("__"): # not a real type, but rather a helper
            # type dependency generation
            type_requires_graph[type_id] = type_information["__requires"]
            
            # prop dependency generation
            for prop in type_information["properties"]:
                prop_requires_graph[prop["id"]] = prop["__requires"]
                prop_to_type_map[prop["id"]] = type_id
            
    
    
    types_to_create = _generate_dependency_creation_order(type_requires_graph)
    props_to_create = _generate_dependency_creation_order(prop_requires_graph)
        
    origin_id, new_location_id = s.mqlreadmulti([{"id" : types_to_create[0], "type" : "/type/type", "domain" : {"id" : None}},
                                               {"id" : new_location, "a:id" : None}])                         
    origin_id = origin_id["domain"]["id"]
    new_location_id = new_location_id["a:id"]
    
    only_include = types_to_create + props_to_create
    
    for type_id in types_to_create:
        # let's find the type's key
        key = None
        for group in graph[type_id]["key"]:
            if group["namespace"] == origin_id:
                key = group["value"]
                break
        
        if key is None: # this shouldn't happen
            key = graph[type_id]["id"].split("/")[-1] # this can be wrong... different key than typeid
            
        
        tip = None
        if graph[type_id]["/freebase/documented_object/tip"]:
            tip = graph[type_id]["/freebase/documented_object/tip"]["value"]
        
        ignore = TYPE_INGORE_PROPERTIES
        extra = _generate_extra_properties(graph[type_id], ignore)
        
        name = graph[type_id]["name"]["value"]
        included = [_convert_name_to_new(included_type["id"], origin_id, new_location_id, only_include) for included_type in graph[type_id]["/freebase/type_hints/included_types"]]
        cvt = graph[type_id]["/freebase/type_hints/mediator"]
        
        create_type(s, name, key, new_location_id, included=included, cvt=cvt, tip=tip, extra=extra)
    
    for prop_id in props_to_create:
        type_id = prop_to_type_map[prop_id]
        all_properties_for_type = graph[type_id]["properties"]
        for prop in all_properties_for_type:
            if prop["id"] == prop_id: # good, we are dealing with our specific property 
                
                new_schema = _convert_name_to_new(type_id, origin_id, new_location_id, only_include)
                
                name =  prop["name"]
                
                expected = None
                if prop["expected_type"]:
                    expected = _convert_name_to_new(prop["expected_type"], origin_id, new_location_id, only_include)
                
                for group in prop["key"]:
                    if group["namespace"] == type_id:
                        key = group["value"]
                        break
                
                tip = None
                if prop["/freebase/documented_object/tip"]:
                    tip = prop["/freebase/documented_object/tip"]["value"]
                
                disambig = prop["/freebase/property_hints/disambiguator"]
                unique = prop["unique"]
                
                ignore = PROPERTY_IGNORE_PROPERTIES
                extra = _generate_extra_properties(prop, ignore)   
                
                if prop['master_property']:
                    converted_master_property = _convert_name_to_new(prop["master_property"], origin_id, new_location_id, only_include)
                    if converted_master_property == prop["master_property"]:
                        raise CVTError("You can't set follow_types to False if there's a cvt. A cvt requires you get all the relevant types. Set follow_types to true.\n" + \
                                       "The offending property was %s, whose master was %s." % (prop["id"], prop["master_property"]))
                    reciprocate_property(s, name, key, converted_master_property,
                        unique, disambig=disambig, tip=tip, extra=extra)
                
                elif prop['delegated']:
                    delegate_property(s, _convert_name_to_new(prop['delegated'], origin_id, new_location_id, only_include), new_schema,
                        expected=expected, tip=tip, extra=extra)
                
                else:
                    create_property(s, name, key, new_schema, expected, unique,
                        disambig=disambig, tip=tip, extra=extra)

def _get_graph(s, initial_types, follow_types):
    """ get the graph of dependencies of all the types involved, starting with a list supplied """
    
    assert isinstance(initial_types, (list, tuple))
    
    graph = {}
    to_update = set(initial_types)
    done = set()
    while len(to_update) > 0:
        new = to_update.pop()
        graph[new] = _get_needed(s, new)
        if follow_types:
            [to_update.add(b) for b in graph[new]["__related"] if b not in done]
            done.update(graph[new]["__related"])
        if not follow_types:
            # we have to check that there are no cvts attached to us, or else
            # ugly things happen (we can't include the cvt because the cvt won't link to us.)
            for prop in graph[new]["properties"]:
                if prop["master_property"]:
                    raise CVTError("You can't set follow_types to False if there's a cvt. A cvt requires you get all the relevant types. Set follow_types to true.\n" + \
                                    "The offending property was %s, whose master was %s." % (prop["id"], prop["master_property"]))
    
    graph["__follow_types"] = follow_types
    return graph


def _convert_name_to_new(old_name, operating_base, new_base, only_include=None):
    if old_name in only_include and old_name.startswith(operating_base):
        return new_base + old_name.replace(operating_base, "", 1)
    else:
        return old_name

def _generate_dependency_creation_order(requires_graph):
    # This is a naive topographical sort to determine
    # in what order to create types or properties so
    # that the other type/properties they rely on
    # are already created
    
    # This function is called with the type dependencies
    # and then the property dependencies.
    
    
    # we sort the dependency_list because its a good idea
    # to create the guys with zero dependencies before the
    # guys with one.. it's just a simple optimization to 
    # the topographical sort
    dependency_list = [(len(requires), name) for (name, requires) in requires_graph.iteritems()]
    dependency_list.sort()
    
    creation_order_list = []
    while len(dependency_list) > 0:
        number_of_requirements, id = dependency_list.pop(0)
        if number_of_requirements == 0:
            creation_order_list.append(id)
            continue
        else:
            are_the_types_dependencies_already_resolved = True
            for requirement in requires_graph[id]:
                if requirement not in creation_order_list:
                    are_the_types_dependencies_already_resolved = False
                    continue
            if are_the_types_dependencies_already_resolved:
                creation_order_list.append(id)
            else:
                dependency_list.append((number_of_requirements, id))
    return creation_order_list

def _generate_extra_properties(dictionary_of_values, ignore):
    extra = {}
    for k, v in dictionary_of_values.iteritems():
        if k not in ignore and not k.startswith("__"):
            if v:
                if isinstance(v, basestring):
                    extra.update({k:v})
                elif isinstance(v, bool):
                    extra.update({k:v})
                elif v.has_key("id"):
                    extra.update({k:v["id"]})
                elif v.has_key("value"):
                    extra.update({k:v["value"]})
                else:
                    raise ValueError("There is a problem with getting the property value.")
            else:
                if isinstance(v, bool): # well, if its False...
                    extra.update({k:v})
    return extra

def _get_needed(s, type_id):
    q = deepcopy(TYPE_QUERY)
    q.update(id=type_id)

    r = s.mqlread(q)
    properties = r.properties

    # let's identify who the parent is in order to only include
    # other types in that domain. We don't want to go around including
    # all of commons because someone's a /people/person
    parents = [r["domain"]["id"]]

    included_types = map(lambda x: x["id"], r["/freebase/type_hints/included_types"])
    related_types = set(included_types)
    for prop in properties:
        if prop["expected_type"]:
            related_types.add(prop["expected_type"])

    # we have two different types of relationships: required and related.
    # related can be used to generate subgraphs of types
    # required is used to generate the dependency graph of types

    related = _return_relevant(related_types, parents)
    requires = _return_relevant(included_types, parents)

    # get property information
    properties = r["properties"]
    for prop in properties:
        dependent_on = set()
        if prop["master_property"]:
            dependent_on.add(prop["master_property"])
        if prop["delegated"]:
            dependent_on.add(prop["delegated"])

        prop["__requires"] = _return_relevant(dependent_on, parents)

    # return all the information along with our special __* properties
    info = r
    info.update(__related=related, __requires=requires)

    return info


def _return_relevant(start_list, parents):
    final = []
    for item in start_list:
        indomain = False
        for parent in parents:
            if item.startswith(parent):
                indomain = True
                continue
        if indomain:
            final.append(item)
    return final

PROPERTY_QUERY = {
        "optional" : True,
        "type" : "/type/property",
        "delegated" : None,
        "enumeration" : None, 
        "expected_type" : None,
        "id" : None,
        "key" : [{
            "namespace" : None, 
            "value" : None
        }],
        "master_property" : None,
        "name" : {"value" : None, "lang" : "/lang/en", "optional":True}, 
        "unique" : None, 
        "unit" : None,
        "/freebase/documented_object/tip" : {"value" : None, "limit":1, "optional" : True},
        "/freebase/property_hints/disambiguator" : None,
        "/freebase/property_hints/display_none" : None,
        "/freebase/property_hints/display_orientation" : None,
        "/freebase/property_hints/enumeration" : None,
        "/freebase/property_hints/dont_display_in_weblinks" : None,
        "/freebase/property_hints/inverse_description" : None,
    }

TYPE_QUERY = {
        "type" : "/type/type",
        "domain" : {},
        "key" : [{"namespace" : None, "value" : None}],
        "name" : {"value" : None, "lang" : "/lang/en", "optional":True},
        "/freebase/type_hints/included_types" : [{"id" : None, "optional" : True}],
        "/freebase/type_hints/mediator" : None,
        "/freebase/type_hints/enumeration" : None,
        "/freebase/type_hints/minor" : None,
        "/freebase/documented_object/tip" : {"value" : None, "limit":1, "optional":True},
        }
TYPE_QUERY.update(properties=[deepcopy(PROPERTY_QUERY)])    

TYPE_INGORE_PROPERTIES = ("name", "domain", "key", "type", "id", "properties", "/freebase/type_hints/enumeration",
            "/freebase/type_hints/included_types", "/freebase/type_hints/mediator", "/freebase/documented_object/tip")

PROPERTY_IGNORE_PROPERTIES = ("name", "expected_type", "key", "id", "master_property", "delegated", "unique", "type", "schema",
            "/freebase/property_hints/disambiguator", "enumeration", "/freebase/property_hints/enumeration", 
            "/freebase/documented_object/tip")
