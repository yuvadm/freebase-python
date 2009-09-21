# ==================================================================
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
# ====================================================================

"""
declarations for external metaweb api.

    
    from metaweb.api import HTTPMetawebSession
    
    mss = HTTPMetawebSession('sandbox-freebase.com')
    print mss.mqlread([dict(name=None, type='/type/type')])
"""



__all__ = ['MetawebError', 'MetawebSession', 'HTTPMetawebSession', 'attrdict']
__version__ = '1.0.2'

import os, sys, re
import cookielib

SEPARATORS = (",", ":")

# json libraries rundown
# jsonlib2 is the fastest, but it's written in C, thus not as
# accessible. json is included in python2.6. simplejson
# is the same as json.

try:
    import jsonlib2 as json
except ImportError:
    try:
        import json
    except ImportError:
        try:
            import simplejson as json
        except ImportError:
            try:
                # appengine provides simplejson at django.utils.simplejson
                from django.utils import simplejson as json
            except ImportError:
                raise Exception("unable to import neither json, simplejson, jsonlib2, or django.utils.simplejson")

try:
    from urllib import quote as urlquote
except ImportError:
    from urlib_stub import quote as urlquote
import pprint
import socket
import logging

LITERAL_TYPE_IDS = set([
  "/type/int",
  "/type/float",
  "/type/boolean",
  "/type/rawstring",
  "/type/uri",
  "/type/text",
  "/type/datetime",
  "/type/bytestring",
  "/type/id",
  "/type/key",
  "/type/value",
  "/type/enumeration"
])


class Delayed(object):
    """
    Wrapper for callables in log statements. Avoids actually making
    the call until the result is turned into a string.
    
    A few examples:
    
    json.dumps is never called because the logger never
    tries to format the result
    >>> logging.debug(Delayed(json.dumps, q))
    
    This time json.dumps() is actually called:
    >>> logging.warn(Delayed(json.dumps, q))
    
    """
    def __init__(self, f, *args, **kwds):
        self.f = f
        self.args = args
        self.kwds = kwds
    
    def __str__(self):
        return str(self.f(*self.args, **self.kwds))

def logformat(result):
    """
    Format the dict/list as a json object
    """
    rstr = json.dumps(result, indent=2)
    if rstr[0] == '{':
        rstr = rstr[1:-2]
    return rstr

from httpclients import Httplib2Client, Urllib2Client, UrlfetchClient

# Check for urlfetch first so that urlfetch is used when running the appengine SDK
try:
    import google.appengine.api.urlfetch
    from cookie_handlers import CookiefulUrlfetch
    http_client = UrlfetchClient
except ImportError:
    try:
        import httplib2
        from cookie_handlers import CookiefulHttp
        http_client = Httplib2Client
    except ImportError:
        import urllib2
        httplib2 = None
        CookiefulHttp = None
        http_client = Urllib2Client

