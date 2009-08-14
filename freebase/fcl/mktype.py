# ==================================================================
# Copyright (c) 2007,2008,2009 Metaweb Technologies, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above
#       copyright notice, this list of conditions and the following
#       disclaimer in the documentation and/or other materials provided
#       with the distribution.
# 
# THIS SOFTWARE IS PROVIDED BY METAWEB TECHNOLOGIES AND CONTRIBUTORS
# ``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL METAWEB
# TECHNOLOGIES OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
# ====================================================================

import os, sys, re, time
from cmdutil import *
from fbutil import *

from freebase.schema import create_object, create_type

def cmd_mkobj(fb, id, typeid='/common/topic', name=''):
    """create a new object with a given type  -- EXPERIMENTAL
    %prog mkobj new_id typeid name

    create a new object with type typeid at the given
    namespace location.

    if present, name gives the display name of the new object.
    
    """
    id = fb.absid(id)
    
    return create_object(fb.mss, name="", path=id, 
                        included_types=type_id, create="unless_exists")
                
def cmd_mktype(fb, id, name=''):
    """create a new type  -- EXPERIMENTAL
    %prog mktype new_id name

    create a new object with type Type at the given
    namespace location.

    this doesn't create any type hints.

    if present, name gives the display name of the new property
    
    For more options when creating a type, use the python library
    """
    id = fb.absid(id)
    ns, key = dirsplit(id)
    return create_type(s, name, key, ns, cvt=False, tip=None, included=None, extra=None)

def mkprop(fb, typeid, key, name='', vtype=None, master_property=None):
    """helper to create a new property
    """
    if name == '':
        name = key

    wq = { 'create': 'unless_exists',
           'id': None,
           'type': '/type/property',
           'name': name,
           'schema': typeid,
           'key': {
               'namespace': typeid,
               'value': key
            }
         }

    if vtype is not None:
        wq['expected_type'] = vtype
    if master_property is not None:
        wq['master_property'] = master_property

    return fb.mss.mqlwrite(wq)


def cmd_mkprop(fb, id, name='', vtype=None, revkey=None, revname=''):
    """create a new property  -- EXPERIMENTAL
    %prog mkprop new_id [name] [expected_type] [reverse_property] [reverse_name]

    create a new object with type Property at the given
    location.  creates both the "schema" and "key" links
    for the property, but doesn't create any freebase property
    hints.

    if present, name gives the display name of the new property
    """
    id = fb.absid(id)
    if vtype is not None:
        vtype = fb.absid(vtype)

    typeid, key = dirsplit(id)


    r = mkprop(fb, typeid, key, name, vtype)

    # write the reverse property if specified

    print r.id, r.create

    if revkey is None:
        return

    assert vtype is not None

    rr = mkprop(fb, vtype, revkey, revname, typeid, id)
    print rr.id, rr.create


def cmd_publish_type(fb, typeid):
    """try to publish a freebase type for the client
    %prog publish_type typeid

    set /freebase/type_profile/published to the /freebase/type_status
    instance named 'Published'
  

    should also try to set the domain to some namespace that
    has type:/type/domain

    """
    id = fb.absid(typeid)

    w = {
        'id': id,
        '/freebase/type_profile/published': {
            'connect': 'insert',
            'type': '/freebase/type_status',
            'name': 'Published'
        }
    }
    r = fb.mss.mqlwrite(w)

    print r['/freebase/type_profile/published']['connect']
