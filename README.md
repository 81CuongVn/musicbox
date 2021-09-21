# Simple Discord Music Bot

## Requirements:
* Python 3.7+
* FFMPEG executable in PATH
* Discord, both app and developer bot

## Usage:
* In main.py: Enter the token of your bot in "bot_token"
* Local Host: Open your terminal, navigate to the file location and type "py main.py"
* Heroku Cloud Host: add python, ffmpeg and opus buildpacks, then deploy it
* Overview of available commands via !help

## Key Features:
* Ability to output streamed or downloaded songs via youtube search
* Play, queue, repeat, pause, resume, stop and skip songs
* View songs in queue and remove specific songs

## Future Milestones:
* make bot exception proof (e.g. limits for long videos)
* support for multiple discord servers?
* internal cleanups
* make cogs loadable
