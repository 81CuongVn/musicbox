# Simple Discord Music Bot

## Local Host:
### Requirements:
* Python 3.7+
* FFMPEG executable in PATH
* Discord, both app and developer bot

### Usage:
* In main.py: Enter the token of your bot in "bot_token" (Do NOT share your token!!)
* Open your terminal, navigate to the file location and type "py main.py"
* Add your bot to your server with the link provided in the Discord Developer Portal
  
## Cloud Host (Heroku):
### Requirements:
* Python, FFMPEG and Opus Buildpacks
* Discord, both app and developer bot
  
### Usage:
* In main.py: Enter the token of your bot in "bot_token" (Do NOT share your token!!)
* Push it to the (!private!) Git-Repository
* Connect the Git-Repository to Heroku under Deploy on the Heroku Dashboard
* Deploy it under Deploy (Automatic or Manual)
* Turn on your Dyno Worker under Resources
* Add your bot to your server with the link provided in the Discord Developer Portal

## Key Features:
* Ability to output streamed or downloaded songs via youtube search
* Play, queue, repeat, pause, resume, stop and skip songs
* View songs in queue and remove specific songs

## Future Milestones:
* make bot exception/spam/abuse proof (e.g. limits for long videos)
* support for multiple discord servers?
* internal cleanups
* make cogs loadable
