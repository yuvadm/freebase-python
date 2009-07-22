import freebase, freebase.schema
from freebase.api import LITERAL_TYPE_IDS

import logging

def merge(s, amoeba_id, target_id):
    # We'll merge by types. This isn't really an issue, since everything
    # displayed in the UI is by types

    # In merging, we'll use the analogy of phagocytosis.
    # http://en.wikipedia.org/wiki/Phagocytosis
    # In this example, the amoeba is the main guy who is swallowing the target

    # types_to_merge = set(["/common/topic"]) let's merge all for now.

    # In cases where there is no merging problem, it doesn't matter who is the
    # amoeba and who is the target, but the final merge product will be in the amoeba

    # get all the properties of amoeba+target
    amoeba_types = get_types(amoeba_id)
    target_types = get_types(target_id)
    all_types = amoeba_types.union(target_types)

    properties_unique = {}
    properties_expected = {}
    type_to_properties = {}

    for type_id in all_types:
        unique_property_query = { "id" : type_id, 
                                   "type" : "/type/type",
                                   "properties" : [{
                                        "id" : None, 
                                        "unique" : None,
                                        "expected_type" : None
                                    }] }
        r = s.mqlread(unique_property_query)
        
        all_properties = []
        if r:
            for prop in r["properties"]:
                properties_unique[prop.id] = prop.unique
                properties_expected[prop.id] = prop.expected_type
                all_properties.append(prop)
        type_to_properties[type_id] = all_properties

    # type amoeba with new types in target
    for type_id in target_types:
        freebase.schema.add_type_to_object(s, amoeba_id, type_id)

    # get all properties of target
    mega_target_query = { "id" : target_id }
    mega_amoeba_query = { "id" : amoeba_id }
    for type_id in target_types:
        for prop_id in type_to_properties[type_id]:
            mega_target_query.update({prop_id["id"]:[{}]})
    for type_id in amoeba_types:
        for prop_id in type_to_properties[type_id]:
            mega_amoeba_query.update({prop_id["id"]:[{}]})
        

    # for every non-empty property in target:
    #  1. if it doesn't exist in amoeba, add replace-style
    #  2. if it does exist in amoeba:  if the property is unique, do nothing
    #                                  if property is not unique, just add replace

    target_result, amoeba_result = s.mqlreadmulti([mega_target_query, mega_amoeba_query])

    property_values = {}
    for prop, value in target_result.iteritems():
        if prop in properties_unique.iterkeys():
            # if value is primitive
            if properties_expected[prop] in LITERAL_TYPE_IDS:
                property_values[prop] = [{"value" : b["value"]} 
                                            for b in value]
            else:
                property_values[prop] = [{"id" : b["id"]} 
                                            for b in value]
    
    master_write_amoeba_query = { "id" : amoeba_id }
    for prop, val in property_values.iteritems():
        if val:
            if amoeba_result.has_key(prop) and amoeba_result[prop]:
                # if property is unique, do nothing
                # if property is not unique, just add replace
                if not properties_unique[prop]:
                    [b.update(connect="replace") for b in val]
                    master_write_amoeba_query.update({prop:val})
                
            else:
                [b.update(connect="replace") for b in val]
                master_write_amoeba_query.update({prop:val})
    
    # delete target information
    
        
    # write amoeba information
    s.mqlwrite(master_write_amoeba_query)
    
    # make name of target an alias in amoeba
    get_amoeba_name_query = {"id" : amoeba_id,
                             "name" : None }
    get_target_alias_query = {"id" : target_id,
                              "/common/topic/alias" : [{}] }
    amoeba_name, target_aliases = s.mqlread([get_amoeba_name_query,
                                            get_target_alias_query])
    # TODO:
    #set_alias_query = {"id" : amoeba_id}
    #for alias in target_aliases["/common/topic/alias"]:
    #    if alias.value != amoeba_name:
    #        set_alias_query.update({"lang": "/lang/en",
    #        "value": "Beeetles",
    #        "connect": "insert"})
    
    # migrate data (thinks linking here)
    # get all the links from the target to someone else

def get_types(topic_id):
    type_query = {"id" : topic_id, "type" : [{"id" : None}]}
    return set([type_obj["id"] for type_obj in s.mqlread(type_query)["type"]])
    

if __name__ == '__main__':
    s = freebase.api.HTTPMetawebSession("http://sandbox-freebase.com")
    
    """console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)

    s.log.setLevel(logging.DEBUG)
    s.log.addHandler(console)"""

    merge(s, "/guid/9202a8c04000641f800000000bc3141d", "/guid/9202a8c04000641f800000000aa5533e")
    #merge(s, "/en/the_beatles", "/en/the_police")