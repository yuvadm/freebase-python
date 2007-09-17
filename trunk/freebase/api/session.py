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
#  declarations for external metaweb api.
#
#
#    from metaweb.api import HTTPMetawebSession
#
#    mss = HTTPMetawebSession('sandbox.freebase.com')
#    print mss.mqlread([dict(name=None, type='/type/type')])
#
#
#

import os, sys, re
import urllib2
import cookielib
import simplejson
from urllib import quote as urlquote
import pprint
import socket

import logging
log = logging.getLogger()
log.setLevel(logging.DEBUG)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
# add the handler to the root logger
log.addHandler(console)


__all__ = ['MetawebError', 'MetawebSession', 'HTTPMetawebSession']

__version__ = '0.1'

import simplejson.encoder
simplejson.JSONEncoder.item_separator = ','
simplejson.JSONEncoder.key_separator = ':'
#delattr(simplejson.encoder.ESCAPE_DCT, '/')

def urlencode_weak(s):
    return urlquote(s, safe='{}[],"/:$')


# from http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/361668
class attrdict(dict):
    """A dict whose items can also be accessed as member variables.

    >>> d = attrdict(a=1, b=2)
    >>> d['c'] = 3
    >>> print d.a, d.b, d.c
    1 2 3
    >>> d.b = 10
    >>> print d['b']
    10

    # but be careful, it's easy to hide methods
    >>> print d.get('c')
    3
    >>> d['get'] = 4
    >>> print d.get('a')
    Traceback (most recent call last):
    TypeError: 'int' object is not callable
    """
    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        self.__dict__ = self



# TODO expose the common parts of the result envelope
class MetawebError(Exception):
    """
    an error report from the metaweb service.
    """
    pass



# TODO right now this is a completely unnecessary superclass.
#  is there enough common behavior between session types
#  to justify it?
class MetawebSession(object):
    """
    MetawebSession is the base class for MetawebSession, subclassed for
    different connection types.  Only http is available externally.

    This is more of an interface than 
    """

    # interface definition here...
    

