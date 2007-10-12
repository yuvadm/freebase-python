# ========================================================================
# Copyright (c) 2007, Metaweb Technologies, Inc.
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
# ========================================================================

#
# URI Templating in Python
#
# see http://bitworking.org/projects/URI-Templates/
#  and http://bitworking.org/news/URI_Templates
#
# this implementation can also parse URIs, as long as the
#   template is sufficiently specific.  to allow this to work
#   the '/' character is forbidden in keys when parsing.  
#   later it should be possible to loosen this restriction.
#
# TODO:
#   simplify the syntax calling in - currently
#     uri = new URITemplate(ut.template).run({...})
#   allow parsing to be aware of www. and trailing /
#   nail down quoting issues
#

import os, sys, re

class URITemplate(object):
    VARREF = re.compile(r'\{([0-9a-zA-Z_]+)\}')

    def __init__(self, s):
        self.template = s;

        self.params = []
        tsplit = self.VARREF.split(s)
        rxs = ['^']
        for i in range(len(tsplit)):
            if i % 2:
                # track the vars used
                self.params.append(tsplit[i])
                # vars match any string
                # XXX vars are assumed to lack '/' - this is imperfect...
                rxs.append('([^/]*)')
            else:
                # quote special chars regexp interpretation
                rxs.append(re.escape(tsplit[i]))
        rxs.append('$')
        self._parser = re.compile(''.join(rxs))

    def __repr__(self):
        return '<URITemplate %r>' % self.template

    def run (self, **args):
        def repl(m):
            key = m.group(1)
            return args[key]
        
        uri = self.VARREF.sub(repl,self.template)

        # XXX for testing, compare this to args array
        if self.parse(uri) is None:
            print 're-parsing generated uri failed: %r, %r' % (uri, self.template)

        return uri


    def parse(self, uri):
        m = self._parser.match(uri)
        if m is None:
            return None
        return dict(zip(self.params, m.groups()))
    
if __name__ == '__main__':
    ut = URITemplate('xxx{key}yyy')
    print ut.run(key='ABC')
