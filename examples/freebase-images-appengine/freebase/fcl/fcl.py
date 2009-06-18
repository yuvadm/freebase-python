#!/usr/bin/env python
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

import os, sys, re, time, stat

from optparse import OptionParser
import getpass
import cookielib
import logging
import simplejson


from fbutil import FbException, CmdException, log, default_propkeys
console = logging.StreamHandler()
log.addHandler(console)

from freebase.api import HTTPMetawebSession, MetawebError, attrdict

_cookiedir = None
if os.environ.has_key('HOME'):
    _cookiedir = os.path.join(os.environ['HOME'], '.pyfreebase')


class Command(object):
    def __init__(self, module, name, func):
        self.module = module
        self.name = name
        self.func = func

        PROG = re.compile(r'\%prog')
        NEWLINE = re.compile(r'(?:\r?\n)+')

        # fill in self.doc
        if isinstance(func.__doc__, basestring):
            doc = PROG.sub('fcl', func.__doc__ + '\n')
            self.shortdoc, self.doc = NEWLINE.split(doc, 1)
        else:
            self.shortdoc = '(missing documentation)'
            self.doc = '(missing documentation)'



class FbCommandHandler(object):

    def __init__(self):
        self.service_host = 'www.freebase.com'
        self.cookiejar = None
        self.cwid = ''
        self.progpath = 'fcl'
        self.commands = {}

        self.cookiefile = None
        if _cookiedir is not None:
            self.cookiefile = os.path.join(_cookiedir, 'cookiejar')


    def init(self):
        if self.cookiefile is not None:
            self.cookiejar = cookielib.LWPCookieJar(self.cookiefile)
            if os.path.exists(self.cookiefile):
                try:
                    self.cookiejar.load(ignore_discard=True)
                except cookielib.LoadError:
                    log.warn('error loading cookies')

        #print 'start cookies %r' % self.cookiejar

        self.mss = HTTPMetawebSession(self.service_host,
                                      cookiejar=self.cookiejar)


    def absid(self, path):
        if path is None:
            path = ''
        if path.startswith('/'):
            return path

        if not isinstance(self.cwid, basestring) or not self.cwid.startswith('/'):
            # svn cwid support is disabled because it relies on some svn glue that
            # was not sufficiently well thought out.
            # raise CmdException("can't resolve relative id %r without cwid - see 'fcl help pwid'" % (path))
            raise CmdException("no support for relative id %r" % (path))

        if path == '' or path == '.':
            return self.cwid

        return self.cwid + '/' + path


    def absprop(self, propkey):
        if propkey.startswith('/'):
            return propkey

        # check schemas of /type/object and /type/value,
        #  as well as other reserved names
        if propkey in default_propkeys:
            return default_propkeys[propkey]

        return self.absid(propkey)

    def thead(self, *args):
        strs = ['%r' % arg
                for arg in args]
        print '\t'.join(strs)

    def trow(self, *args):
        print '\t'.join(args)
        return
        strs = ['%r' % arg
                for arg in args]
        print '\t'.join(strs)

    def save(self):
        #print 'end cookies %r' % self.cookiejar
        if _cookiedir and self.cookiefile.startswith(_cookiedir):
            # create private cookiedir if needed
            if not os.path.exists(_cookiedir):
                os.mkdir(_cookiedir, 0700)
                os.chmod(_cookiedir, stat.S_IRWXU)

        if self.cookiejar is None:
            return

        self.cookiejar.save(ignore_discard=True)

        # save the cwd and other state too


    def import_commands(self, modname):
        """
        import new fb commands from a file
        """
        namespace = {}
    
        pyimport = 'from %s import *' % modname
        exec pyimport in namespace
        mod = sys.modules.get(modname)

        commands = [Command(mod, k[4:], getattr(mod, k))
                    for k in getattr(mod, '__all__', dir(mod))
                    if (k.startswith('cmd_')
                        and callable(getattr(mod, k)))]

        
        for cmd in commands:
            log.info('importing %r' % ((cmd.name, cmd.func),))
            self.commands[cmd.name] = cmd
    
        log.info('imported %r from %r' % (modname, mod.__file__))


    def dispatch(self, cmd, args):
        if cmd in self.commands:
            try:
                self.commands[cmd].func(self, *args)
            except KeyboardInterrupt, e:
                sys.stderr.write('%s\n' % (str(e),))
            except FbException, e:
                sys.stderr.write('%s\n' % (str(e),))
            except CmdException, e:
                sys.stderr.write('%s\n' % (str(e),))
            except MetawebError, e:
                sys.stderr.write('%s\n' % (str(e),))
        else:
            self.oparser.error('unknown subcommand %r, try "%s help"' % (cmd, self.progpath))

        self.save()
        

    def cmdline_main(self):
        op = OptionParser(usage='%prog [options] command [args...] ')
        self.oparser = op

        op.disable_interspersed_args()

        op.add_option('-d', '--debug', dest='debug',
                        default=False, action='store_true',
                        help='turn on debugging output')

        op.add_option('-v', '--verbose', dest='verbose',
                        default=False, action='store_true',
                        help='verbose output')

        op.add_option('-V', '--very-verbose', dest='very_verbose',
                        default=False, action='store_true',
                        help='lots of debug output')

        op.add_option('-s', '--service', dest='service_host',
                        metavar='HOST',
                        default=self.service_host,
                        help='Freebase HTTP service address:port')

        op.add_option('-S', '--sandbox', dest='use_sandbox',
                        default=False, action='store_true',
                        help='shortcut for --service=sandbox.freebase.com')

        op.add_option('-c', '--cookiejar', dest='cookiefile',
                        metavar='FILE',
                        default=self.cookiefile,
                        help='Cookie storage file (will be created if missing)')
        options,args = op.parse_args()

        if len(args) < 1:
            op.error('required subcommand missing')


        loglevel = logging.WARNING
        if options.verbose:
            loglevel = logging.INFO
        if options.very_verbose:
            loglevel = logging.DEBUG

        console.setLevel(loglevel)
        log.setLevel(loglevel)

        if options.use_sandbox:
            self.service_host = 'sandbox.freebase.com'
        else:
            self.service_host = options.service_host

        self.cookiefile = options.cookiefile
        #self.progpath = sys.argv[0]
        
        self.init()

        self.mss.log.setLevel(loglevel)
        self.mss.log.addHandler(console)

        self.import_commands('freebase.fcl.commands')
        self.import_commands('freebase.fcl.mktype')

        cmd = args.pop(0)
        self.dispatch(cmd, args)

# entry point for script
def main():
    try:
        # turn off crlf output on windows so we work properly
        # with unix tools.
        import msvcrt
        msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
        msvcrt.setmode(sys.stderr.fileno(), os.O_BINARY)
    except ImportError:
        pass

    fb = FbCommandHandler()
    fb.cmdline_main()

if __name__ == '__main__':
    main()
