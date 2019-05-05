# SCP-079-NOPORN - Auto delete NSFW media messages
# Copyright (C) 2019 SCP-079 <https://scp-079.org>
#
# This file is part of SCP-079-NOPORN.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
import pickle
from configparser import RawConfigParser
from os import mkdir
from os.path import exists
from shutil import rmtree
from threading import Lock
from typing import Dict, List, Set, Union

# Enable logging
logger = logging.getLogger(__name__)

# Init

all_commands: List[str] = ["config", "noporn_config"]

declared_message_ids: Dict[str, Dict[int, Set[int]]] = {
    "ban": {},
    "delete": {}
}
# declared_message_ids = {
#     "ban": {
#         -10012345678: {123}
#     },
#     "delete": {
#         -10012345678: {124}
#     }
# }

default_config: Dict[str, Union[bool, int, Dict[str, bool]]] = {
    "default": True,
    "channel": True,
    "locked": 0,
    "recheck": False
}

default_user_status: Dict[str, Union[Dict[int, int], Dict[str, float]]] = {
    "nsfw": {},
    "score": {
        "captcha": 0,
        "lang": 0,
        "noflood": 0,
        "noporn": 0,
        "recheck": 0,
        "warn": 0
    }
}

file_ids: Set[str] = set()

left_group_ids: Set[int] = set()

lock_image: Lock = Lock()

receivers_bad: List[str] = ["APPEAL", "CAPTCHA", "LANG", "NOFLOOD", "NOPORN",
                            "NOSPAM", "MANAGE", "RECHECK", "USER", "WATCH"]

receivers_declare: List[str] = ["LANG", "NOFLOOD", "NOPORN", "NOSPAM", "RECHECK", "USER"]

receivers_status: List[str] = ["CAPTCHA", "LANG", "NOFLOOD", "NOPORN", "NOSPAM", "MANAGE", "RECHECK"]

version: str = "0.1.3"

watch_ids: Dict[str, Dict[int, int]] = {
    "ban": {},
    "delete": {}
}
# watch_ids = {
#     "ban": {
#         12345678: 0
#     },
#     "delete": {
#         12345678: 0
#     }
# }

# Read data from config.ini

# [basic]
bot_token: str = ""
prefix: List[str] = []
prefix_str: str = "/!"

# [bots]
captcha_id: int = 0
clean_id: int = 0
lang_id: int = 0
noflood_id: int = 0
noporn_id: int = 0
nospam_id: int = 0
user_id: int = 0
warn_id: int = 0

# [channels]
debug_channel_id: int = 0
exchange_channel_id: int = 0
logging_channel_id: int = 0
test_group_id: int = 0
logging_channel_username: str = ""

# [custom]
default_group_link: str = ""
project_link: str = ""
project_name: str = ""
punish_time: int = 0
reset_day: str = ""
threshold_porn: float = 0
user_name: str = ""

# [encrypt]
password: str = ""

try:
    config = RawConfigParser()
    config.read("config.ini")
    # [basic]
    bot_token = config["basic"].get("bot_token", bot_token)
    prefix = list(config["basic"].get("prefix", prefix_str))
    # [bots]
    captcha_id = int(config["bots"].get("captcha_id", captcha_id))
    clean_id = int(config["bots"].get("clean_id", clean_id))
    lang_id = int(config["bots"].get("lang_id", lang_id))
    noflood_id = int(config["bots"].get("noflood_id", noflood_id))
    noporn_id = int(config["bots"].get("noporn_id", noporn_id))
    nospam_id = int(config["bots"].get("nospam_id", nospam_id))
    user_id = int(config["bots"].get("user_id", user_id))
    warn_id = int(config["bots"].get("warn_id", warn_id))
    # [channels]
    debug_channel_id = int(config["channels"].get("debug_channel_id", debug_channel_id))
    exchange_channel_id = int(config["channels"].get("exchange_channel_id", exchange_channel_id))
    logging_channel_id = int(config["channels"].get("logging_channel_id", logging_channel_id))
    test_group_id = int(config["channels"].get("test_group_id", test_group_id))
    logging_channel_username = config["channels"].get("logging_channel_username", logging_channel_username)
    # [custom]
    default_group_link = config["custom"].get("default_group_link", default_group_link)
    project_link = config["custom"].get("project_link", project_link)
    project_name = config["custom"].get("project_name", project_name)
    punish_time = int(config["custom"].get("punish_time", punish_time))
    reset_day = config["custom"].get("reset_day", reset_day)
    threshold_porn = float(config["custom"].get("threshold_porn", threshold_porn))
    user_name = config["custom"].get("user_name", user_name)
    # [encrypt]
    password = config["encrypt"].get("password", password)
