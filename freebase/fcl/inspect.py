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


#
#
#  wrap all the nastiness needed for a general mql inspect query
#
#

import os, sys, re


null = None
true = True
false = False

inspect_query = {
          'name': null,
          'type': [],

          '/type/reflect/any_master': [{
            'optional':true,
            'id': null,
            'name': null,
            'link': {
              'master_property': {
                'id': null,
                'schema': null
              }
            }
          }],

          '/type/reflect/any_reverse': [{
            'optional':true,
            'id': null,
            'name': null,
            'link': {
              'master_property': {
                'id':null,
                'schema': null,
                'expected_type': null,
                'reverse_property': {
                  'id': null,
                  'schema': null,
                  'optional': true
                }
              }
            }
          }],

          '/type/reflect/any_value': [{
            'optional':true,
            'value': null,
            'link': {
              'master_property': {
                'id':null,
                'schema': null,
                'expected_type': null
              },
            }
          }],

          't:/type/reflect/any_value': [{
            'optional':true,
            'type': '/type/text',
            'value': null,
            'lang': null,
            'link': {
              'master_property': {
                'id':null,
                'schema': null
              },
            }
          }],
          
          '/type/object/creator': [{
            'optional':true,
            'id':null,
            'name':null
          }],
          '/type/object/timestamp': [{
            'optional':true,
            'value': null,
          }],

          '/type/object/key': [{
            'optional':true,
            'value': null,
            'namespace': null
          }],
          '/type/namespace/keys': [{
            'optional':true,
            'value': null,
            'namespace': null
          }]
}


def transform_result(result):
    proptypes = {}
    props = {}

    # copy a property from a /type/reflect clause
    def pushtype(propdesc, prop):
        tid = propdesc['schema']
        propid = propdesc['id']

        if isinstance(prop, dict):
            prop = dict(prop)
            if 'link' in prop:
                prop.pop('link')

        if tid not in proptypes:
            proptypes[tid] = {}
        if propid not in proptypes[tid]:
            proptypes[tid][propid] = []

        if propid not in props:
            props[propid] = []
        props[propid].append(prop)
    
    # copy a property that isn't enumerated by /type/reflect
    def pushprop(propid):
        ps = result[propid]
        if ps is None:
            return

        # hack to infer the schema from id, not always reliable!
        schema = re.sub(r'/[^/]+$', '', propid)
        keyprop = dict(id=propid, schema=schema)
        for p in ps:
            pushtype(keyprop, p)

    ps = result['/type/reflect/any_master'] or []
    for p in ps:
        propdesc = p.link.master_property
        pushtype(propdesc, p)

    # non-text non-key values
    ps = result['/type/reflect/any_value'] or []
    for p in ps:
        propdesc = p.link.master_property

        # /type/text values are queried specially
        #  so that we can get the lang, so ignore
        #  them here.
        if propdesc.expected_type == '/type/text':
            continue

        pushtype(propdesc, p)

    # text values
    ps = result['t:/type/reflect/any_value'] or []
    for p in ps:
        propdesc = p.link.master_property
        pushtype(propdesc, p)

    pushprop('/type/object/creator')
    pushprop('/type/object/timestamp')
    pushprop('/type/object/key')
    pushprop('/type/namespace/keys')

    # now the reverse properties
    ps = result['/type/reflect/any_reverse'] or []
    for prop in ps:
        propdesc = prop.link.master_property.reverse_property

        # synthetic property descriptor for the reverse of
        #  a property with no reverse descriptor.
        # note the bogus id starting with '-'.
        if propdesc is None:
            #  schema = prop.link.master_property.expected_type
            #  if schema is None:
            #      schema = 'other'

            schema = 'other'
            propdesc = dict(id='-' + prop.link.master_property.id,
                            schema=schema)

        pushtype(propdesc, prop)

    #return proptypes
    return props


def inspect_object(mss, id):
    q = dict(inspect_query)
    q['id'] = id
    r = mss.mqlread(q)
    if r is None:
        return None
    return transform_result(r)
