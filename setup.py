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

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


json = []

# if jsonlib2 is already installed, then we're fine
# we don't need anything else
try:
    import jsonlib2
except ImportError:
    # if python version < 2.6, require simplejson
    # if python version >= 2.6, it comes with json

    major, minor, micro, releaselevel, serial = sys.version_info
    if major <= 2 and minor < 6:
       json.append("simplejson")

setup(
    name='freebase',
    version='1.0.3',
    author='Nick Thompson',
    author_email='nix@metaweb.com',
    maintainer_email='developers@freebase.com',
    license='BSD',
    url='http://code.google.com/p/freebase-python/',
    description='Python client library for the freebase.com service',
    long_description="""A Python library providing a convenient
    wrapper around the freebase.com service api, as well as some
    utility functions helpful in writing clients of the api.""",
    packages=['freebase', 'freebase.api', 'freebase.fcl'],
    entry_points = {
        'console_scripts': [
            'fcl = freebase.fcl.fcl:main',
            'fb_save_base = freebase.schema_cmd:fb_save_base',
            'fb_save_type = freebase.schema_cmd:fb_save_type',
            'fb_restore = freebase.schema_cmd:fb_restore'
        ]
    },
    test_suite = "test.runtests.main",
    install_requires=[] + json,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Database :: Front-Ends',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content :: CGI Tools/Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        ],
)

