#========================================================================
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
# THIS SOFTWARE IS PROVIDED BY METAWEB TECHNOLOGIES ``AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL METAWEB TECHNOLOGIES BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN
# IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# ========================================================================
#
# This is the full "metaweb.py" module from the Metaweb API documentation
#
# In the documentation, each function is presented as a separate
# example.  This is the whole file.
#
# If you find any errors or have suggestions for improving this module,
# send them to the Freebase developers mailing list: developers@freebase.com
# You can subscribe to the mailing list at http://lists.freebase.com/
#

import urllib        # URL encoding
import urllib2       # Higher-level URL content fetching
import simplejson    # JSON serialization and parsing

#
# When experimenting, use the sandbox.freebase.com service.
# Every Monday, sandbox.freebase.com is erased and it is updated
# with a fresh copy of data from www.freebase.com.  This makes
# it an ideal place to experiment.
#
host = 'sandbox.freebase.com'              # The Metaweb host
readservice = '/api/service/mqlread'   # Path to mqlread service
loginservice = '/api/account/login'     # Path to login service
writeservice = '/api/service/mqlwrite'  # Path to mqlwrite service
uploadservice = '/api/service/upload'   # Path to upload service
                 
# If anything goes wrong when talking to a Metaweb service, we raise MQLError.
class MQLError(Exception):
    def __init__(self, value):     # This is the exception constructor method
        self.value = value
    def __str__(self):             # Convert error object to a string
        return repr(self.value)

# Submit the MQL query q and return the result as a Python object.
# If authentication credentials are supplied, use them in a cookie.
# Raises MQLError if the query was invalid. Raises urllib2.HTTPError if
# mqlread returns an HTTP status code other than 200 (which should not happen).
def read(q, credentials=None):
    # Put the query in an envelope
    env = {'qname':{'query':q}}
    # JSON serialize and URL encode the envelope and the query parameter
    args = urllib.urlencode({'queries':simplejson.dumps(env)})
    # Build the URL and create a Request object for it
    url = 'http://%s%s?%s' % (host, readservice, args)
    req = urllib2.Request(url)

    # Send our authentication credentials, if any, as a cookie.
    # The need for mqlread authentication is a temporary restriction.
    if credentials: 
        req.add_header('Cookie', credentials)

    # Now upen the URL and and parse its JSON content
    f = urllib2.urlopen(req)        # Open the URL
    response = simplejson.load(f)   # Parse JSON response to an object
    inner = response['qname']       # Open outer envelope; get inner envelope

    # If anything was wrong with the invocation, mqlread will return an HTTP
    # error, and the code above with raise urllib2.HTTPError.
    # If anything was wrong with the query, we won't get an HTTP error, but
    # will get an error status code in the response envelope.  In this case
    # we raise our own MQLError exception.
    if not inner['code'].startswith('/api/status/ok'):
        error = inner['messages'][0]
        raise MQLError('%s: %s' % (error['code'], error['message']))

    # If there was no error, then just return the result from the envelope
    return inner['result'];

# Submit the MQL query q and return the result as a Python object
# This function behaves like read() above, but uses cursors so that
# it works even for very large result sets
def readall(q, credentials=None):
    # This is the start of the mqlread URL.
    # We just need to append the envelope to it
    urlprefix = 'http://%s%s?queries=' % (host, readservice)

    # The query and most of the envelope are constant. We just need to append
    # the encoded cursor value and some closing braces to this prefix string
    jsonq = simplejson.dumps(q);
    envelopeprefix = urllib.quote_plus('{"q0":{"query":'+jsonq+',"cursor":')
    
    cursor = 'true'   # This is the initial value of the cursor
    results = []      # We accumulate results in this array

    # Loop until mqlread tells us there are no more results
    while cursor:
        # append the cursor and the closing braces to the envelope
        envelope = envelopeprefix + urllib.quote_plus(cursor + '}}')
        # append the envelope to the URL
        url = urlprefix + envelope

        # Begin an HTTP request for the URL
        req = urllib2.Request(url)

        # Send our authentication credentials, if any, as a cookie.
        # The need for mqlread authentication is a temporary restriction.
        if credentials: 
            req.add_header('Cookie', credentials)

        # Read and parse the URL contents
        f = urllib2.urlopen(req)          # Open URL
        response = simplejson.load(f)     # Parse JSON response
        inner = response['q0']            # Get inner envelope from outer

        # Raise a MQLError if there were errors
        if not inner['code'].startswith('/api/status/ok'):
            error = inner['messages'][0]
            raise MQLError('%s: %s' % (error['code'], error['message']))

        # Append this batch of results to the main array of results.
        results.extend(inner['result']);

        # Finally, get the new value of the cursor for the next iteration
        cursor = inner['cursor']
        if cursor:                        # If it is not false, put it
            cursor = '"' + cursor + '"'   #  in quotes as a JSON string

    # Now that we're done with the loop, return the results array
    return results

