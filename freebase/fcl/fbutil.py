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


import re

import logging
log = logging.getLogger()


class FbException(Exception):
    pass

class CmdException(Exception):
    pass

media_types = {
            'html': ['text/html'],
            'txt':  ['text/plain'],

            'xml':  ['text/xml',
                     'application/xml'],

            'atom': ['application/atom+xml'],

            'js':   ['text/javascript',
                     'application/javascript',
                     'application/x-javascript'],

            'json': ['application/json'],

            'jpg':  ['image/jpeg',
                     'image/pjpeg'],

            'gif':  ['image/gif'],

            'png':  ['image/png'],
    }

extension_to_media_type = dict([(k,vs[0]) for k,vs in media_types.items()])
media_type_to_extension = {}
for k,vs in media_types.items():
    for v in vs:
        media_type_to_extension[v] = k




DIRSPLIT = re.compile(r'^(.+)/([^/]+)$')

def dirsplit_unsafe(id):
    m = DIRSPLIT.match(id)
    if m is None:
        return (None, id)
    dir,file = m.groups()
    return (dir,file)

def dirsplit(id):
    dir,file = dirsplit_unsafe(id)
    if dir == '/guid':
        raise FbException('%r is not a freebase keypath' % (id,))
    return (dir,file)

value_types = [
    '/type/text',
    '/type/key',
    '/type/rawstring',
    '/type/float',
    '/type/int',
    '/type/boolean',
    '/type/uri',
    '/type/datetime',
    '/type/id',
    '/type/enumeration',
    ]

default_propkeys = {
    'value': '/type/value/value',
    'id': '/type/object/id',
    'guid': '/type/object/guid',
    'type': '/type/object/type',
    'name': '/type/object/name',
    'key': '/type/object/key',
    'timestamp': '/type/object/timestamp',
    'permission': '/type/object/permission',
    'creator': '/type/object/creator',
    'attribution': '/type/object/attribution'
};