class HTTPMetawebSession(MetawebSession):
    """
    a MetawebSession is a request/response queue.

    this version uses the HTTP api, and is synchronous.
    """
    # share cookies across sessions, so that different sessions can
    #  see each other's writes immediately.
    _cookies = cookielib.CookieJar()
    _cookiespy = urllib2.HTTPCookieProcessor(_cookies)

    def __init__(self, service_url, username=None, password=None, prev_session=None):
        """
        create a new MetawebSession for interacting with the Metaweb.

        a new session will inherit state from prev_session if present, 
        """
        super(HTTPMetawebSession, self).__init__()

        assert not service_url.endswith('/')
        if not '/' in service_url:  # plain host:port
            service_url = 'http://' + service_url

        self.service_url = service_url

        self.username = username
        self.password = password

        self.tid = None

        if prev_session:
            self.service_url = prev.service_url

    def _httpreq(self, service_path, method='GET', body=None, form=None,
                 headers=None, **kws):
        """
        make an http request to the service.

        form arguments are encoded in the url, even for POST, if a non-form
        content-type is given for the body.
        """

        if method == 'POST':
            assert body is not None or form is not None
        elif method == 'GET':
            assert body is None
        else:
            assert 0, 'unknown method %s' % method

        log.debug('HTTPREQ: %s %s %s %s', service_path, method, kws, self._cookies)

        url = self.service_url + service_path

        if headers is None:
            headers = []

        # XXX This is a lousy way to parse Content-Type, where is
        #  the library?
        ct = None
        for k,v in headers:
            if k.lower() == 'content-type':
                ct = v.split(';')[0]
                break

        if body is not None:
            # if body is provided, content-type had better be too
            assert ct is not None

        if form is not None:
            qstr = '&'.join(['%s=%s' % (urlencode_weak(k), urlencode_weak(v))
                             for k,v in form.items()])
            if method == 'POST':
                # put the args on the url if we're putting something else
                # in the body.  this is used to add args to raw uploads.
                if body is not None:
                    url += '?' + qstr
                else:
                    if ct is None:
                        # XXX encoding and stuff
                        ct = 'application/x-www-form-urlencoded'
                        headers.append(('content-type', ct))

                    if ct == 'multipart/form-encoded':
                        # XXX fixme
                        raise NotImplementedError
                    elif ct == 'application/x-www-form-urlencoded':
                        body = qstr
            else:
                # for all methods other than POST, use the url
                url += '?' + qstr

        req = urllib2.Request(url, body, dict(headers), **kws)

        self.opener = urllib2.build_opener(self._cookiespy)

        # assure the service that this isn't a CSRF form submission
        self.opener.addheaders = [('User-agent',
                                   'python freebase.api-%s' % __version__),
                                  ('X-Metaweb-Request', 'Python')]

        if self.tid is not None:
            self.opener.addheaders.append(('X-Metaweb-TID', self.tid))

        try:
            if headers:
                self.opener.addheaders += headers
            resp = self.opener.open(req)

        except socket.error, e:
            log.error('SOCKET FAILURE: %s', e.fp.read())
            raise MetawebError, 'failed contacting %s: %s' % (url, str(e))

        except urllib2.HTTPError, e:
            if e.code == 400 and e.info().type == 'application/json':
                r = self._readjson(e.fp)
                for msg in r.messages:
                    if msg.get('level', 'error') == 'error':
                        raise MetawebError(u'%s %s %r' % (msg.get('code',''), msg.message, msg.info))

                # some 400 we don't recognize.  hmm.
                raise MetawebError(u'%r' %  r)
            raise MetawebError, 'request failed: %s: %r %r' % (url, str(e), e.fp.read())

        for header in resp.info().headers:
            log.debug('HTTP HEADER %s', header)
            name, value = re.split("[:\n\r]", header, 1)
            if name.lower() == 'x-metaweb-tid':
                self.tid = value.strip()
            #if name.lower().startswith('set-cookie'):
            #  if value.startswith(' metaweb-user'):
            #    pass
            #  else:
            #    self.saved_headers[name] = value.strip()
            #  log.debug('HTTP VALUE %s', value)              

        return resp

    def _readjson(self, fp):
        # TODO really this should be accomplished by hooking
        # simplejson to create attrdicts instead of dicts.
        def struct2attrdict(st):
            """
            copy a json structure, turning all dicts into attrdicts.
            
            copying descends instances of dict and list, including subclasses.
            """
            if isinstance(st, dict):
                return attrdict([(k,struct2attrdict(v)) for k,v in st.items()])
            if isinstance(st, list):
                return [struct2attrdict(li) for li in st]
            return st

        json = fp.read()
        if json == '':
            log.error('the empty string is not valid json')
            raise MetawebError('the empty string is not valid json')

        try:
            r = simplejson.loads(json)
        except ValueError, e:
            log.error('error parsing json string %r' % json)
            raise MetawebError, 'error parsing JSON string: %s' % e

        return struct2attrdict(r)

    def _mqlresult(self, r):
        if r.code != '/api/status/ok':
            for msg in r.messages:
                log.error('mqlread failed: %s %s' % (msg.code, msg.message))
            raise MetawebError, 'query failed: %s' % r.messages[0].code

        return r.result

    def login(self):
        """sign in to the service"""

        assert self.username is not None
        assert self.password is not None
        
        log.debug('LOGIN USERNAME: %s', self.username)
        
        try:
            resp = self._httpreq('/api/account/login', 'POST',
                                 form=dict(username=self.username,
                                           password=self.password))
        except urllib2.HTTPError, e:
            raise MetawebError("login error: %s", e)

        r = self._readjson(resp)

        if r.code != '/api/status/ok':
            raise MetawebError(u'%s %r' % (r.get('code',''), r.messages))

        log.debug('LOGIN RESP: %r', r)
        log.debug('LOGIN INFO: %s', resp.info())
        log.debug('LOGIN COOKIES: %s', self._cookies)


    def mqlreaditer(self, sq):
        """read a structure query"""

        cursor = True

        while 1:
            subq = dict(query=[sq], cursor=cursor, escape=False)
            qstr = simplejson.dumps(dict(c0=subq))

            service = '/api/service/mqlread'
            
            resp = self._httpreq(service, form=dict(queries=qstr))
            r = self._readjson(resp)
            r = r['c0']

            for item in self._mqlresult(r):
                yield item

            if r['cursor']:
                cursor = r['cursor']
            else:
                break

    def mqlread(self, sq):
        """read a structure query"""
        subq = dict(query=sq, cursor=True, escape=False)
        qstr = simplejson.dumps(dict(c0=subq))

        log.debug('MQLREAD: %s', qstr)

        service = '/api/service/mqlread'

        resp = self._httpreq(service, form=dict(queries=qstr))
        r = self._readjson(resp)
        r = r['c0']
        return self._mqlresult(r)

    def trans(self, guid):
        """translate blob from guid """
        url = '/api/trans/raw/' + urlquote(guid)
        resp = self._httpreq(url)
        content = resp.read()
        return content

    def mqlwrite(self, sq):
        """do a mql write"""
        query = dict(query=sq, escape=False)
        qstr = simplejson.dumps(query)

        log.debug('MQLWRITE: %s', qstr)

        service = '/api/service/mqlwrite'
        resp = self._httpreq(service, 'POST',
                             form=dict(query=qstr))
        r = self._readjson(resp)
        return self._mqlresult(r)

    def upload(self, body, content_type):
        """upload to the metaweb"""

        log.debug('UPLOAD %s', content)

        service = '/api/service/upload'
        resp = self._httpreq(service, 'POST',
                             headers={'content-type': content_type},
                             body=qstr)
        r = self._readjson(resp)
        return self._mqlresult(r)


if __name__ == '__main__':
    mss = HTTPMetawebSession('sandbox.freebase.com')

    print mss.mqlread([dict(name=None, type='/type/type')])