# Submit the specified username and password to the Metaweb login service.
# Return opaque authentication credentials on success. 
# Raise MQLError on failure.
def login(username, password):
    # Establish a connection to the server and make a request.
    # Note that we use the low-level httplib library instead of urllib2.
    # This allows us to manage cookies explicitly.
    conn = httplib.HTTPConnection(host)
    conn.request('POST',                   # POST the request
                 loginservice,             # The URL path /api/account/login
                 # The body of the request: encoded username/password
                 urllib.urlencode({'username':username, 'password':password}),
                 # This header specifies how the body of the post is encoded.
                 {'Content-type': 'application/x-www-form-urlencoded'})

    # Get the response from the server
    response = conn.getresponse()

    if response.status == 200:  # We get HTTP 200 OK even if login fails
        # Parse response body and raise a MQLError if login failed
        body = simplejson.loads(response.read())
        if not body['code'].startswith('/api/status/ok'):
            error = body['messages'][0]
            raise MQLError('%s: %s' % (error['code'], error['message']))

        # Otherwise return cookies to serve as authentication credentials.
        # The set-cookie header holds one or more cookie specifications,
        # separated by commas. Each specification is a name, an equal
        # sign, a value, and one or more trailing clauses that consist
        # of a semicolon and some metadata.  We don't care about the
        # metadata. We just want to return a comma-separated list of
        # name=value pairs.
        cookies = response.getheader('set-cookie').split(',')
        return ';'.join([c[0:c.index(';')] for c in cookies])
    else:                      # This should never happen
        raise MQLError('HTTP Error: %d %s' % (response.status,response.reason))


# Submit the MQL write q and return the result as a Python object.
# Authentication credentials are required, obtained from login()
# Raises MQLError if the query was invalid. Raises urllib2.HTTPError if
# mqlwrite returns an HTTP status code other than 200
def write(query, credentials):
    # We're requesting this URL
    req = urllib2.Request('http://%s%s' % (host, writeservice))
    # Send our authentication credentials as a cookie
    req.add_header('Cookie', credentials)
    # This custom header is required and guards against XSS attacks
    req.add_header('X-Metaweb-Request', 'True')
    # The body of the POST request is encoded URL parameters
    req.add_header('Content-type', 'application/x-www-form-urlencoded')
    # Wrap the query object in a query envelope
    envelope = {'qname': {'query': query}}
    # JSON encode the envelope
    encoded = simplejson.dumps(envelope)
    print encoded
    # Use the encoded envelope as the value of the q parameter in the body
    # of the request.  Specifying a body automatically makes this a POST.
    req.add_data(urllib.urlencode({'queries':encoded}))

    # Now do the POST
    f = urllib2.urlopen(req)
    response = simplejson.load(f)   # Parse HTTP response as JSON
    print response
    inner = response['qname']       # Open outer envelope; get inner envelope

    # If anything was wrong with the invocation, mqlwrite will return an HTTP
    # error, and the code above with raise urllib2.HTTPError.
    # If anything was wrong with the query, we will get an error status code
    # in the response envelope.
    # we raise our own MQLError exception.
    if not inner['code'].startswith('/api/status/ok'):
        error = inner['messages'][0]
        raise MQLError('%s: %s' % (error['code'], error['message']))

    # If there was no error, then just return the result from the envelope
    return inner['result']

# Upload the specified content (and give it the specified type).
# Return the guid of the /type/content object that represents it.
# The returned guid can be used to retrieve the content with /api/trans/raw.
def upload(content, type, credentials):
    # This is the URL we POST content to
    url = 'http://%s%s'%(host,uploadservice)
    # Build the HTTP request
    req = urllib2.Request(url, content)         # URL and content to POST
    req.add_header('Content-Type', type)        # Content type header
    req.add_header('Cookie', credentials)       # Authentication header
    req.add_header('X-Metaweb-Request', 'True') # Guard against XSS attacks
    f = urllib2.urlopen(req)                # POST the request
    response = simplejson.load(f)           # Parse the response
    if not response['code'].startswith('/api/status/ok'):
        error = response['messages'][0]
        raise MQLError('%s: %s' % (error['code'], error['message']))
    return response['result']['id']         # Extract and return content id
