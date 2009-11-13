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
from fbutil import *
from cmdutil import *

try:
    import simplejson as json
except ImportError:
    import json

import freebase.rison as rison
from freebase.api import attrdict

from freebase.schema import connect_object, disconnect_object

def cmd_help(fb, command=None):
    """get help on commands

    %prog help [cmd]
    """

    if command is not None:
        cmd = fb.commands[command]
        print '   %s: %s' % (cmd.name, cmd.shortdoc)
        print cmd.doc
        return

    print """
the interface to this tool is loosely modeled on the
"svn" command-line tool.  many commands work slightly
differently from their unix and svn equivalents - 
read the doc for the command first.

use "%s help <subcommand>" for help on a particular
subcommand.
""" % fb.progpath

    fb.oparser.print_help()

    print 'available subcommands:'
    cmds = sorted(fb.commands.keys())

    for fk in cmds:
        cmd = fb.commands[fk]
        print '   %s: %s' % (cmd.name, cmd.shortdoc)


def cmd_wikihelp(fb):
    """get help on commands in mediawiki markup format

    %prog wikihelp
    """

    print """usage: %s subcommand [ args ... ]

    the interface to this tool is loosely modeled on the
    "svn" command-line tool.  many commands work slightly
    differently from their unix and svn equivalents - 
    read the doc for the command first.
    """ % fb.progpath

    print 'subcommands:'
    for fk in sorted(fb.commands.keys()):
        cmd = fb.commands[fk]

        # mediawiki markup cares about the difference between
        #  a blank line and a blank line with a bunch of
        #  spaces at the start of it.  ewww.
        doc = re.sub(r'\r?\n {0,8}', '\n        ', cmd.doc)

        print '==== %s %s: %s ====' % (fb.progpath, cmd.name, cmd.shortdoc)
        print doc
        print


# this command is disabled because it relies on some svn glue that
# was not sufficiently well thought out.
def old_cmd_pwid(fb):
    """show the "current working namespace id"

    %prog pwid

    by default, relative ids can't be resolved.  however, if you
    run the fb tool from a directory that has the svn property
    'freebase:id' set, relative ids will be resolved relative
    to that id.  the idea is that you can create an svn tree
    that parallels the freebase namespace tree.  

    for example:
        $ %prog pwid

        $ svn propset freebase:id "/freebase" .

        $ %prog pwid
        /freebase

    """
    if fb.cwid is not None:
        print fb.cwid
    else:
        print ''


@option('long', '-l', default=False, action='store_true', help='show time and permission')
@option('timesort', '-t', default=False, action='store_true', help='sort by time')
@option('revsort', '-r', default=False, action='store_true', help='reverse sort order')
def cmd_ls(fb, path=None, long=False, timesort=False, revsort=False):
    """list the keys in a namespace

    %prog ls [id]
    """
    path = fb.absid(path)
    # ignore trailing /
    if len(path) > 1:
        path = re.sub('/$', '', path)

    kq = {
        'value': None,
        'namespace': {
            'id': None
        },
        'sort': 'value',
        'optional':True
     }

    if long or timesort:
        kq['link'] = {
            'timestamp': None,
            'creator': None
          }
    if timesort:
        kq['sort'] = 'link.timestamp'

    if revsort:
        kq['sort'] = '-' + kq['sort']

    q = {'id': path,
         '/type/namespace/keys': [kq]
         }

    r = fb.mss.mqlread(q)
    if r is None:
        raise CmdException('query for id %r failed' % path)

    #sys.stdout.write(' '.join([mk.value for mk in r['/type/namespace/keys']]))

    for mk in r['/type/namespace/keys']:
        if long:
            # trim off the /user/
            creator = re.sub('^/user/', '', mk.link.creator)
            timestamp = mk.link.timestamp
            fb.out(mk.value, creator, timestamp)
        else:
            fb.out(mk.value)

    if 0:
        suffix = ''
        if ('/type/namespace' in mk.namespace.type
            or '/type/domain' in mk.namespace.type):
            suffix = '/'
        print mk.value, mk.namespace.id+suffix



