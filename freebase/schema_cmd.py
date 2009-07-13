from optparse import OptionParser
import getpass
import sys

from freebase.api import HTTPMetawebSession

from freebase.schema import dump_base, dump_type, restore

try:
    import jsonlib2 as json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        import json

def fb_save_base():
    op = OptionParser(usage='%prog [options] baseid')
    
    op.disable_interspersed_args()
    
    op.add_option('-s', '--service', dest='service_host',
                    metavar='HOST',
                    default="freebase.com",
                    help='Freebase HTTP service address:port')
    
    op.add_option('-S', '--sandbox', dest='use_sandbox',
                    default=False, action='store_true',
                    help='shortcut for --service=sandbox-freebase.com')

    options, args = op.parse_args()
    
    service_host = options.service_host
    if options.use_sandbox:
        service_host = "sandbox-freebase.com"

    if len(args) < 1:
        op.error('Required baseid missing')
    
    if len(args) > 1:
        op.error('Too many arguments')
    
    s = HTTPMetawebSession(service_host)
    
    print >> sys.stdout, json.dumps(dump_base(s, args[0]), indent=2)
    
def fb_save_type():
    op = OptionParser(usage='%prog [options] typeid ')
    
    op.disable_interspersed_args()

    op.add_option('-s', '--service', dest='service_host',
                    metavar='HOST',
                    default="freebase.com",
                    help='Freebase HTTP service address:port')
    
    op.add_option('-S', '--sandbox', dest='use_sandbox',
                    default=False, action='store_true',
                    help='shortcut for --service=sandbox-freebase.com')
    
    op.add_option('-n', '--no-follow', dest='follow',
                    default=False, action='store_false',
                    help="Don't follow types, only copy the one specified.")
    
    op.add_option('-f', '--follow', dest="follow",
                    default=True, action="store_true",
                    help="Follow the types (you might end up copying multiple types)")


    options,args = op.parse_args()
    
    service_host = options.service_host
    if options.use_sandbox:
        service_host = "sandbox-freebase.com"

    if len(args) < 1:
        op.error('Required typeid missing')
    
    if len(args) > 1:
        op.error('Too many arguments')
    
    s = HTTPMetawebSession(service_host)
    print >> sys.stdout, json.dumps(dump_type(s, args[0], options.follow), indent=2)
    

def fb_restore():
    op = OptionParser(usage='%prog [options] new_location graph_output_from_dump*_command')
    
    op.disable_interspersed_args()

    op.add_option('-s', '--service', dest='service_host',
                    metavar='HOST',
                    help='Freebase HTTP service address:port')
    
    op.add_option('-S', '--sandbox', dest='use_sandbox',
                    default=False, action='store_true',
                    help='shortcut for --service=sandbox-freebase.com (default)')
    
    op.add_option('-F', '--freebase', dest='use_freebase',
                    default=False, action='store_true',
                    help='shortcut for --service=freebase.com (not default)')

    op.add_option('-u', '--username', dest='username',
                    action='store',
                    help='username for freebase service')

    op.add_option('-p', '--password', dest='password',
                    action='store',
                    help='password for freebase service')

                    

    options,args = op.parse_args()

    if (options.username and not options.password) or (not options.username and options.password):
        op.error("You must supply both a username and password")

    if options.use_sandbox and options.use_freebase:
        op.error("You can't use both freebase and sandbox!")
    
    if options.service_host and (options.use_sandbox or options.use_freebase):
        op.error("You can't specify both --service and --freebase or --sandbox")
    
    if not options.service_host and not options.use_sandbox and not options.use_freebase:
        op.error("You have to specify to upload to sandbox or production (freebase)")
    
    service_host = options.service_host
    if options.use_sandbox:
        service_host = "sandbox-freebase.com"
    if options.use_freebase:
        service_host = "freebase.com"

    s = login(service_host, username=options.username, password=options.password)
    
    newlocation = args[0]
    if len(args) == 1:
        graphfile = "-" #stdin
    else: graphfile = args[1]
    if graphfile != "-":
        fg = open(graphfile, "r")
        graph = json.load(fg)
        fg.close()
    if graphfile == "-": # use stdin
        graph = json.load(sys.stdin)
        
    restore(s, graph, newlocation, ignore_types=None)

def login(api_host, username=None, password=None):
    
    s = HTTPMetawebSession(api_host)
    if not username:
        print "In order to perform this operation, we need to use a valid freebase username and password"
        username = raw_input("Please enter your username: ")
        try:
            password = getpass.getpass("Please enter your password: ")
        except getpass.GetPassWarning:
            password = raw_input("Please enter your password: ")

    s.login(username, password)

    print "Thanks!"
    return s