def urlencode_weak(s):
    return urlquote(s, safe=',/:$')


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
        # adds the *args and **kwargs to self (which is a dict)
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
    
    This is more of an interface than a class
    """
    
    # interface definition here...


# from httplib2
NORMALIZE_SPACE = re.compile(r'(?:\r\n)?[ \t]+')
def _normalize_headers(headers):
    return dict([ (key.lower(), NORMALIZE_SPACE.sub(value, ' ').strip())  for (key, value) in headers.iteritems()])

class HTTPMetawebSession(MetawebSession):
    """
    a MetawebSession is a request/response queue.
    
    this version uses the HTTP api, and is synchronous.
    """
    # share cookies across sessions, so that different sessions can
    #  see each other's writes immediately.
    _default_cookiejar = cookielib.CookieJar()
    
    def __init__(self, service_url, username=None, password=None, prev_session=None, cookiejar=None, cookiefile=None, application_name=None):
        """
        create a new MetawebSession for interacting with the Metaweb.
        
        a new session will inherit state from prev_session if present,
        """
        super(HTTPMetawebSession, self).__init__()
        
        self.log = logging.getLogger("freebase")
        self.application_name = application_name
        
        assert not service_url.endswith('/')
        if not '/' in service_url:  # plain host:port
            service_url = 'http://' + service_url
        
        self.service_url = service_url
        
        self.username = username
        self.password = password
        
        self.tid = None
        
        if prev_session:
            self.service_url = prev.service_url
        
        if cookiefile is not None:
            cookiejar = self.open_cookie_file(cookiefile)
        
        if cookiejar is not None:
            self.cookiejar = cookiejar
        elif prev_session:
            self.cookiejar = prev_session.cookiejar
        else:
            self.cookiejar = self._default_cookiejar
        
        self._http_request = http_client(self.cookiejar, self._raise_service_error)

    
    def open_cookie_file(self, cookiefile=None):
        if cookiefile is None or cookiefile == '':
            if os.environ.has_key('HOME'):
                cookiefile = os.path.join(os.environ['HOME'], '.pyfreebase/cookiejar')

            else:
                raise MetawebError("no cookiefile specified and no $HOME/.pyfreebase directory" % cookiefile)
        
        cookiejar = cookielib.LWPCookieJar(cookiefile)
        if os.path.exists(cookiefile):
            cookiejar.load(ignore_discard=True)
        
        return cookiejar

    
    def _httpreq(self, service_path, method='GET', body=None, form=None,
                 headers=None):
        """
        make an http request to the service.
        
        form arguments are encoded in the url, even for POST, if a non-form
        content-type is given for the body.
        
        returns a pair (resp, body)
        
        resp is the response object and may be different depending
        on whether urllib2 or httplib2 is in use?
        """
        
        if method == 'GET':
            assert body is None
        if method != "GET" and method != "POST":
            assert 0, 'unknown method %s' % method
        
        url = self.service_url + service_path
        
        if headers is None:
            headers = {}
        else:
            headers = _normalize_headers(headers)
        
        # this is a lousy way to parse Content-Type, where is the library?
        ct = headers.get('content-type', None)
        if ct is not None:
            ct = ct.split(';')[0]
        
        if body is not None:
            # if body is provided, content-type had better be too
            assert ct is not None
        
        if form is not None:
            qstr = '&'.join(['%s=%s' % (urlencode_weak(unicode(k).encode('utf-8')),
                                        urlencode_weak(unicode(v).encode('utf-8')))
                             for k,v in form.items()])
            if method == 'POST':
                # put the args on the url if we're putting something else
                # in the body.  this is used to add args to raw uploads.
                if body is not None:
                    url += '?' + qstr
                else:
                    if ct is None:
                        ct = 'application/x-www-form-urlencoded'
                        headers['content-type'] = ct + '; charset=utf-8'
                    
                    if ct == 'multipart/form-encoded':
                        # TODO handle this case
                        raise NotImplementedError
                    elif ct == 'application/x-www-form-urlencoded':
                        body = qstr
            else:
                # for all methods other than POST, use the url
                url += '?' + qstr

        
        # assure the service that this isn't a CSRF form submission
        headers['x-metaweb-request'] = 'Python'
        
        if 'user-agent' not in headers:
            user_agent = ["python", "freebase.api-%s" % __version__]
            if self.application_name:
                user_agent.append(self.application_name)
            headers['user-agent'] = ' '.join(user_agent)
        
        ####### DEBUG MESSAGE - should check log level before generating
        loglevel = self.log.getEffectiveLevel()
        if loglevel <= 20: # logging.INFO = 20
            if form is None:
                formstr = ''
            else:
                formstr = '\nFORM:\n  ' + '\n  '.join(['%s=%s' % (k,v)
                                              for k,v in form.items()])
            if headers is None:
                headerstr = ''
            else:
                headerstr = '\nHEADERS:\n  ' + '\n  '.join([('%s: %s' % (k,v))
                                                  for k,v in headers.items()])
            self.log.info('%s %s%s%s', method, url, formstr, headerstr)
        
        # just in case you decide to make SUPER ridiculous GET queries:
        if len(url) > 1000 and method == "GET":
            method = "POST"
            url, body = url.split("?", 1) 
            ct = 'application/x-www-form-urlencoded'
            headers['content-type'] = ct + '; charset=utf-8'
           
        return self._http_request(url, method, body, headers)
    
    def _raise_service_error(self, url, status, ctype, body):
        
        is_jsbody = (ctype.endswith('javascript')
                     or ctype.endswith('json'))
        if str(status) == '400' and is_jsbody:
            r = self._loadjson(body)
            msg = r.messages[0]
            raise MetawebError(u'%s %s %r' % (msg.get('code',''), msg.message, msg.info))
        
        raise MetawebError, 'request failed: %s: %s\n%s' % (url, status, body)
    
    def _httpreq_json(self, *args, **kws):
        resp, body = self._httpreq(*args, **kws)
        return self._loadjson(body)
    
    def _loadjson(self, json_input):
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
        
        if json_input == '':
            self.log.error('the empty string is not valid json')
            raise MetawebError('the empty string is not valid json')
        
        try:
            r = json.loads(json_input)
        except ValueError, e:
            self.log.error('error parsing json string %r' % json_input)
            raise MetawebError, 'error parsing JSON string: %s' % e
        
        return struct2attrdict(r)
    
    def _check_mqlerror(self, r):
        if r.code != '/api/status/ok':
            for msg in r.messages:
                self.log.error('mql error: %s %s %r' % (msg.code, msg.message, msg.get('query', None)))
            raise MetawebError, 'query failed: %s\n%s\n%s' % (r.messages[0].code, r.messages[0].message, json.dumps(r.messages[0].get('query', None), indent=2))
    
    def _mqlresult(self, r):
        self._check_mqlerror(r)
        
        self.log.info('result: %s', Delayed(logformat, r))
        
        return r.result


    
    def login(self, username=None, password=None, rememberme=False):
        """sign in to the service. For a more complete description,
        see http://www.freebase.com/view/en/api_account_login"""
        
        service = '/api/account/login'
        
        username = username or self.username
        password = password or self.password
        
        assert username is not None
        assert password is not None
        
        self.log.debug('LOGIN USERNAME: %s', username)

        rememberme = rememberme and "true" or "false"
        form_params = {"username": username,
                       "password": password }
        if rememberme:
            form_params["rememberme"] = "true"
        r = self._httpreq_json(service, 'POST',
                               form=form_params)
        
        if r.code != '/api/status/ok':
            raise MetawebError(u'%s %r' % (r.get('code',''), r.messages))
        
        self.log.debug('LOGIN RESP: %r', r)
        self.log.debug('LOGIN COOKIES: %s', self.cookiejar)
    
    def logout(self):
        """logout of the service. For a more complete description,
        see http://www.freebase.com/view/en/api_account_logout"""
        
        service = '/api/account/logout'
        
        self.log.debug("LOGOUT")
        
        r = self._httpreq_json(service, 'GET')
        
        if r.code != '/api/status/ok':
            raise MetawebError(u'%s %r' % (r.get('code',''), r.messages)) #this should never happen
    
    def user_info(self, mql_output=None):
        """ get user_info. For a more complete description,
        see http://www.freebase.com/view/guid/9202a8c04000641f800000000c36a842"""
        
        service = "/api/service/user_info"
        
        qstr = json.dumps(mql_output, separators=SEPARATORS)
        
        r = self._httpreq_json(service, 'POST', form=dict(mql_output=qstr))
        return r
    
    def loggedin(self):
        """check to see whether a user is logged in or not. For a
        more complete description, see http://www.freebase.com/view/en/api_account_loggedin"""
        
        service = "/api/account/loggedin"
        try:
            r = self._httpreq_json(service, 'GET')
            if r.code == "/api/status/ok":
                return True
        
        except MetawebError, me:
            return False

    def create_private_domain(self, domain_key, display_name):
        """ create a private domain. For a more complete description,
        see http://www.freebase.com/edit/topic/en/api_service_create_private_domain"""
        
        service = "/api/service/create_private_domain"
        
        form = dict(domain_key=domain_key, display_name=display_name)
        
        r = self._httpreq_json(service, 'POST', form=form)
        return r
    
    
    def delete_private_domain(self, domain_key):
        """ create a private domain. For a more complete description,
        see http://www.freebase.com/edit/topic/en/api_service_delete_private_domain"""
        
        service = "/api/service/delete_private_domain"
        
        form = dict(domain_key=domain_key)
        
        return self._httpreq_json(service, 'POST', form=form)
    
    def mqlreaditer(self, sq, asof=None):
        """read a structure query."""
        
        cursor = True
        service = '/api/service/mqlread'
        
        if isinstance(sq, (tuple, list)):
            if len(sq) > 1:
                raise MetawebError("You cannot ask mqlreaditer a query in the form: [{}, {}, ...], just [{}] or {}")
            sq = sq[0]
        
        while 1:
            subq = dict(query=[sq], cursor=cursor, escape=False)
            if asof:
                subq['as_of_time'] = asof
            
            qstr = json.dumps(subq, separators=SEPARATORS)
                        
            r = self._httpreq_json(service, 'POST', form=dict(query=qstr))
            
            for item in self._mqlresult(r):
                yield item
            
            if r['cursor']:
                cursor = r['cursor']
                self.log.info('CONTINUING with %s', cursor)
            else:
                return
    
    def mqlread(self, sq, asof=None):
        """read a structure query. For a more complete description,
        see http://www.freebase.com/view/en/api_service_mqlread"""
        subq = dict(query=sq, escape=False)
        if asof:
            subq['as_of_time'] = asof
        
        if isinstance(sq, list):
            subq['cursor'] = True
        
        service = '/api/service/mqlread'
        
        self.log.info('%s: %s',
                      service,
                      Delayed(logformat, sq))
        
        qstr = json.dumps(subq, separators=SEPARATORS)
        r = self._httpreq_json(service, 'POST', form=dict(query=qstr))
        
        return self._mqlresult(r)
    
    def mqlreadmulti(self, queries, asof=None):
        """read a structure query"""
        keys = [('q%d' % i) for i,v in enumerate(queries)];
        envelope = {}
        for i,sq in enumerate(queries):
            subq = dict(query=sq, escape=False)
            if asof:
                subq['as_of_time'] = asof
            
            # XXX put this back once mqlreadmulti is working in general
            #if isinstance(sq, list):
            #    subq['cursor'] = True
            envelope[keys[i]] = subq
        
        service = '/api/service/mqlread'
        
        self.log.info('%s: %s',
                      service,
                      Delayed(logformat, envelope))
        
        qstr = json.dumps(envelope, separators=SEPARATORS)
        rs = self._httpreq_json(service, 'POST', form=dict(queries=qstr))
        
        self.log.info('%s result: %s',
                      service,
                      Delayed(json.dumps, rs, indent=2))
        
        return [self._mqlresult(rs[key]) for key in keys]
    
    def trans(self, guid):
        """translate blob from id. Identical to `raw`. For more
        information, see http://www.freebase.com/view/en/api_trans_raw"""
        return self.raw(guid)
    
    def raw(self, id):
        """translate blob from id. For a more complete description,
        see http://www.freebase.com/view/en/api_trans_raw"""
        url = '/api/trans/raw' + urlquote(id)
        
        self.log.info(url)
        
        resp, body = self._httpreq(url)
        
        self.log.info('raw is %d bytes' % len(body))
        
        return body
    
    def blurb(self, id, break_paragraphs=False, maxlength=200):
        """translate only the text in blob from id. For a more
        complete description, see http://www.freebase.com/view/en/api_trans_blurb"""
        url = '/api/trans/blurb' + urlquote(id)
        
        self.log.info(url)
        
        resp, body = self._httpreq(url, form=dict(break_paragraphs=break_paragraphs, maxlength=maxlength))
        
        self.log.info('blurb is %d bytes' % len(body))
        
        return body
    
    def unsafe(self, id):
        """ unsafe raw... not really documented, but identical to raw,
        except it will be exactly what you uploaded. """
        url = '/api/trans/unsafe' + urlquote(id)
        
        self.log.info(url)
        
        resp, body = self._httpreq(url, headers={'x-metaweb-request' : 'Python'})
        
        self.log.info('unsafe is %d bytes' % len(body))
        
        return body
    
    def image_thumb(self, id, maxwidth=None, maxheight=None, mode="fit", onfail=None):
        """ given the id of an image, this will return a URL of a thumbnail of the image.
        The full details of how the image is cropped and finessed is detailed at
        http://www.freebase.com/view/en/api_trans_image_thumb """
        
        service = "/api/trans/image_thumb"
        assert mode in ["fit", "fill", "fillcrop", "fillcropmid"]
        
        form = dict(mode=mode)
        if maxwidth is not None:
            form["maxwidth"] = maxwidth
        if maxheight is not None:
            form["maxheight"] = maxheight
        if onfail is not None:
            form["onfail"] = onfail
        
        resp, body = self._httpreq(service + urlquote(id), form=form)
        self.log.info('image is %d bytes' % len(body))
        
        return body
    
    def mqlwrite(self, sq, use_permission_of=None, attribution_id=None):
        """do a mql write. For a more complete description,
        see http://www.freebase.com/view/en/api_service_mqlwrite"""
        query = dict(query=sq, escape=False)
        if use_permission_of:
            query['use_permission_of'] = use_permission_of
        if attribution_id:
            query['attribution'] = attribution_id

        qstr = json.dumps(query, separators=SEPARATORS)
        
        self.log.debug('MQLWRITE: %s', qstr)
        
        service = '/api/service/mqlwrite'
        
        self.log.info('%s: %s',
                      service,
                      Delayed(logformat,sq))
        
        r = self._httpreq_json(service, 'POST',
                               form=dict(query=qstr))
        
        self.log.debug('MQLWRITE RESP: %r', r)
        return self._mqlresult(r)
    
    def mqlcheck(self, sq):
        """ See if a write is valid, and see what would happen, but do not
        actually do the write """
        
        query = dict(query=sq, escape=False)
        qstr = json.dumps(query, separators=SEPARATORS)
        
        self.log.debug('MQLCHECK: %s', qstr)
        
        service = '/api/service/mqlcheck'
        
        self.log.info('%s: %s',
                      service,
                      Delayed(logformat, sq))
        
        r = self._httpreq_json(service, 'POST',
                               form=dict(query=qstr))

        
        self.log.debug('MQLCHECK RESP: %r', r)
        
        return self._mqlresult(r)
    
    def mqlflush(self):
        """ask the service not to hand us old data"""
        self.log.debug('MQLFLUSH')
        
        service = '/api/service/touch'
        r = self._httpreq_json(service)
        
        self._check_mqlerror(r)
        return True
    
    def touch(self):
        """ make sure you are accessing the most recent data. For a more
        complete description, see http://www.freebase.com/view/en/api_service_touch"""
        return self.mqlflush()

    
    def upload(self, body, content_type, document_id=False, permission_of=False):
        """upload to the metaweb. For a more complete description,
        see http://www.freebase.com/view/en/api_service_upload"""
        
        service = '/api/service/upload'
        
        self.log.info('POST %s: %s (%d bytes)',
                      service, content_type, len(body))

        
        headers = {}
        if content_type is not None:
            headers['content-type'] = content_type
        
        form = None
        if document_id is not False:
            if document_id is None:
                form = { 'document': '' }
            else:
                form = { 'document': document_id }
        if permission_of is not False:
            if form:
                form['permission_of'] = permission_of
            else:
                form = { 'permission_of' : permission_of }
        
        # note the use of both body and form.
        #  form parameters get encoded into the URL in this case
        r = self._httpreq_json(service, 'POST',
                               headers=headers, body=body, form=form)
        return self._mqlresult(r)
    
    
    def uri_submit(self, URI, document=None, content_type=None):
        """ submit a URI to freebase. For a more complete description,
        see http://www.freebase.com/edit/topic/en/api_service_uri_submit """
        
        service = "/api/service/uri_submit"
        
        form = dict(uri=URI)
        if document is not None:
            form["document"] = document
        if content_type is not None:
            form["content_type"] = content_type
        
        r = self._httpreq_json(service, 'POST', form=form)
        return self._mqlresult(r)
        
    
    def search(self, query, format=None, prefixed=None, limit=20, start=0,
                type=None, type_strict="any", domain=None, domain_strict=None,
                escape="html", timeout=None, mql_filter=None, mql_output=None):
        """ search freebase.com. For a more complete description,
        see http://www.freebase.com/view/en/api_service_search"""
        
        service = "/api/service/search"
        
        form = dict(query=query)
        
        if format:
            form["format"] = format
        if prefixed:
            form["prefixed"] = prefixed
        if limit:
            form["limit"] = limit
        if start:
            form["start"] = start
        if type:
            form["type"] = type
        if type_strict:
            form["type_strict"] = type_strict
        if domain:
            form["domain"] = domain
        if domain_strict:
            form["domain_strict"] = domain_strict
        if escape:
            form["escape"] = escape
        if timeout:
            form["timeout"] = timeout
        if mql_filter:
            form["mql_filter"] = mql_filter
        if mql_output:
            form["mql_output"] = mql_output
            
        
        r = self._httpreq_json(service, 'POST', form=form)
        
        return self._mqlresult(r)
        
    
    def geosearch(self, location=None, location_type=None, mql_input=None, limit=20,
                start=0, type=None, geometry_type=None, intersect=None, mql_filter=None,
                within=None, inside=None, order_by=None, count=None, format="json", mql_output=None):
        """ perform a geosearch. For a more complete description,
        see http://www.freebase.com/api/service/geosearch?help """
        
        service = "/api/service/geosearch"
        
        if location is None and location_type is None and mql_input is None:
            raise Exception("You have to give it something to work with")
        
        form = dict()
        
        if location:
        	form["location"] = location
        if location_type:
        	form["location_type"] = location_type
        if mql_input:
        	form["mql_input"] = mql_input
        if limit:
        	form["limit"] = limit
        if start:
        	form["start"] = start
        if type:
        	form["type"] = type
        if geometry_type:
        	form["geometry_type"] = geometry_type
        if intersect:
        	form["intersect"] = intersect
        if mql_filter:
        	form["mql_filter"] = mql_filter
        if within:
        	form["within"] = within
        if inside:
        	form["inside"] = inside
        if order_by:
        	form["order_by"] = order_by
        if count:
        	form["count"] = count
        if format:
        	form["format"] = format
        if mql_output:
        	form["mql_output"] = mql_output
        
        if format == "json":
            r = self._httpreq_json(service, 'POST', form=form)
        else:
            r = self._httpreq(service, 'POST', form=form)
            
        return r
    
    def version(self):
        """ get versions for various parts of freebase. For a more
        complete description, see http://www.freebase.com/view/en/api_version"""
        
        service = "/api/version"
        r = self._httpreq_json(service)
        
        return r
    
    def status(self):
       """ get the status for various parts of freebase. For a more
       complete description, see http://www.freebase.com/view/en/api_status """
       
       service = "/api/status"
       r = self._httpreq_json(service)
       
       return r

    ### DEPRECATED IN API
    def reconcile(self, name, etype=['/common/topic']):
        """DEPRECATED: reconcile name to guid. For a more complete description,
        see http://www.freebase.com/view/en/dataserver_reconciliation
        
        If interested in a non-deprecated version,
        check out http://data.labs.freebase.com/recon/"""
        
        service = '/dataserver/reconciliation'
        r = self._httpreq_json(service, 'GET', form={'name':name, 'types':','.join(etype)})
        
        
        # TODO non-conforming service, fix later
        #self._mqlresult(r)
        return r


if __name__ == '__main__':
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    
    mss = HTTPMetawebSession('sandbox-freebase.com')
    
    mss.log.setLevel(logging.DEBUG)
    mss.log.addHandler(console)

    
    print mss.mqlread([dict(name=None, type='/type/type')])
