# TODO: copy /freebase/type_hints junk

from pprint import pprint
import random

from type_creation import create_type, create_property, delegate_property, reciprocate_property

from freebase.api  import HTTPMetawebSession, MetawebError

s = HTTPMetawebSession("http://sandbox-freebase.com")
s.login("nitromaster101", "something")

import time

def create_type_dependencies(s, base_id=None, type_id=None):
    
    if base_id:
        q = {"id" : base_id, "/type/domain/types" : [{"id" : None}] }
        results = s.mqlread(q)
        types = map(lambda x: x["id"], results["/type/domain/types"])
        #pprint(types)
    
    if type_id:
        types = [type_id]
        base_id = "/".join(type_id.split("/")[:-1])
        print base_id
    
    if not base_id and not type_id:
        raise Exception("You need to supply either a base_id or a type_id")
    
    graph = {}
    to_update = set(types)
    done = set()
    while len(to_update) > 0:
        new = to_update.pop()
        graph[new] = get_needed(s, new)
        [to_update.add(b) for b in graph[new]["related"] if b not in done]
        done.update(graph[new]["related"])
    
    # find distinct subgraphs (looking at needs)
    subgraphs = []
    unknown = set(graph.keys())
    while len(unknown) > 0:
        visited = set()
        to_visit = set([list(unknown)[0]])
        while len(to_visit) > 0:
            new = to_visit.pop()
            visited.add(new)
            try:
                unknown.remove(new)
            except KeyError:
                pass
            [to_visit.add(b) for b in graph[new]["related"] if b not in visited]
        subgraphs.append(list(visited))
    #pprint(subgraphs)
    
    pprint(graph)
    return
    
    # create type dependencies
    typegraph = {}
    for tid, idres in graph.items():
        typegraph[tid] = idres["needs"]
    
    least_needy_type = map(lambda (name, x): (len(x), name), typegraph.items())
    least_needy_type.sort()
    
    types_to_create = create_what(least_needy_type, typegraph)
    
    # create property dependencies
    propgraph = {}
    proptotype = {}
    for tid, idres in graph.items():
        for prop in idres["properties"]:
            propgraph[prop["id"]] = prop["needs"]
            proptotype[prop["id"]] = tid
    least_needy = map(lambda (name, x): (len(x), name), propgraph.items())
    least_needy.sort()
    
    props_to_create = create_what(least_needy, propgraph)
    
    domainname = "awesome" + str(int(random.random() * 1e10))
    print "\ndomainid", domainname
    print "--------------------------"
    dn = s.create_private_domain(domainname, domainname + "!")
    domain_id = dn.domain_id
    
    better_id = s.mqlread({"id" : domain_id, "a:id" : None})
    domain_id = better_id["a:id"]
    
    for type in types_to_create:
        print type
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
        create_type(s, graph[type]["name"]["value"], key, domain_id,
            included=map(lambda x: convert_name(x["id"], base_id, domain_id), graph[type]["/freebase/type_hints/included_types"]),
            cvt=graph[type]["/freebase/type_hints/mediator"],
            enum=graph[type]["/freebase/type_hints/enumeration"],
            tip=tip)
    
    print "--------------------------"
    
    for prop in props_to_create:
        info = graph[proptotype[prop]]["properties"]
        for i in info:
            if i["id"] == prop: 
                schema = convert_name(proptotype[prop], base_id, domain_id)
                print prop
                expected = None
                if i["expected_type"]:
                    expected = convert_name(i["expected_type"]["id"], base_id, domain_id)
                for k in i["key"]:
                    if k.namespace == proptotype[prop]:
                        key = k.value
                if i["/freebase/documented_object/tip"]:
                    tip = graph[type]["/freebase/documented_object/tip"]
                    
                if i['master_property']:
                    reciprocate_property(s, i["name"], key, convert_name(i["master_property"]["id"], base_id, domain_id),
                        i["unique"], disambig=i["/freebase/property_hints/disambiguator"], tip=tip)
                elif i['delegated']:
                    delegate_property(s, convert_name(i['delegated']['id'], base_id, domain_id), schema,
                        expected=expected, tip=tip)
                else:
                    create_property(s, i["name"], key, schema, expected, i["unique"], 
                        disambig=i["/freebase/property_hints/disambiguator"], tip=tip) 
                        
                
        
    
    print "\ndomain id was", domainname
    

def convert_name(old_name, operating_base, new_base):
    if old_name.startswith(operating_base):
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
       


def get_needed(s, type_id):
    #print type_id
    q = {
        "type" : "/type/type",
        "id" : type_id,
        "domain" : [{}],
        "expected_by" : [{}],
        "key" : [{"namespace" : None, "value" : None}],
        "name" : {"value" : None, "lang" : "/lang/en", "optional":True},
        "/freebase/type_hints/included_types" : [{}],
        "/freebase/type_hints/mediator" : None,
        "/freebase/type_hints/enumeration" : None,
        "/freebase/documented_object/tip" : {"value" : None, "limit":1, "optional":True},
        "properties" : [{
            "optional" : True,
            "delegated" : {},
            "enumeration" : None, 
            "expected_type" : {}, 
            "id" : None,
            "key" : [{
                "namespace" : None, 
                "value" : None
            }],
            #"link" : [{}], 
            "master_property" : {},
            "name" : {"value" : None, "lang" : "/lang/en", "optional":True}, 
            "reverse_property" : {}, 
            "schema" : {"id" : None, "name" : None},
            "unique" : None, 
            "unit" : None,
            "/freebase/documented_object/tip" : {"value" : None, "limit":1, "optional" : True},
            "/freebase/property_hints/disambiguator" : None
        }]  
    }
    
    r = s.mqlread(q)
    properties = r.properties
    
    #print "************************************************" + type_id
    #pprint(r)
    #print "************************************************" + type_id
    # hopefully there's only one domain
    fathers = map(lambda x: x["id"], r["domain"])
   
    brothers = set()
    included_types = map(lambda x: x["id"], r["/freebase/type_hints/included_types"])
    brothers.update(included_types)
    for prop in properties:
        if prop["expected_type"]:
            brothers.add(prop["expected_type"]["id"])
        
    
    family = return_relevant(brothers, fathers)
    needed = return_relevant(included_types, fathers)
    
    # get property information
    properties = r["properties"]
    for prop in properties:
        needs = set()
        if prop["master_property"]:
            needs.add(prop["master_property"]["id"])
        if prop["delegated"]:
            needs.add(prop["delegated"]["id"])
        
        prop["needs"] = return_relevant(needs, fathers)
    
    answer = r
    answer.update(related=family, needs=needed, properties=properties)
    
    return answer
    

def return_relevant(start_list, fathers):
    final = []
    for item in start_list:
        indomain = False
        for father in fathers:
            if item.startswith(father):
                indomain = True
                continue
        if indomain:
            final.append(item)
    return final

if __name__ == '__main__':
    
    create_type_dependencies(s, base_id="/people")
    
    