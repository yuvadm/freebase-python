
from freebase.api.session import HTTPMetawebSession
from freebase.api.session import get_key_namespace, LITERAL_TYPE_IDS

def key_exists(s, k):
    q = {
        "id" : k,
        "guid" : None
    }
    return not None == s.mqlread(q)


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


def copy_property(s, id, newid, **extra):
    newname, newschema = get_key_namespace(newid)
    
    info = get_property_info(s, id)
    info["__raw"].update(extra)
    create_property(s, info["name"], newname, newschema, info["expected_type"], info["unique"], info["/freebase/property_hints/disambiguator"],
        info["/freebase/documented_object/tip"], info["__raw"])

def move_property(s, id, newid, **extra):
    copy_property(s, id, newid, **extra)
    disconnect_schema = {"type" : "/type/property", "schema" : {"connect" : "delete", "id" : "/".join(id.split("/")[:-1]) }}    
    s.disconnect_object(id, extra = disconnect_schema)

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
            elif isinstance(res[i], bool):
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
def create_type(s, name, key, ns, cvt=None, tip=None, included=None, extra=None):
    if key_exists(s, ns + "/" + key ):
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
        itsq = [{
            "id|=" : included,
            "/freebase/type_hints/included_types" : [{"id" : None}]
        }]
        r = s.mqlread(itsq)
        included_types = set(included)
        if r:
            for i in r:
                included_types.update(map(lambda x: x["id"], i["/freebase/type_hints/included_types"]))

        its = [{"connect" : "insert", "id" : t} for t in included_types]
        q['/freebase/type_hints/included_types'] = its

    # TODO: enum

    if cvt:
        q['/freebase/type_hints/mediator'] = { "connect" : "update", "value" : True }
    if tip:
        q['/freebase/documented_object/tip'] = { "connect" : "update", "value" : tip, "lang" : "/lang/en" }
    
    if extra: q.update(extra)
    return s.mqlwrite(q, use_permission_of=ns)


# Create Property
def create_property(s, name, key, schema, expected, unique=False, disambig=False, tip=None, extra=None):
    if key_exists(s, schema + "/" + key):
        # this isn't (neccesarily) a problem
        # raise Exception("The key \"%s\" already exists!" % (schema + "/" + key))
        return

    # validate parameters str

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

def delegate_property(s, p, schema, name=None, key=None, expected=None, tip=None, extra=None):
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
                raise Exception("You can't set the expected_type if the expected_type of the delegated (master) is a primitive")
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


    q = {
        "id" : master,
        "/type/property/expected_type" : None,
        "/type/property/schema" : None }
    r = s.mqlread(q)
    ect = r["/type/property/expected_type"]
    schema = r["/type/property/schema"]

    master = {"master_property" : master}
    if extra: master.update(extra)

    # NOTE: swapping ect and schema; see comment above
    return create_property(s, name, key, ect, schema, unique, disambig, tip,
        extra = master)

# upload / restore types
def dump_base(s, base_id):
    types = map(lambda x: x["id"], s.mqlread({"id" : base_id, "/type/domain/types":[{"id" : None}]})["/type/domain/types"])
    graph = _get_graph(s, types, True)
    graph["__follow_types"] = True
    
    return graph

def dump_type(s, type_id, follow_types=True):
    types = [type_id]
    graph = _get_graph(s, types, follow_types)
    graph["__follow_types"] = follow_types
    
    return graph
    

