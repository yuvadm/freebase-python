from freebase.schema import dump_base, dump_type, restore

try:
    import jsonlib2 as json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        import json

import sys

def cmd_dump_base(fb, baseid):
    """dump a base to stdout
    %prog dump_base baseid

    Dump a base by outputting a json representation
    of the types and properties involved.
    """
    print >> sys.stdout, json.dumps(dump_base(fb.mss, baseid), indent=2)

def cmd_dump_type(fb, baseid, follow_types=True):
    """dump a type to stdout
    %prog dump_type typeid [follow_types=True]

    Dump a type by outputting a json representation
    of the type and properties involved.
    """
    print >> sys.stdout, json.dumps(dump_type(fb.mss, typeid, follow_types), indent=2)

def cmd_restore(fb, newlocation, graphfile):
    """restore a graph object to the graph
    %prog restore newlocation graphfile

    Restore a graph object to the newlocation
    """
    fh = open(graphfile, "r")
    graph = json.loads(fh.read())
    fh.close()
    return restore(fb.mss, graph, newlocation, ignore_types=None)

