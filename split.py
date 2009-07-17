import freebase, freebase.schema
from freebase.api.session import LITERAL_TYPE_IDS

from copy import deepcopy

## TODO: CLONE TYPES

class AttributionNode(object):
    def __init__(self, s):
        self._dict = {}
        self.s = s
        
    def get(self, user):
        if self._dict.has_key(user):
            return self._dict[user]
        
        # create attribution node
        attribution_id = self.s.mqlwrite({"create" : "unconditional", 
                            "type": "/type/attribution",
                            "id" : None })["id"]
        self._dict[user] = attribution_id
        return self._dict[user]
    
    def set(self, user, attribution_id):
        self._dict[user] = attribution_id
        

s = freebase.api.HTTPMetawebSession("http://sandbox-freebase.com")

# let's determine the split locations
topic_id = "/en/the_beatles"

a = AttributionNode(s)

# get all types
type_query = {"id" : topic_id, "type" : [{"id" : None}]}
types = set([type_id["id"] for type_id in s.mqlread(type_query)["type"]])

split = set(["/music/artist"])
keep = types.difference(split)

properties_expected = {}
type_to_properties = {}

for type_id in split:
    expected_type_property_query = { "id" : type_id, 
                                     "type" : "/type/type",
                                     "properties" : [{
                                         "id" : None, 
                                         "expected_type" : None
                                     }]}
    r = s.mqlread(expected_type_property_query)
    all_properties = []
    if r:
        for prop in r["properties"]:
            prop_id = prop["id"]
            prop_expected_type = prop["expected_type"]
            properties_expected[prop_id] = prop_expected_type
            all_properties.append(prop)
    type_to_properties[type_id] = all_properties

# split

## create new object with new types and correct attribution
newname = s.mqlread({"id" : topic_id, "name" : None})["name"]
#attribution = s.mqlread({"id" : topic_id, "attribution" : None})["attribution"]
user_id = s.user_info()["id"]
attribution = a.get(user_id)

new_object_id = s.create_object(newname, included_types=list(split), 
                                create="unconditional",
                                attribution=attribution)["id"]

# import data from old
# if expected_type is primitive (in LITERAL_TYPE_IDS), then we look for value.
# Else, we look for id

mega_query = { "id" : topic_id }
for prop_id in properties_expected.iterkeys():
    mega_query.update({prop_id:[{}]})

res = s.mqlread(mega_query)

property_values = {}
for prop, value in res.iteritems():
    if prop in properties_expected.iterkeys():
        # if value is primitive
        if properties_expected[prop] in LITERAL_TYPE_IDS:
            property_values[prop] = [{"value" : b["value"]} 
                                        for b in res[prop]]
        else:
            property_values[prop] = [{"id" : b["id"]} 
                                        for b in res[prop]]

master_write_query = { "id" : new_object_id }
master_delete_query = { "id" : topic_id }
for prop, val in property_values.iteritems():
    if val:
        [v.update(connect="replace") for v in val]
        master_write_query.update({prop:val})
        deleteval = deepcopy(val)
        [dv.update(connect="delete") for dv in deleteval]
        master_delete_query.update({prop:deleteval})

# before we write, we have to delete all the old information
# this is because we don't can't have two similar guys connecting
# to the same cvt

# remove types (and properties from old)
# delete types
# (we can't get rid of included_types easily... not sure who depends on whom)
delete_types_query = { "id" : topic_id, 
                       "type":[{"id" : type_id, "connect" : "delete"}
                            for type_id in split]}
s.mqlwrite(delete_types_query)

# delete properties
s.mqlwrite(master_delete_query)

# add the data to the new guy
s.mqlwrite(master_write_query)
print "new object was", new_object_id