def cmd_mkdir(fb, path):
    """create a new freebase namespace
    %prog mkdir id

    create a new instance of /type/namespace at the given
    point in id space.  if id already exists, it should be
    a namespace.
    """
    path = fb.absid(path)
    # ignore trailing /
    path = re.sub('/$', '', path)
    dir,file = dirsplit(path)
    wq = { 'create': 'unless_exists',
           'key':{
               'connect': 'insert',
               'namespace': dir,
               'value': file
               },
           'name': path,
           'type': '/type/namespace'
         }

    r = fb.mss.mqlwrite(wq)

def cmd_ln(fb, src, dst):
    """create a namespace key
    %prog ln srcid dstid

    create a new namespace link at dstid to the object
    currently at srcid.
    """
    src = fb.absid(src)
    dst = fb.absid(dst)
    
    # ignore trailing /
    src = re.sub('/$', '', src)
    dst = re.sub('/$', '', dst)

    return connect_object(fb.mss, src, dst)

def cmd_rm(fb, path):
    """unlink a namespace key
    %prog rm id
    
    remove the /type/key that connects the given id to its
    parent.  id must be a path for this to make any sense.

    note that is like unix 'unlink' rather than 'rm'.
    it won't complain if the 'subdirectory' contains data,
    since that data will still be accessible to other queries.
    it's not like 'rm -rf' either, because it doesn't
    disturb anything other than the one directory entry.
    """
    path = fb.absid(path)
    # ignore trailing /
    path = re.sub('/$', '', path)

    return disconnect_object(fb.mss, path)

def cmd_mv(fb, src, dst):
    """rename srcid to dstid.
    %prog mv srcid dstid

    equivalent to:
    $ fb ln <srcid> <dstid>
    $ fb rm <srcid>
    """
    cmd_ln(fb, src, dst)
    cmd_rm(fb, src)

def cmd_cd(fb, path):
    path = fb.absid(path)
    fb.pwd = path

def cmd_pwd(fb):
    print fb.pwd

def cmd_cat(fb, id, include_headers=False):
    """download a document from freebase to stdout
    %prog cat id

    equivalent to "%prog get id -".
    """
    return cmd_get(fb, id, localfile='-', include_headers=include_headers)

def cmd_shell(fb):
    import readline
    import shlex
    def complete_cmd(text, state):
        m = [ c for c in fb.commands if c.startswith(text) ]
        return m[state]

    readline.set_completer(complete_cmd)
    readline.parse_and_bind('tab: complete')
    graphs = {
        'http://trunk.qa.metaweb.com':'qa',
        'http://branch.qa.metaweb.com':'qa',
        'http://www.freebase.com':'otg',
        'http://api.freebase.com':'otg',
        'http://freebase.com':'otg',
        'http://www.sandbox-freebase.com':'sandbox',
        'http://api.sandbox-freebase.com':'sandbox',
        'http://sandbox-freebase.com':'sandbox'
    }

    gname = graphs.get(fb.mss.service_url, 'unknown')
    while True:
        try:
            line = raw_input((fb.mss.username+'@' if fb.mss.username else '') +gname+': '+fb.pwd+' > ')
        except EOFError:
            print
            break

        if line:
            args = shlex.split(line)
            cmd = args.pop(0)
            if cmd in fb.commands:
                fb.dispatch(fb.commands[cmd], args, {});
            else:
                print >>sys.stderr, "No such command: "+cmd
        
