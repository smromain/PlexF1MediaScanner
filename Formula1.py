#!/usr/bin/env python

#     Copyright (C) 2013  Casey Duquette
#
#     This program is free software; you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation; either version 2 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.

"""
Custom scanner plugin for Plex Media Server for Formula 1 Broadcasts.
"""

import re, os, os.path
import sys
import logging

# I needed some plex libraries, you may need to adjust your plex install location accordingly
sys.path.append("/var/lib/plexmediaserver/Library/Application Support/Plex Media Server/Scanners/Series")
sys.path.append("/usr/lib/plexmediaserver/Resources/Plug-ins-b23ab3896/Scanners.bundle/Contents/Resources/Common/")

import Media, VideoFiles, Stack, Utils
from mp4file import mp4file, atomsearch
from pprint import pformat


# Expected format (smcgill1969):
# Formula.1.2020x05.70th-Anniversary-GB.Race.SkyF1HD.1080p/02.Race.Session.mp4
episode_regexp = 'Formula.1[\._ ](?P<year>[0-9]{4})x(?P<raceno>[0-9]{2})[\._ ](?P<location>.*?)[\._ ](?P<session>.*?).SkyF1HD.(1080p|SD)/(?P<episode>.*?)[\._ ](?P<description>.*?).mp4'

sessions = {}
sessions['Practice'] = 1
sessions['Qualifying'] = 2
sessions['Race'] = 3

def remove_prefix(s, prefix):
    return s[len(prefix):] if s.startswith(prefix) else s

# Look for episodes.
def Scan(path, files, mediaList, subdirs, language=None, root=None):
    logging.basicConfig(filename='/var/lib/plexmediaserver/Library/Application Support/Plex Media Server/Logs/Formula1.log', level=logging.DEBUG)
    logging.basicConfig(level=logging.DEBUG)

    # Scan for video files.
    VideoFiles.Scan(path, files, mediaList, subdirs, root)

    # Run the select regexp for all media files.
    for i in files:
        logging.debug('Processing: %s' % i)
        file = remove_prefix(i, root + '/')

        match = re.search(episode_regexp, file)
        if match:
            logging.debug("Regex matched file:" + file)

            # Extract data.
            show = 'Formula 1'
            year = int(match.group('year').strip())
            show = "%s %s" % (show, year) # Make a composite show name like Formula1 + yyyy
            location = match.group('location').replace("-"," ")

            # episode is just a meaningless index to get the different FP1-3, Qualifying, Race and other files to
            # be listed under a location i.e. Spain, which again is mapped to season number - as season can not contain a string
            episode = int(match.group('episode').strip())

            # description will be the displayed filename when you browse to a location (season number)
            description = (location + " " + match.group('description')).replace("."," ") # i.e. # spain grand prix free practice 3
            library_name = "%sx%s: %s %s" %(year, match.group('raceno'), location, match.group('session'))

            logging.debug("show: %s" % show)
            logging.debug("location: %s" % location)
            logging.debug("episode: %s" % episode)
            logging.debug("description: %s" % description)
            logging.debug("library_name: %s" % library_name)

            tv_show = Media.Episode(
                library_name,         # show (inc year(season))
                sessions[match.group('session')],   # season. Must be int, strings are not supported :(
                episode,            # episode, indexed the files for a given show/location
                description,        # includes location string and ep name i.e. Spain Grand Prix Qualifying
                year)               # the actual year detected, same as used in part of the show name

            logging.debug("tv_show created")
            tv_show.parts.append(i)
            logging.debug("part added to tv_shows")
            mediaList.append(tv_show)
            logging.debug("added tv_show to mediaList")
        else:
            logging.debug("Regex FAILED to match file: "+file)

    for s in subdirs:
        nested_subdirs = []
        nested_files = []
        for z in os.listdir(s):
            if os.path.isdir(os.path.join(s, z)):
                nested_subdirs.append(os.path.join(s, z))
            elif os.path.isfile(os.path.join(s, z)):
                nested_files.append(os.path.join(s, z))
        # This should be safe, since we're not following symlinks or anything that might cause a loop.
        Scan(s, nested_files, mediaList, nested_subdirs, root=root)

    # Stack the results.
    Stack.Scan(path, files, mediaList, subdirs)

import sys

if __name__ == '__main__':
  print "Hello, world!"
  path = sys.argv[1]
  files = [os.path.join(path, file) for file in os.listdir(path)]
  media = []
  print("Files: %s" % files)
  Scan(path, files, media, [])
  print "Media:", media
