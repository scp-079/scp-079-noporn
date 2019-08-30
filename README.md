# SCP-079-NOPORN

This bot is used to auto delete NSFW media messages.

## How to use

See [this article](https://scp-079.org/noporn/).

## To Do List

- [x] Auto delete NSFW media messages
- [x] Update user's score
- [x] Watch ban or ban by checking user's score and status
- [x] Managed by SCP-079-CONFIG

## Requirements

- Python 3.6 or higher
- Ubuntu: `sudo apt update && sudo apt install caffe-cpu opencc -y`
- Follow the file `fix.py` to fix a error
- virtualenv: `virtualenv -p python3 scp-079 --system-site-packages`
- pip: `pip install -r requirements.txt` or `pip install -U APScheduler OpenCC Pillow pyAesCrypt pyrogram[fast] nsfw numpy scikit-image`

## Files

- plugins
    - functions
        - `channel.py` : Functions about channel
        - `etc.py` : Miscellaneous
        - `file.py` : Save files
        - `filters.py` : Some filters
        - `fix.py` : Show steps to fix an error
        - `group.py` : Functions about group
        - `ids.py` : Modify id lists
        - `image.py` : Functions about image
        - `receive.py` : Receive data from exchange channel
        - `telegram.py` : Some telegram functions
        - `tests.py` : Some test functions
        - `timers.py` : Timer functions
        - `user.py` : Functions about user and channel object
    - handlers
        - `command.py` : Handle commands
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