def cmd_get(fb, id, localfile=None, include_headers=False):
    """download a file from freebase
    %prog get id [localfile]

    download the document or image with the given id from freebase
    into localfile.  localfile '-' means stdout.  localfile
    defaults to a file in the current directory with the same name
    as the last key in the path, possibly followed by a metadata
    extension like .html or .txt.
    """
    id = fb.absid(id)
    dir,file = dirsplit_unsafe(id)

    def read_content(id, content_only=False):
        c = attrdict(id=id)
        cq = { 'id': id,
               'type': [],
               '/common/document/content': None,
               '/common/document/source_uri': None,
               '/type/content/media_type': { 'name':None,
                                             'optional': True },
               #'/type/content/text_encoding': { 'name':None },
               '/type/content/blob_id':None,
             }
        cd = fb.mss.mqlread(cq)
        if cd is None:
            raise CmdException('no match for id %r' % id)
        
        if '/type/content' in cd.type:
            c.media_type = cd['/type/content/media_type'].name
            #c.text_encoding = cd['/type/content/text_encoding'].name
            c.sha256 = cd['/type/content/blob_id']
            return c

        if content_only:
            raise CmdException('%s is not a content id' % id)

        cid = cd['/common/document/content']
        if cid is not None:
            return read_content(cid, content_only=True)

        # in this case we don't have a content object
        if cd['/common/document/source_uri'] is not None:
            return None

        raise CmdException('%s is not a content or document id' % id)


    content = read_content(id)
    log.debug('COBJ %r' % content)
    if content is not None:
        fileext = media_type_to_extension.get(content.media_type, None)
    else:
        fileext = None

    if localfile == '-':
        ofp = sys.stdout
    else:
        if localfile is None:
            implicit_outfile = True
            localfile = file
        elif re.match(r'[/\\]$', localfile):
            implicit_outfile = True
            localfile = localfile + file
        else:
            implicit_outfile = False
        localfile = os.path.abspath(localfile)

        # add file extension based on content-type:
        #  should be an option to disable this
        if implicit_outfile and fileext is not None:
            localfile += '.' + fileext

        # if we didn't explicitly name the output file,
        #  don't destroy an existing file
        localfile_base = localfile
        count = 0
        while implicit_outfile and os.path.exists(localfile):
            count += 1
            localfile = '%s.%d' % (localfile_base, count)
        ofp = open(localfile, 'wb')

    body = fb.mss.trans(id)

    if include_headers:
        # XXX show content-type, what else?
        pass

    ofp.write(body)

    if localfile != '-':
        print ('%s saved (%d bytes)' % (localfile, len(body)))
        ofp.close()


def cmd_put(fb, localfile, id=None, content_type=None):
    """upload a document to freebase   -- EXPERIMENTAL
    %prog put localfile [id] [content-type]

    upload the document or image in localfile to given freebase
    id.  if localfile is '-' the data will be read from stdin.

    if id is missing or empty, a new document will be created.
    later the id might default to something computed from localfile
    and any svn attributes it has.

    output: a single line, the id of the document.
    """
    if content_type is None:
        ext = re.sub('^.*\.([^/.]+)$', r'\1', localfile)
        media_type = extension_to_media_type.get(ext, None)

        if media_type is None:
            raise CmdException('could not infer a media type from extension %r: please specify it'
                               % ext)

        if media_type.startswith('text/'):
            # this is a bad assumption.  should sniff it?
            text_encoding = 'utf-8'
            content_type = '%s;charset=%s' % (media_type, text_encoding)
        else:
            content_type = media_type

    new_id = None
    if id is not None:
        idinfo = fb.mss.mqlread({ 'id': id, 'type': '/common/document' })
        if idinfo is None:
            new_id = id
            id = None

    body = open(localfile, 'rb').read()
    r = fb.mss.upload(body, content_type, document_id=id)

    if new_id is None:
        print r.document
    else:
        cmd_ln(fb, r.document, new_id)
        print new_id