except Exception as e:
    logger.warning(f"Read data from config.ini error: {e}", exc_info=True)

# Check
if (bot_token in {"", "[DATA EXPUNGED]"}
        or prefix == []
        or captcha_id == 0
        or clean_id == 0
        or lang_id == 0
        or noflood_id == 0
        or noporn_id == 0
        or nospam_id == 0
        or user_id == 0
        or warn_id == 0
        or debug_channel_id == 0
        or exchange_channel_id == 0
        or logging_channel_id == 0
        or test_group_id == 0
        or logging_channel_username in {"", "[DATA EXPUNGED]"}
        or default_group_link in {"", "[DATA EXPUNGED]"}
        or project_link in {"", "[DATA EXPUNGED]"}
        or project_name in {"", "[DATA EXPUNGED]"}
        or punish_time == 0
        or reset_day in {"", "[DATA EXPUNGED]"}
        or threshold_porn == 0
        or user_name in {"", "[DATA EXPUNGED]"}
        or password in {"", "[DATA EXPUNGED]"}):
    raise SystemExit('No proper settings')

bot_ids: Set[int] = {captcha_id, clean_id, lang_id, noflood_id, noporn_id, nospam_id, user_id, warn_id}

# Load data from pickle

# Init dir
try:
    rmtree("tmp")
except Exception as e:
    logger.info(f"Remove tmp error: {e}")

for path in ["data", "tmp"]:
    if not exists(path):
        mkdir(path)

# Init ids variables

admin_ids: Dict[int, Set[int]] = {}
# admin_ids = {
#     -10012345678: {12345678}
# }

bad_ids: Dict[str, Set[int]] = {
    "channels": set(),
    "users": set()
}
# bad_ids = {
#     "channels": {-10012345678},
#     "users": {12345678}
# }

except_ids: Dict[str, Set[int]] = {
    "channels": set(),
    "users": set()
}
# except_ids = {
#     "channels": {-10012345678},
#     "users": {12345678}
# }

user_ids: Dict[int, Dict[str, Union[float, Dict[Union[int, str], Union[float, int]], Set[int]]]] = {}
# user_ids = {
#     12345678: {
#         "nsfw": {},
#         "score": {
#             "captcha": 0,
#             "lang": 0,
#             "noflood": 0,
#             "noporn": 0,
#             "recheck": 0,
#             "warn": 0
#         }
#     }
# }

# Init data variables

configs: Dict[int, Dict[str, Union[bool, int, Dict[str, bool]]]] = {}
# configs = {
#     -10012345678: {
#         "default": True,
#         "channel": True,
#         "locked": 0,
#         "recheck": False
# }

# Load data
file_list: List[str] = ["admin_ids", "bad_ids", "except_ids", "configs", "user_ids"]
for file in file_list:
    try:
        try:
            if exists(f"data/{file}") or exists(f"data/.{file}"):
                with open(f"data/{file}", 'rb') as f:
                    locals()[f"{file}"] = pickle.load(f)
            else:
                with open(f"data/{file}", 'wb') as f:
                    pickle.dump(eval(f"{file}"), f)
        except Exception as e:
            logger.error(f"Load data {file} error: {e}")
            with open(f"data/.{file}", 'rb') as f:
                locals()[f"{file}"] = pickle.load(f)
    except Exception as e:
        logger.critical(f"Load data {file} backup error: {e}")
        raise SystemExit("[DATA CORRUPTION]")

# Start program
copyright_text = (f"SCP-079-NOPORN v{version}, Copyright (C) 2019 SCP-079 <https://scp-079.org>\n"
                  "Licensed under the terms of the GNU General Public License v3 or later (GPLv3+)\n")
print(copyright_text)
