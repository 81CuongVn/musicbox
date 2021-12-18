# Simple Discord Music Bot

## Local Host:
### Requirements:
* Python 3.7+
* FFMPEG executable in PATH
* Discord, both app and developer bot (ownership)

### Usage:
* Manually create a file named **`.env``** and insert your bot-token (as BOT_TOKEN) and bot-id (as BOT_ID)
* Install required python libraries with ```pip install -r requirements.txt```
* Add your bot to your server with the link provided in the Discord Developer Portal
* Start the bot with ```py main.py```

## Cloud Host (Heroku):
### Requirements:
* Python, FFMPEG and Opus Buildpacks in Heroku
* Discord, both app and developer bot (ownership)

### Usage:
* Connect the Git-Repository to Heroku under Deploy on the Heroku Dashboard
* Add your bot-token (as BOT_TOKEN) and bot-id (as BOT_ID) as config vars to Heroku under Settings
* Deploy the bot under Deploy (not needed if automatic deploys are enabled)
* Turn on your Dyno Worker under Resources
* Add your bot to your server with the link provided in the Discord Developer Portal
* For 24/7 host: Add your credit card to increase dyno hours for free

## Key Features:
* Ability to play songs from youtube urls or search keywords
* Play, queue, repeat, pause, resume, stop and skip songs
* View songs in queue and remove specific songs
* Multi-server usage support
* Youtube playlist support (limited to playlists with ~ 20 songs due to bandwidth reasons)

## Future Milestones:
* support for spotify links