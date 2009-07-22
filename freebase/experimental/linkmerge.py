
import freebase, freebase.schema
from freebase.api import LITERAL_TYPE_IDS, MetawebError

from copy import deepcopy
import itertools
import logging

ALL_LINKS_QUERY = [{"type": "/type/link",
                    "source": {"id" : None},
                    "target": {"id" : None},
                    "target_value": None,
                    "master_property": { "id" : None, "expected_type" : None, "unique" : None },
                    "operation": None,
                    "valid": True }]

def merge(s, amoeba_id, target_id):
    # In merging, we'll use the analogy of phagocytosis.
    # http://en.wikipedia.org/wiki/Phagocytosis
    # In this example, the amoeba is the main guy who is swallowing the target

    # In cases where there is no merging problem, it doesn't matter who is the
    # amoeba and who is the target, but the final merge product will be in the amoeba

    # this merging will be done using links
    # effectively, we want to move everything that links to the target
    # and link it to the amoeba. This does present some issues:
    # some things just can't be moved (/en keys, for example).
    
    target_source_l, target_target_l, target_target_v_l = get_all_links(target_id)
    amoeba_source_l, amoeba_target_l, amoeba_target_v_l = get_all_links(amoeba_id)

    total_delete_query = {}
    total_write_query = { "id" : amoeba_id }

    # let's redirect all source and target links on target to amoeba
    #print [i for i in target_source_l]; print
    for link in target_source_l:
        # try this
        if link.master_property.expected_type != "/type/text" and \
            link.master_property.expected_type != "/type/key" and \
            link.master_property.id != "/type/object/permission" and \
            (not (link.master_property.unique and exists(amoeba_source_l, amoeba_target_l, link.master_property.id))):
            prop = link.master_property.id
            print prop
            current_prop = total_write_query.get(prop, [])
            current_prop.append({"id" : link.target.id, "connect" : "replace"})
            total_write_query[prop] = current_prop
            
            to_delete_prop = total_delete_query.get(prop, [])
            to_delete_prop.append({"id" : link.target.id, "connect" : "delete"})
            total_delete_query[prop] = to_delete_prop
            
    for link in target_target_l:
        if link.master_property.expected_type != "/type/text" and \
            link.master_property.expected_type != "/type/key" and \
            link.master_property.id != "/type/object/permission":
            
            prop = "!" + link.master_property.id
            print prop
            current_prop = total_write_query.get(prop, [])
            current_prop.append({"id" : link.source.id, "connect" : "replace"})
            total_write_query[prop] = current_prop
            
            to_delete_prop = total_delete_query.get(prop, [])
            to_delete_prop.append({"id" : link.source.id, "connect" : "delete"})
            total_delete_query[prop] = to_delete_prop
    
    # delete old
    badpropnames = set([])
    for propname, guys in total_delete_query.iteritems():
        new = dict({propname:guys, "id":target_id})
        try:
            s.mqlwrite(new)
        except MetawebError, me:
            print "Oh well, %s failed. %s" % (propname, me)
            badpropnames.add(propname)
    for badprop in badpropnames:
        del total_write_query[badprop]
    s.mqlwrite(total_write_query)
        
    
def exists(source_links, target_links, property_id):
    print "testing", property_id
    for link in itertools.chain(source_links, target_links):
        if link.master_property.id == property_id:
            if link.target and link.source:
                print "outta here", property_id
                return True
            return False
    return False
    


def get_all_links(the_id):
    source, target, target_value = [deepcopy(ALL_LINKS_QUERY) for i in range(3)]
    source[0].update(source={"id" : the_id})
    target[0].update(target={"id" : the_id})
    target_value[0].update(target_value={"id" : the_id })

    return (s.mqlreaditer(source),
            s.mqlreaditer(target),
            s.mqlreaditer(target_value))


if __name__ == '__main__':
    s = freebase.api.HTTPMetawebSession("http://sandbox-freebase.com")
    merge(s, "/guid/9202a8c04000641f800000000bc3141d", "/guid/9202a8c04000641f800000000aa5533e")