def cmd_dump(fb, id):
    """show all properties of a freebase object
    %prog dump object_id
    """
    id = fb.absid(id)

    import inspection

    r = inspection.inspect_object(fb.mss, id)
    if r is None:
        raise CmdException('no match for id %r' % id)

    for k in sorted(r.keys()):
        vs = r[k]
        for v in vs:
            id = v.get('id', '')

            name = '%r' % (v.get('name') or v.get('value'))
            if name == 'None': name = ''

            type = v.get('type', '')
            if type == '/type/text':
                extra = v.get('lang', '')
            elif type == '/type/key':
                extra = v.get('namespace', '')
            else:
                extra = ''

            fb.out(k, id, name, type, extra)
                    

def cmd_pget(fb, id, propid):
    """get a property of a freebase object  -- EXPERIMENTAL
    %prog pget object_id property_id

    get the property named by property_id from the object.

    XXX output quoting is not well specified.

    property_id must be a fully qualified id for now.

    prints one line for each match.

    if propid ends in '*' this does a wildcard for a particular type.
    """
    id = fb.absid(id)
    proptype, propkey = dirsplit(propid)

    if propkey != '*':
        # look up the prop
        q = { 'id': id,
               propid: [{}],
             }
        r = fb.mss.mqlread(q)
        for v in r[propid]:
            if 'value' in v:
                print v.value
            else:
                print v.id

    else:
        # look up the prop
        q = { 'id': id,
               '*': [{}],
             }
        if isinstance(proptype, basestring):
            q['type'] = proptype

        r = fb.mss.mqlread(q)

        for k in sorted(r.keys()):
            v = r[k];
            if 'value' in v:
                print '%s %s' % (k, v.value)
            else:
                print '%s %s' % (k, v.id)

def cmd_pdel(fb, id, propid, oldval):
    """delete a property of a freebase object   -- EXPERIMENTAL
    %prog pdel object_id property_id oldvalue

    set the property named by property_id on the object.
    value is an id or a json value.  XXX this is ambiguous.

    property_id must be a fully qualified id for now.

    for now you need to provide a "oldval" argument,
    later this tool will query and perhaps prompt if the
    deletion is ambiguous.

    prints a single line, either 'deleted' or 'missing'
    """
    return cmd_pset(fb, id, propid, None, oldval)


def cmd_touch(fb):
    """bypass any cached query results the service may have.  use sparingly.
    """
    fb.mss.mqlflush()


def cmd_pset(fb, id, propkey, val, oldval=None, extra=None):
    """set a property of a freebase object  -- EXPERIMENTAL
    %prog pset object_id property_id value

    set the property named by property_id on the object.
    value is an id or a json value.  XXX this is ambiguous.

    property_id must be a fully qualified id for now.

    if the property should be a unique property, this will
    write with 'connect:update'.  if the property may have
    multiple, it is written with 'connect:insert'.

    prints a single line, either 'inserted' or 'present'
    """
    id = fb.absid(id)

    propid = fb.absprop(propkey)

    # look up the prop
    pq = { 'id': propid,
           'type': '/type/property',
           'name': None,
           'unique': None,
           'expected_type': {
               'id':   None,
               'name': None,
               'default_property': None,
               'optional': True,
           },
         }

    prop = fb.mss.mqlread(pq)

    if prop is None:
        raise CmdException('can\'t resolve property key %r - use an absolute id' % propid);

    if propid.startswith('/type/object/') or propid.startswith('/type/value/'):
        propkey = re.sub('/type/[^/]+/', '', propid);
    else:
        propkey = propid

    wq = { 'id': id,
           propkey: {
           }
         }

    if val is None:
        val = oldval
        wq[propkey]['connect'] = 'delete'
    elif prop.unique:
        wq[propkey]['connect'] = 'update'
    else:
        wq[propkey]['connect'] = 'insert'

    if prop.expected_type is None:
        wq[propkey]['id'] = val
    elif prop.expected_type.id not in value_types:
        wq[propkey]['id'] = val
    elif prop.expected_type.id == '/type/float':
        wq[propkey]['value'] = float(val)
    elif prop.expected_type.id == '/type/int':
        wq[propkey]['value'] = int(val)
    elif prop.expected_type.id == '/type/boolean':
        wq[propkey]['value'] = bool(val)
    elif prop.expected_type.id == '/type/text':
        wq[propkey]['value'] = val
        if extra is not None:
            lang = extra
        else:
            lang = '/lang/en'
        wq[propkey]['lang'] = lang
    elif prop.expected_type.id == '/type/key':
        wq[propkey]['value'] = val
        if extra is not None:
            wq[propkey]['namespace'] = extra
        else:
            raise CmdException('must specify a namespace to pset /type/key')
    else:
        wq[propkey]['value'] = val


    r = fb.mss.mqlwrite(wq)
    print r[propkey]['connect']
    
