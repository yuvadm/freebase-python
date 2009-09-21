try:
    from google.appengine.api import urlfetch
    from cookie_handlers import CookiefulUrlfetch
except:
    pass

try:
    import httplib2
    from cookie_handlers import CookiefulHttp
except:
    pass

try:
    import urllib2
    import socket
except:
    pass

import logging
import re

class Urllib2Client(object):
    def __init__(self, cookiejar, rse):
        cookiespy = urllib2.HTTPCookieProcessor(cookiejar)
        self.opener = urllib2.build_opener(cookiespy)
        self._raise_service_error = rse
        self.log = logging.getLogger("freebase")

    def __call__(self, url, method, body, headers):
        req = urllib2.Request(url, body, headers)

        try:
            resp = self.opener.open(req)

        except socket.error, e:
            self.log.error('SOCKET FAILURE: %s', e.fp.read())
            raise MetawebError, 'failed contacting %s: %s' % (url, str(e))

        except urllib2.HTTPError, e:
            self.log.error('HTTP ERROR: %s', e)
            self._raise_service_error(url, e.code, e.info().type, e.fp.read())

        for header in resp.info().headers:
            self.log.debug('HTTP HEADER %s', header)
            name, value = re.split("[:\n\r]", header, 1)
            if name.lower() == 'x-metaweb-tid':
                self.tid = value.strip()

        return (resp, resp.read())

class Httplib2Client(object):
    def __init__(self, cookiejar, rse):
        self.cookiejar = cookiejar
        self._raise_service_error = rse
        self.httpclient = CookiefulHttp(cookiejar=self.cookiejar)

    def __call__(self, url, method, body, headers):
        try:
            resp, content = self.httpclient.request(url, method=method,
                                                    body=body, headers=headers)
            if (resp.status != 200):
                self._raise_service_error(url, resp.status, resp['content-type'], content)

        except socket.error, e:
            self.log.error('SOCKET FAILURE: %s', e.fp.read())
            raise MetawebError, 'failed contacting %s: %s' % (url, str(e))

        except httplib2.HttpLib2ErrorWithResponse, e:
            self._raise_service_error(url, resp.status, resp['content-type'], content)
        except httplib2.HttpLib2Error, e:
            raise MetawebError(u'HTTP error: %s' % (e,))

        #tid = resp.get('x-metaweb-tid', None)

        return (resp, content)


class UrlfetchClient(object):
    def __init__(self, cookiejar, rse):
        self.cookiejar = cookiejar
        self._raise_service_error = rse
        self.httpclient = CookiefulUrlfetch(cookiejar=self.cookiejar)

    def __call__(self, url, method, body, headers):
        resp = self.httpclient.request(url, payload=body, method=method, headers=headers)

        if resp.status_code != 200:
            self._raise_service_error(url, resp.status_code, resp.headers['content-type'], resp.body)

        return (resp, resp.content)

