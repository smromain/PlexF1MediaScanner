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
import urllib
import ssl
import json
from time import sleep
from pprint import pformat

is_windows = hasattr(sys, 'getwindowsversion')
data_dir = os.getenv('LOCALAPPDATA') if is_windows else os.getenv('PLEX_HOME')
scanner_path = os.path.join(data_dir, 'Plex Media Server', 'Scanners', 'Series')

# Check for and load environment variables from f1.env
env_path = os.path.join(scanner_path, 'f1.env')
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                key, value = line.split('=', 1)
                os.environ[key] = value



# Notate in the f1.env file the path to the common library, eg PLEX_SCANNER_LIBRARY_PATH="C:\Program Files\Plex\Plex Media Server\Resources\Plug-ins-f2c27da23\Scanners.bundle\Contents\Resources\Common"
sys.path.append(os.getenv('PLEX_SCANNER_LIBRARY_PATH'))

import Media, VideoFiles, Stack

# Expected format (smcgill1969):
# Formula.1.2020x05.70th-Anniversary-GB.Race.SkyF1HD.1080p/02.Race.Session.mp4
episode_regexp = r'Formula.1[\._ ](?P<year>[0-9]{4})x(?P<raceno>[0-9]{2})[\._ ](?P<location>.*)[\._ ](?P<session>.*?).SkyF1U?HD.(1080p|SD|4K)\\(?P<episode>.*?)[\._ ](?P<description>.*?).mp4'

sessions = {}
sessions['Practice'] = 1
sessions['Qualifying'] = 2
sessions['Race'] = 3

def remove_prefix(s, prefix):
    return s[len(prefix):] if s.startswith(prefix) else s


def download_url(url, filename):
    try:
        insecure_context = ssl._create_unverified_context()
        urllib.urlretrieve(url, filename, context=insecure_context)
        os.chmod(filename, 0666)
    except IOError as e:
        logging.error("Unable to download from url: %s to %s. Error: %s" % (url, filename, e))

def download_art(filename, art_type, season, round, session, event, allow_fake=False):
    """Download and save artwork from thesportsdb

    season = year
    round = raceno
    event = eg "Australian Grand Prix"
    session = Practice/Race/something
    """
    if os.path.exists(filename):
        return

    found = False
    if round == 0:
        logging.warn("Found invalid round, file may not be for a race weekend, eg testing")
        allow_fake = True
    else:
        logging.debug("Downloading artwork to: %s" % filename)

        try:
            insecure_context = ssl._create_unverified_context()
            dataurl = ' https://www.thesportsdb.com/api/v1/json/3/eventsround.php?id=4370&r=%s&s=%s' % (round, season)
            logging.info("Pulling data from: %s" % dataurl)
            eventdata = urllib.urlopen(dataurl, context=insecure_context)
            sleep(2) #sportsdb API limit
            eventdata = json.loads(eventdata.read())

            # try to get an aimage specific to this session
            for event in eventdata['events']:
                # logging.critical(pformat(event))
                # session is likely race/practice/qualy/sprint

                if " shootout " in session.lower():
                    session = "Sprint Shootout"
                elif " sprint " in session.lower():
                    session = "Grand Prix Sprint"
                elif " qualifying " in session.lower():
                    session = "Qualifying"
                elif " race " in session.lower():
                    session = "Grand Prix"

                if event['strEvent'].lower().endswith(session.lower()):
                    if event[art_type]:
                        download_url(event[art_type], filename)
                        found = True
                    
            # get any image for this round instead
            if not found:
                for event in eventdata['events']:
                    if event[art_type]:
                        download_url(event[art_type], filename)
                        found = True
        except Exception as e:
            logging.critical("Unable to download artwork... %s" % e)

    if not found:
        if allow_fake:
            if art_type == "strPoster":
                download_url("https://www.thesportsdb.com/images/media/league/poster/4e1svi1605133041.jpg", filename)
            else:
                download_url("https://github.com/potchin/PlexF1MediaScanner/raw/master/episode_poster.png", filename)
        else:
            logging.warn("Unable to find art for event")
    return




# Look for episodes.
def Scan(path, files, mediaList, subdirs, language=None, root=None):
    logging.basicConfig(filename=os.path.join(data_dir, 'Plex Media Server', 'Logs', 'Formula1.log'), level=logging.DEBUG)

    # Scan for video files.
    VideoFiles.Scan(path, files, mediaList, subdirs, root)

    # Run the select regexp for all media files.
    for i in files:
        logging.debug('Processing: %s' % i)

        file = remove_prefix(i, root + '\\' if is_windows else '/')
        match = re.search(episode_regexp, file)
        if match:
            logging.debug("Regex matched file:" + file)

            # Extract data.
            show = 'Formula 1'
            year = int(match.group('year').strip())
            show = "%s %s" % (show, year) # Make a composite show name like Formula1 + yyyy
            location = match.group('location').replace("-"," ").replace("."," ")

            # episode is just a meaningless index to get the different FP1-3, Qualifying, Race and other files to
            # be listed under a location i.e. Spain, which again is mapped to season number - as season can not contain a string
            episode = int(match.group('episode').strip())

            # description will be the displayed filename when you browse to a location (season number)
            description = (location + " " + match.group('description')).replace("."," ") # i.e. # spain grand prix free practice 3
            library_name = "%sx%s: %s %s" %(year, match.group('raceno'), location, match.group('session'))
            try:
                session = sessions[match.group('session')]
            except KeyError:
                logging.warning('Couldnt match session "%s", Defaulting to 0' % match.group('session'))
                session = 0

            logging.debug("show: %s" % show)
            logging.debug("location: %s" % location)
            logging.debug("episode: %s" % episode)
            logging.debug("description: %s" % description)
            logging.debug("session: %s" % session)
            logging.debug("library_name: %s" % library_name)

            posterfile=os.path.dirname(i)+"/poster.jpg"
            download_art(posterfile, "strPoster", year, int(match.group('raceno')), match.group('session'), location)

            thumbnail=i[:-3]+"jpg"
            download_art(thumbnail, "strThumb", year, int(match.group('raceno')), match.group('session'), location, allow_fake=True)

            fanart=os.path.dirname(i)+"/fanart.jpg"
            download_art(fanart, "strThumb", year, int(match.group('raceno')), match.group('session'), location)

            try:
                tv_show = Media.Episode(
                    library_name,         # show (inc year(season))
                    session,              # season. Must be int, strings are not supported :(
                    episode,              # episode, indexed the files for a given show/location
                    description,          # includes location string and ep name i.e. Spain Grand Prix Qualifying
                    year)                 # the actual year detected, same as used in part of the show name
                
                # force set the title + title_sort to the library_name, otherwise it will default to the folder name

                tv_show.title = library_name
                tv_show.title_sort = library_name

            except Exception as e:
                logging.error(e)
                # sys.exit 1

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
  print("You're not plex!")