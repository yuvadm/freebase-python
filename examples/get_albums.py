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

query = {
    "id" :   "/en/the_beatles",
    "type" : "/music/artist",
    "album" : [{
        "name" :         None,
        "release_date" : None,
        "track": {
            "return" : "count"
        },
        "sort" : "release_date"
    }]
}

results = freebase.mqlread(query)
for album in results.album:
    print "Album \"" + album.name + "\" has " + str(album.track) + " tracks."


# Album "Please Please Me" has 14 tracks.
# Album "From Me to You" has 2 tracks.
# Album "Introducing... The Beatles" has 24 tracks.
# Album "She Loves You" has 2 tracks.
# Album "With the Beatles" has 14 tracks.
# Album "I Want to Hold Your Hand" has 2 tracks.
# Album "Meet the Beatles" has 12 tracks.
# Album "Second Album" has 11 tracks.
# Album "Something New" has 11 tracks.
# Album "A Hard Day's Night" has 36 tracks.
# Album "I Feel Fine" has 2 tracks.
# Album "Beatles for Sale" has 14 tracks.
# Album "Beatles '65" has 11 tracks.
# Album "The Early Beatles" has 11 tracks.
# Album "Beatles VI" has 11 tracks.
# Album "Help! / I'm Down" has 2 tracks.
# Album "Help!" has 14 tracks.
# Album "Rubber Soul" has 14 tracks.
# Album "We Can Work It Out / Day Tripper" has 2 tracks.
# Album "Paperback Writer / Rain" has 2 tracks.
# Album "Yesterday... and Today" has 11 tracks.
# Album "Revolver" has 14 tracks.
# Album "Strawberry Fields Forever / Penny Lane" has 2 tracks.
# Album "Sgt. Pepper's Lonely Hearts Club Band" has 24 tracks.
# Album "Magical Mystery Tour" has 11 tracks.
# Album "Hello, Goodbye" has 2 tracks.
# Album "Magical Mystery Tour" has 6 tracks.
# Album "Lady Madonna" has 2 tracks.
# Album "Hey Jude" has 2 tracks.
# Album "The White Album" has 81 tracks.
# Album "Yellow Submarine" has 13 tracks.
# Album "Get Back" has 2 tracks.
# Album "Abbey Road" has 17 tracks.
# Album "Hey Jude" has 10 tracks.
# Album "Let It Be" has 12 tracks.
# Album "1962-1966" has 26 tracks.
# Album "1967-1970" has 28 tracks.
# Album "Love Songs" has 25 tracks.
# Album "The Beatles at the Hollywood Bowl" has 13 tracks.
# Album "Sgt. Pepper's Lonely Hearts Club Band" has 3 tracks.
# Album "Past Masters, Volume One" has 18 tracks.
# Album "Past Masters, Volume Two" has 15 tracks.
# Album "Rockin' at the Star-Club" has 16 tracks.
# Album "The Early Tapes of the Beatles" has 14 tracks.
# Album "Live at the BBC" has 69 tracks.
# Album "Anthology 1" has 60 tracks.
# Album "Free as a Bird" has 4 tracks.
# Album "The Best Of [26 Unforgetable Hit Songs]" has 26 tracks.
# Album "Real Love" has 4 tracks.
# Album "Anthology 2" has 45 tracks.
# Album "Anthology 3" has 50 tracks.
# Album "Yellow Submarine Songtrack" has 15 tracks.
# Album "1" has 27 tracks.
# Album "Let It Be... Naked" has 12 tracks.
# Album "The Capitol Albums, Volume 1" has 90 tracks.
# Album "The Capitol Albums, Volume 2" has 68 tracks.
# Album "16 Superhits, Volume 1" has 16 tracks.
# Album "16 Superhits, Volume 2" has 16 tracks.
# Album "16 Superhits, Volume 3" has 16 tracks.
# Album "16 Superhits, Volume 4" has 16 tracks.
# Album "1962 Live at Star Club in Hamburg" has 24 tracks.
# Album "1962 Live Recordings" has 30 tracks.
# Album "1962-1966 (Red Album)" has 26 tracks.
# Album "1962-1970" has 18 tracks.
# Album "A Collection of Beatles Oldies (UK Mono LP)" has 16 tracks.
# Album "Alternate Rubber Soul" has 28 tracks.
# Album "Anthology (disc 3)" has 22 tracks.
# Album "Beatles Tapes III: The 1964 World Tour" has 19 tracks.
# Album "Beatles VI (Stereo and Mono)" has 22 tracks.
# Album "Best Selection 1962-1968 Part 3" has 20 tracks.
# Album "Best, Volume 4: 1964" has 12 tracks.
# Album "Best, Volume 9: 1966" has 12 tracks.
# Album "Christmas" has 20 tracks.
# Album "Complete Rooftop Concert 1" has 22 tracks.
# Album "EP Collection (disc 1)" has 4 tracks.
# Album "EP Collection (disc 10)" has 4 tracks.
# Album "EP Collection (disc 11: Yesterday)" has 4 tracks.
# Album "EP Collection (disc 12)" has 4 tracks.
# Album "EP Collection" has 12 tracks.
# Album "EP Collection (disc 2: Twist and Shout)" has 4 tracks.
# Album "EP Collection (disc 3)" has 4 tracks.
# Album "EP Collection (disc 4)" has 4 tracks.
# Album "EP Collection (disc 5)" has 4 tracks.
# Album "EP Collection (disc 6)" has 4 tracks.
# Album "EP Collection (disc 7)" has 4 tracks.
# Album "EP Collection (disc 8)" has 4 tracks.
# Album "EP Collection (disc 9)" has 4 tracks.
# Album "EP Collection, Volume 1" has 32 tracks.
# Album "EP Collection, Volume 2" has 26 tracks.
# Album "From Yesterday Forever" has 22 tracks.
# Album "Get Back" has 20 tracks.
# Album "Golden Best 20, Volume 1" has 19 tracks.
# Album "In the Beginning" has 12 tracks.
# Album "Introducing the Beatles (Us Mono Ver. 2)" has 12 tracks.
# Album "Live at Star Club 1962, Volume 1" has 11 tracks.
# Album "Live in Adelaide & Houston, Texas" has 18 tracks.
# Album "Live in Japan 1964" has 22 tracks.
# Album "Live in Paris 1965 2" has 24 tracks.
# Album "Live in Paris, 1965" has 23 tracks.
# Album "Mythology 2 (disc 1)" has 21 tracks.

