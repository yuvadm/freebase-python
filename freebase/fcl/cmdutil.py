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


import sys
import optparse

from math import ceil

import logging
log = logging.getLogger()


class CmdException(Exception):
    pass


# decorator for adding subcommand option parsers
def option(argname, *args, **kws):
    kws['dest'] = argname
    def decorate(f):
        oparser = getattr(f, 'oparser', None)
        if oparser is None:
            # set usage= later?
            f.oparser = oparser = optparse.OptionParser()
            oparser.disable_interspersed_args()

        oparser.add_option(*args, **kws)
        return f
    return decorate


def complete(*types):
    def decorate(f):
        f.types = types
        return f
    return decorate

class TableOut(object):
    def __init__(self):
        self.outf = sys.stdout
        self.rows = []
        self.cols = 1

        # maximum number of lines to buffer
        self.bufmax = 200

        self.termwidth = 80
        self.minspacing = 4

        # should be false if using in a pipeline,
        # true for human user (like ls)
        if hasattr(self.outf, "isatty") and self.outf.isatty():
            self.humane = True
        else:
            self.humane = False

    def __call__(self, *items):
        self.rows.append(items)
        if self.cols < len(items):
            self.cols = len(items)
        if len(self.rows) > self.bufmax:
            self.flush()

    def flush(self):
        if self.humane and self.cols == 1:
            self.pack_list()
        else:
            self.tty_table()

        self.rows = []
        self.cols = 1

    def pack_list(self):
        l = [row[0] for row in self.rows]
        maxlength = 0
        for item in l:
            if maxlength < len(item):
                maxlength = len(item)

        # round maxlength up to tab width
        colwidth = int(ceil(maxlength + self.minspacing - 1))

        if colwidth > 80:
            colwidth = 80

        ncols = self.termwidth // colwidth

        colwidths = [colwidth] * ncols
        all = l + [None]*ncols

        row_major = False
        if row_major:
            items = [all[i:i+ncols] for i in range(0, len(l), ncols)]
        else:
            # standard unix ls order
            nrows = (len(l)+ncols-1) // ncols
            items = [all[i:i+nrows*ncols:nrows] for i in range(0, nrows)]

        self.showtty(colwidths, items)


    def tty_table(self):
        l = self.rows

        colwidths = []
        for row in l:
            if len(colwidths) < len(row):
                colwidths = colwidths + [0] * (len(row) - len(colwidths))
            for i, item in enumerate(row):
                if colwidths[i] < len(item) + self.minspacing:
                    colwidths[i] = len(item) + self.minspacing

        self.showtty(colwidths, l)

    def showtty(self, colwidths, rows):
        """Simple unix style text table output"""

        for row in rows:
            #print '%s %r' % (type(row), row)
            for i, item in enumerate(row):
                if item is None: continue
                self.outf.write(item)
                # fill out column, except for last cell
                if i < len(row) - 1:
                    padding = colwidths[i] - len(item)
                    if padding < 1:
                        padding = 1
                    self.outf.write(' ' * padding)
            self.outf.write('\n')


# "out" is a function for generating a "row" of output
#  the row can be one or more strings
# 
out = TableOut()
    
