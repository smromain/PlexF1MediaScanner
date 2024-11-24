PlexF1MediaScanner
==================

Fork from [kennethx/PlexF1MediaScanner](https://github.com/kennethx/PlexF1MediaScanner). Props to them!

This is a custom scanner for Plex for parsing data for Formula 1 race weekends. It should be the scanner for a library that **only**
contains F1 content, it wont match anything else.

## Installation

- Create a new file called `f1.env` in the same directory as `Formula1.py` and add the path to the common library, eg `PLEX_SCANNER_LIBRARY_PATH="C:\Program Files\Plex\Plex Media Server\Resources\Plug-ins-f2c27da23\Scanners.bundle\Contents\Resources\Common"` (there is a sample in the repo).
- Copy the `Formula1.py` file and the `f1.env` file to your Scanners/Series directory, for Linux this is `/var/lib/plexmediaserver/Library/Application Support/Plex Media Server/Scanners/Series/` and for windows this is `C:\Users\<username>\AppData\Local\Plex Media Server\Scanners\Series\`
- Add a new `TV shows` library called `Formula 1` (or whatever), add the folder containing F1 broadcasts.
- Under `Advanced`, select `Formula1` as the scanner and `Personal Media Shows` for the agent. Also set `Seasons` to `Hide` (we only ever have 1 season per session).

## Folder Structure

The script expects the media to be formatted similar to the below:

```
F1
├── Formula.1.2020x05.70th-Anniversary-GB.Race.SkyF1HD.1080p
│   ├── 01.Pre-Race.Buildup.mp4
│   ├── 02.Race.Session.mp4
│   ├── 03.Post-Race.Analysis.mp4
└── Formula.1.2020x06.Spain.Qualifying.SkyF1HD.1080p
    ├── 01.Pre-Qualifying.Buildup.mp4
    ├── 02.Qualifying.Session.mp4
    ├── 03.Post-Qualifying.Analysis.mp4
```

Each F1 session will show as a TV Show in Plex, with each event (eg Qualifying, Race) showing as an episode inside that. Annoyingly you cannot have different sessions as different TV seasons without messing around with the folder structure. Here's what it looks like:

![Plex Screenshot](screenshot.png "Plex Screenshot")

The scanner (since I havent bothered writing a metadata agent) will try to pull some artwork from [thesportsdb.com](https://www.thesportsdb.com/league/4370) and will drop them into files on the filesystem. You probably could do some renaming and get
[SportScanner](https://github.com/mmmmmtasty/SportScanner) to pull in all the metadata but since that's no longer maintained its less risky to just use thesportsdb.com directly and get plex to use local images.

## Troubleshooting

Regular expressions aren't perfect (especially mine) and if your file and directory structure doesnt match what I think it is then stuff wont appear in your library.
To see what went wrong with detection, check out the log file (`/var/lib/plexmediaserver/Library/Application Support/Plex Media Server/Logs/Formula1.log`). 

To force plex to retry, first get the ID of the your F1 Library (`/usr/lib/plexmediaserver/Plex\ Media\ Scanner --list`) then force an update: `/usr/lib/plexmediaserver/Plex\ Media\ Scanner --force --scan --refresh --section YOUR_SECTION_NUMBER`.
