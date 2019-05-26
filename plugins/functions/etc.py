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
from json import dumps, loads
from random import choice, uniform
from string import ascii_letters, digits
from threading import Thread, Timer
from time import sleep
from typing import Callable, List, Optional, Union

from cryptography.fernet import Fernet
from pyrogram import Message
from pyrogram.errors import FloodWait

# Enable logging
logger = logging.getLogger(__name__)


def bold(text) -> str:
    # Get a bold text
    try:
        text = str(text)
        if text.strip():
            return f"**{text}**"
    except Exception as e:
        logger.warning(f"Bold error: {e}", exc_info=True)

    return ""


def button_data(action: str, action_type: str = None, data: Union[int, str] = None) -> Optional[bytes]:
    # Get a button's bytes data
    result = None
    try:
        button = {
            "a": action,
            "t": action_type,
            "d": data
        }
        result = dumps(button).replace(" ", "").encode("utf-8")
    except Exception as e:
        logger.warning(f"Button data error: {e}", exc_info=True)

    return result


def code(text) -> str:
    # Get a code text
    try:
        text = str(text)
        if text.strip():
            return f"`{text}`"
    except Exception as e:
        logger.warning(f"Code error: {e}", exc_info=True)

    return ""


def code_block(text) -> str:
    # Get a code block text
    try:
        text = str(text)
        if text.strip():
            return f"```{text}```"
    except Exception as e:
        logger.warning(f"Code block error: {e}", exc_info=True)

    return ""


def crypt_str(operation: str, text: str, key: str) -> str:
    # Encrypt or decrypt a string
    f = Fernet(key)
    text = text.encode("utf-8")
    if operation == "decrypt":
        result = f.decrypt(text)
    else:
        result = f.encrypt(text)

    result = result.decode("utf-8")

    return result


def delay(secs: int, target: Callable, args: list) -> bool:
    # Call a function with delay
    try:
        t = Timer(secs, target, args)
        t.daemon = True
        t.start()
        return True
    except Exception as e:
        logger.warning(f"Delay error: {e}", exc_info=True)

    return False


def format_data(sender: str, receivers: List[str], action: str, action_type: str, data=None) -> str:
    # See https://scp-079.org/exchange/
    text = ""
    try:
        data = {
            "from": sender,
            "to": receivers,
            "action": action,
            "type": action_type,
            "data": data
        }
        text = code_block(dumps(data, indent=4))
    except Exception as e:
        logger.warning(f"Format data error: {e}", exc_info=True)

    return text


def general_link(text: Union[int, str], link: str) -> str:
    # Get a general markdown link
    result = ""
    try:
        result = f"[{text}]({link})"
    except Exception as e:
        logger.warning(f"General link error: {e}", exc_info=True)

    return result


def get_command_context(message: Message) -> str:
    # Get the context "b" in "/command a b"
    result = ""
    try:
        text = get_text(message)
        command_list = text.split(" ")
        if len(list(filter(None, command_list))) > 2:
            i = 1
            command_type = command_list[i]
            while command_type == "" and i < len(command_list):
                i += 1
                command_type = command_list[i]

            result = text[1 + len(command_list[0]) + i + len(command_type):].strip()
    except Exception as e:
        logger.warning(f"Get command context error: {e}", exc_info=True)

    return result


def get_text(message: Message) -> str:
    # Get message's text
    text = ""
    try:
        if message.text or message.caption:
            if message.text:
                text += message.text
            else:
                text += message.caption
    except Exception as e:
        logger.warning(f"Get text error: {e}", exc_info=True)

    return text


def message_link(cid: int, mid: int) -> str:
    # Get a message link in a channel
    text = ""
    try:
        text = f"[{mid}](https://t.me/c/{str(cid)[4:]}/{mid})"
    except Exception as e:
        logger.warning(f"Message link error: {e}", exc_info=True)

    return text


def random_str(i: int) -> str:
    # Get a random string
    text = ""
    try:
        text = "".join(choice(ascii_letters + digits) for _ in range(i))
    except Exception as e:
        logger.warning(f"Random str error: {e}", exc_info=True)

    return text


def receive_data(message: Message) -> dict:
    # Receive data from exchange channel
    data = {}
    try:
        text = get_text(message)
        if text:
            data = loads(text)
    except Exception as e:
        logger.warning(f"Receive data error: {e}")

    return data


def thread(target: Callable, args: tuple) -> bool:
    # Call a function using thread
    try:
        t = Thread(target=target, args=args)
        t.daemon = True
        t.start()
        return True
    except Exception as e:
        logger.warning(f"Thread error: {e}", exc_info=True)

    return False


def user_mention(uid: int) -> str:
    # Get a mention text
    text = ""
    try:
        text = f"[{uid}](tg://user?id={uid})"
    except Exception as e:
        logger.warning(f"User mention error: {e}", exc_info=True)

    return text


def wait_flood(e: FloodWait) -> bool:
    # Wait flood secs
    try:
        sleep(e.x + uniform(0.5, 1.0))
        return True
    except Exception as e:
        logger.warning(f"Wait flood error: {e}", exc_info=True)

    return False
