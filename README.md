![My project2](https://user-images.githubusercontent.com/28533473/153753522-281bd97a-81c0-4df7-8b39-7b063b83390b.png)
# MusicBox
* A simple youtube music bot for discord

## Key Features:
* Ability to play songs from youtube urls or search keywords
* Play, queue, repeat, pause, resume, stop and skip songs
* View songs in queue and remove specific songs
* Multi-server usage support
* Youtube playlist support (limited to playlists with ~ 20 songs due to bandwidth reasons)
* Supports various fun/useful commands

## Local Host:
### Requirements:
* Python 3.7+
* FFMPEG executable in PATH
* Discord, both app and developer bot (ownership)

### Usage:
* Manually create a file named **`.env`** and insert your bot-token (as BOT_TOKEN) and bot-id (as BOT_ID)
* Install required python libraries with ```pip install -r requirements.txt```
* Add your bot to your server with the link provided in the Discord Developer Portal
* Start the bot with ```py main.py```

## Cloud Host (Heroku):
### Requirements:
* Python, FFMPEG and Opus Buildpacks in Heroku
* Discord, both app and developer bot (ownership)

### Usage:
* Connect the Git-Repository to Heroku under Deploy on the Heroku Dashboard
* Add your bot-token (as BOT_TOKEN), bot-id (as BOT_ID) and tenor-token (as TENOR_TOKEN) as config vars to Heroku under Settings
* Deploy the bot under Deploy (not needed if automatic deploys are enabled)
* Add your bot to your server with the link provided in the Discord Developer Portal
* Turn on your Dyno Worker under Resources
* For 24/7 host: Add your credit card to increase dyno hours for free

## Future Milestones:
* support for longer youtube playlists
* support for spotify links/playlists
