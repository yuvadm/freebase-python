#!/usr/bin/python
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

import sys
from freebase.api.session import HTTPMetawebSession

_base = HTTPMetawebSession("sandbox.freebase.com")

__all__ = ["HTTPMetawebSession"]

# we want to add base's functions to __init__.py
# so that we can say freebase.func() and really
# just call base.func()

# a little trick to refer to ourselves
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
# business going. Plus, this is cleaner.
del self

# we want dir(freebase) to be clean
del funcname, func
