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

import freebase

print freebase.search("Kurt Vonnegut")


#from freebase.api import HTTPMetawebSession, MetawebError

#username='username'
#password='password'

query = {    'type':'/music/artist',
             'name':'Sting',
             'album':[],        
         }
#credentials = freebase.login(username, password)

#mss = HTTPMetawebSession('www.freebase.com')
#result = mss.mqlread(query)

#for album in result.album:
#    print album


# output :
#The Dream of the Blue Turtles
#Bring on the Night (disc 1)
#Bring on the Night (disc 2)
#...Nothing Like the Sun
#...Nada Como el Sol
#The Soul Cages
#Acoustic Live in Newcastle
#All This Time
#Mad About You
#Ten Summoner's Tales
#Demolition Man
#Fields of Gold: The Best of Sting 1984-1994
#The Living Sea
#Let Your Soul Be Your Pilot
#Mercury Falling
#Brand New Day
#Desert Rose
#...All This Time
#Still Be Love in the World
#Sacred Love
#Stolen Car
#1991-10-02: Hollywood Bowl, Los Angeles, CA, USA
#Best Ballads
#Brand New Day (bonus disc)
#Brand New Day: The Remixes
#Dolphins
#Englishman in New York
#Five Live!
#Fortress: The London Symphony Orchestra performs Sting
#I Shall Be Released (disc 2)
#I Shall Be Released (disc 3)
#I Shall Be Released (disc 4)
#I Shall Be Released (disc 5)
#I'm So Happy I Can't Stop Crying
#If I Ever Lose My Faith in You
#If You Love Somebody Set Them Free
#Live at the BBC 1st Dec 2001
#Live at the Universal Amphiteater: 10/29/99
#Live in Central Park (disc 2)
#Mercury Falling (bonus disc)
#Moon Walking
#My Funny Friend and Me
#My Funny Valentine
#Send Your Love Remix Album
#Sting at the Movies
#Ten Summoners Tales (DTS)
#They Dance Alone (Gueca Solo)
#This Cowboy Song
#Unplugged (disc 1: The Rehearsal)
#Unplugged (disc 2: Complete Live)
#When We Dance
#You Still Touch Me
