# SCP-079-NOPORN

This bot is used to auto delete NSFW media messages.

## How to use

See [this article](https://scp-079.org/noporn/).

## To Do List

- [x] Auto delete NSFW media messages
- [x] Update user's score
- [x] Watch ban or ban by checking user's score and status
- [x] Managed by SCP-079-CONFIG
- [x] Add recheck feature

## Requirements

- Python 3.6 or higher.
- `requirements.txt` : APScheduler Pillow pyAesCrypt pyrogram[fast] nsfw
- Ubuntu: `sudo apt update && sudo apt install caffe-cpu`

## Files

- plugins
    - functions
        - `channel.py` : Send messages to channel
        - `etc.py` : Miscellaneous
        - `file.py` : Save files
        - `filters.py` : Some filters
        - `group.py` : Functions about group
        - `ids.py` : Modify id lists
        - `image.py` : Functions about image
        - `telegram.py` : Some telegram functions
        - `timers.py` : Timer functions
        - `user.py` : Functions about user
    - handlers
        - `callback.py` : Handle callbacks
        - `command` : Handle commands
        - `message.py`: Handle messages
    - `glovar.py` : Global variables
- `.gitignore` : Ignore
- `config.ini.example` -> `config.ini` : Configuration
- `LICENSE` : GPLv3
- `main.py` : Start here
- `README.md` : This file
- `requirements.txt` : Managed by pip

## Contribute

Welcome to make this project even better. You can submit merge requests, or report issues.

## License

Licensed under the terms of the [GNU General Public License v3](LICENSE).