def restore(s, graph, new_location, ignore_types=None, debug=False):
    follow_types = graph.get("__follow_types", True)
    if debug: print "Following types:", follow_types
    
    # create type dependencies
    typegraph = {}
    for tid, idres in graph.items():
        if not tid.startswith("__"):
            typegraph[tid] = idres["__requires"]
    
    type_deps = map(lambda (name, x): (len(x), name), typegraph.iteritems())
    type_deps.sort()
    if follow_types:
        types_to_create = create_what(type_deps, typegraph)
    else:
        types_to_create = typegraph.keys()
    
    # create property dependencies
    propgraph = {}
    proptotype = {}
    for tid, idres in graph.items():
        if not tid.startswith("__"):
            for prop in idres["properties"]:
                propgraph[prop["id"]] = prop["__requires"]
                proptotype[prop["id"]] = tid
    prop_deps = map(lambda (name, x): (len(x), name), propgraph.items()) #*
    prop_deps.sort()
    if follow_types:
        props_to_create = create_what(prop_deps, propgraph)
    else:
        props_to_create = propgraph.keys()
    
    if debug: print "types", types_to_create
    if debug: print "-----------------------"
    if debug: print "props", props_to_create
    
    base_id, domain_id = s.mqlreadmulti([{"id" : types_to_create[0], "type" : "/type/type", "domain" : {"id" : None}},
                                         {"id" : new_location, "a:id" : None}])                         
    base_id = base_id["domain"]["id"]
    domain_id = domain_id["a:id"]
    
    only_include = types_to_create + props_to_create
    
    for type in types_to_create:
        if debug: print type
        key = ""
        if len(graph[type]["key"]) == 1:
            key = graph[type]["key"][0]["value"]
        else:
            expectedname = graph[type]["id"].split("/")[-1]
            if base_id:
                for group in graph[type]["key"]:
                    if group["namespace"] == base_id:
                        key = group["value"]
                        continue
            if key is None:
                key = expectedname
        tip = None
        if graph[type]["/freebase/documented_object/tip"]:
            tip = graph[type]["/freebase/documented_object/tip"]["value"]
        
        ignore = ("name", "domain", "key", "type", "id", "properties", "/freebase/type_hints/enumeration",
                    "/freebase/type_hints/included_types", "/freebase/type_hints/mediator", "/freebase/documented_object/tip")
        extra = {}
        for k, v in graph[type].items():
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
                        raise Exception("There is a problem with getting the property value.")
        
        create_type(s, graph[type]["name"]["value"], key, domain_id,
            included=map(lambda x: convert_name(x["id"], base_id, domain_id, only_include), graph[type]["/freebase/type_hints/included_types"]),
            cvt=graph[type]["/freebase/type_hints/mediator"],
            tip=tip, extra=extra)

    
    if debug: print "--------------------------"
    
    for prop in props_to_create: #* prop_id
        info = graph[proptotype[prop]]["properties"]
        for i in info:
            if i["id"] == prop: 
                
                schema = convert_name(proptotype[prop], base_id, domain_id, only_include)
                if debug: print prop
                expected = None
                
                if i["expected_type"]:
                    expected = convert_name(i["expected_type"], base_id, domain_id, only_include)
                for k in i["key"]:
                    if k["namespace"] == proptotype[prop]:
                        key = k["value"]
                if i["/freebase/documented_object/tip"]:
                    tip = graph[type]["/freebase/documented_object/tip"]
                
                disambig = i["/freebase/property_hints/disambiguator"]
                
                ignore = ("name", "expected_type", "key", "id", "master_property", "delegated", "unique", "type", "schema",
                            "/freebase/property_hints/disambiguator", "enumeration", "/freebase/property_hints/enumeration", 
                            "/freebase/documented_object/tip")
                extra = {}
                for k, v in i.items():
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
                                raise Exception("There is a problem with getting the property value.")
                            
                            # since we are creating a property, all these connect insert delicacies are unneccesary    
                            """if isinstance(v, basestring) and v.startswith("/"): # an id
                                extra.update({k : {"connect" : "insert", "id" : v}})
                            elif isinstance(v, bool): # a bool value
                                extra.update({k : {"connect" : "insert", "value" : v}})
                            else: # an english value
                                extra.update({k : {"connect" : "insert", "value" : v, "lang" : "/lang/en"}})"""
                
                
                if i['master_property']:
                    converted_master_property = convert_name(i["master_property"], base_id, domain_id, only_include)
                    if converted_master_property == i["master_property"]:
                        raise Exception("You can't set follow_types to False if there's a cvt. A cvt requires you get all the relevant types. Set follow_types to true.\n" + \
                                        "The offending property was %s, whose master was %s." % (prop["id"], prop["master_property"]))
                    reciprocate_property(s, i["name"], key, converted_master_property,
                        i["unique"], disambig=disambig, tip=tip, extra=extra)
                
                elif i['delegated']:
                    delegate_property(s, convert_name(i['delegated'], base_id, domain_id, only_include), schema,
                        expected=expected, tip=tip, extra=extra)
                
                else:
                    create_property(s, i["name"], key, schema, expected, i["unique"], 
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
            # ugly things happen (we can't include the cvt)
            for prop in graph[new]["properties"]:
                if prop["master_property"]:
                    raise Exception("You can't set follow_types to False if there's a cvt. A cvt requires you get all the relevant types. Set follow_types to true.\n" + \
                                    "The offending property was %s, whose master was %s." % (prop["id"], prop["master_property"]))
    return graph


def convert_name(old_name, operating_base, new_base, only_include=None):
    if old_name in only_include and old_name.startswith(operating_base):
        return new_base + old_name.replace(operating_base, "", 1)
    else:
        return old_name

def create_what(deps, graph):
    create_list = []
    while len(deps) > 0:
        neediness, id = deps.pop(0)
        if neediness == 0:
            create_list.append(id)
            continue
        else:
            work = True
            for req in graph[id]:
                if req not in create_list:
                    work = False
                    continue
            if work:
                create_list.append(id)
            else:
                deps.append((neediness, id))
    return create_list        



def _get_needed(s, type_id):
    q = TYPE_QUERY
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

    related = return_relevant(related_types, parents)
    requires = return_relevant(included_types, parents)

    # get property information
    properties = r["properties"]
    for prop in properties:
        dependent_on = set()
        if prop["master_property"]:
            dependent_on.add(prop["master_property"])
        if prop["delegated"]:
            dependent_on.add(prop["delegated"])

        prop["__requires"] = return_relevant(dependent_on, parents)

    # return all the information along with our special __* properties
    info = r
    info.update(__related=related, __requires=requires, __properties=properties)

    return info


def return_relevant(start_list, parents):
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
        #"link" : [{}], 
        "master_property" : None,
        "name" : {"value" : None, "lang" : "/lang/en", "optional":True}, 
        "schema" : {"id" : None, "name" : None},
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
TYPE_QUERY.update(properties=[PROPERTY_QUERY])    