def cmd_login(fb, username=None, password=None):
    """login to the freebase service
    %prog login [username [password]]

    cookies are maintained in a file so
    they are available to the next invocation.
    prompts for username and password if not given
    """
    import getpass
    if username is None:
        sys.stdout.write('freebase.com username: ')
        username = sys.stdin.readline()
        if not username:
            raise CmdException('usernmae required for login')
        username = re.compile('\n$').sub('', username)
    if password is None:
        password = getpass.getpass('freebase.com password: ')

    fb.mss.username = username
    fb.mss.password = password
    fb.mss.login()

def cmd_logout(fb):
    """logout from the freebase service
    %prog logout

    deletes the login cookies
    """
    fb.cookiejar.clear(domain=fb.service_host.split(':')[0])


def cmd_find(fb, qstr):
    """print all ids matching a given constraint.

    if the query string starts with "{" it is treated as json.
    otherwise it is treated as o-rison.

    %prog find
    """
    if qstr.startswith('{'):
        q = simplejson.loads(qstr)
    else:
        q = rison.loads('(' + qstr + ')')

    if 'id' not in q:
        q['id'] = None

    results = fb.mss.mqlreaditer(q)
    for r in results:
        fb.out(r.id)


def cmd_q(fb, qstr):
    """run a freebase query.

    if the query string starts with "{" it is treated as json.
    otherwise it is treated as o-rison.

    dump the result as json.
    
    %prog q
    """
    if qstr.startswith('{'):
        q = simplejson.loads(qstr)
    else:
        q = rison.loads('(' + qstr + ')')

    # done this way for streaming
    first = True
    for result in fb.mss.mqlreaditer(q):
        if first:
            first = False
            print '[',
        else:
            print ',',
        print simplejson.dumps(result, indent=2),
    print ']'

def cmd_open(fb, id):
    """open a web browser on the given id.  works on OSX only for now.
    
    %prog open /some/id
    """
    os.system("open 'http://www.freebase.com/view%s'" % id)


def cmd_log(fb, id):
    """log changes pertaining to a given id.

    INCOMPLETE
    
    %prog log /some/id
    """

    null = None
    true = True
    false = False

    baseq = {
            'type': '/type/link',
            'source': null,
            'master_property': null,
            'attribution': null,
            'timestamp': null,
            'operation': null,
            'valid': null,
            'sort': '-timestamp'
        };
    
    queries = [
        {
        'target_value': { '*': null },
        'target': { 'id': null, 'name': null, 'optional': true },
        },
        {
        'target': { 'id': null, 'name': null },
        }]

    for i,q in list(enumerate(queries)):
        q.update(baseq)
        queries[i] = [q]


    valuesfrom,linksfrom = fb.mss.mqlreadmulti(queries)

    for link in linksfrom:
        # fb.trow(link.master_property.id, ...)
        print simplejson.dumps(link, indent=2)

    for link in valuesfrom:
        # fb.trow(link.master_property.id, ...)
        print simplejson.dumps(link, indent=2)

    

def cmd_search(fb, what):
    """Search freebase for "query" and print out 10 matching ids
    
    %prog search "some query" 
    """
        
    r = fb.mss.search(what, format="ids", limit=10)
    for id in r:    
        print id
    
