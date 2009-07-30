import sys

from freebase.api.session import HTTPMetawebSession
import sandbox

__all__ = ["HTTPMetawebSession", "sandbox"]

_base = HTTPMetawebSession("http://api.freebase.com")

# we want to add base's functions to __init__.py
# so that we can say freebase.func() and really
# just call base.func()

# a little trick to refer to __init__
# self isn't defined because __init__ is in
# a world in and of itself 
self = sys.modules[__name__]

for funcname in dir(_base):
    
    # we only want the 'real' functions
    if not funcname.startswith("_"):
        func = getattr(_base, funcname)
        
        # let's make sure we're getting functions
        # instead of constants or whatever
        if callable(func):
            
            # we're setting these functions
            # so that they can be called like
            # freebase.funcname -> base.func()
            setattr(self, funcname, func)
            
            # make sure we import the base's
            # functions if we import freebase
            __all__.append(funcname)

# we don't want any self-referencing
# business going on. Plus, this is cleaner.
del self

# we want dir(freebase) to be clean
del funcname, func
