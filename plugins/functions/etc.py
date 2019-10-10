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
import re
from hashlib import md5
from html import escape
from json import dumps
from random import choice, uniform
from string import ascii_letters, digits
from threading import Thread, Timer
from time import sleep, time
from typing import Any, Callable, Dict, List, Optional, Union
from unicodedata import normalize

from cryptography.fernet import Fernet
from opencc import convert
from pyrogram import InlineKeyboardMarkup, Message, MessageEntity, User
from pyrogram.errors import FloodWait

from .. import glovar

# Enable logging
logger = logging.getLogger(__name__)


def bold(text: Any) -> str:
    # Get a bold text
    try:
        text = str(text)
        if text.strip():
            return f"<b>{escape(str(text))}</b>"
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


def code(text: Any) -> str:
    # Get a code text
    try:
        text = str(text)
        if text.strip():
            return f"<code>{escape(str(text))}</code>"
    except Exception as e:
        logger.warning(f"Code error: {e}", exc_info=True)

    return ""


def code_block(text: Any) -> str:
    # Get a code block text
    try:
        text = str(text)
        if text.strip():
            return f"<pre>{escape(str(text))}</pre>"
    except Exception as e:
        logger.warning(f"Code block error: {e}", exc_info=True)

    return ""


def crypt_str(operation: str, text: str, key: str) -> str:
    # Encrypt or decrypt a string
    result = ""
    try:
        f = Fernet(key)
        text = text.encode("utf-8")
        if operation == "decrypt":
            result = f.decrypt(text)
        else:
            result = f.encrypt(text)

        result = result.decode("utf-8")
    except Exception as e:
        logger.warning(f"Crypt str error: {e}", exc_info=True)

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


def general_link(text: Union[int, str], link: str) -> str:
    # Get a general markdown link
    result = ""
    try:
        result = f'<a href="{link}">{escape(str(text))}</a>'
    except Exception as e:
        logger.warning(f"General link error: {e}", exc_info=True)

    return result


def get_channel_link(message: Union[int, Message]) -> str:
    # Get a channel reference link
    text = ""
    try:
        text = "https://t.me/"
        if isinstance(message, int):
            text += f"c/{str(message)[4:]}"
        else:
            if message.chat.username:
                text += f"{message.chat.username}"
            else:
                cid = message.chat.id
                text += f"c/{str(cid)[4:]}"
    except Exception as e:
        logger.warning(f"Get channel link error: {e}", exc_info=True)

    return text


def get_command_context(message: Message) -> (str, str):
    # Get the type "a" and the context "b" in "/command a b"
    command_type = ""
    command_context = ""
    try:
        text = get_text(message)
        command_list = text.split(" ")
        if len(list(filter(None, command_list))) > 1:
            i = 1
            command_type = command_list[i]
            while command_type == "" and i < len(command_list):
                i += 1
                command_type = command_list[i]

            command_context = text[1 + len(command_list[0]) + i + len(command_type):].strip()
    except Exception as e:
        logger.warning(f"Get command context error: {e}", exc_info=True)

    return command_type, command_context


def get_command_type(message: Message) -> str:
    # Get the command type "a" in "/command a"
    result = ""
    try:
        text = get_text(message)
        command_list = list(filter(None, text.split(" ")))
        result = text[len(command_list[0]):].strip()
    except Exception as e:
        logger.warning(f"Get command type error: {e}", exc_info=True)

    return result


def get_config_text(config: dict) -> str:
    # Get config text
    result = ""
    try:
        # Basic
        default_text = (lambda x: lang("default") if x else lang("custom"))(config.get("default"))
        delete_text = (lambda x: lang("enabled") if x else lang("disabled"))(config.get("delete"))
        result += (f"{lang('config')}{lang('colon')}{code(default_text)}\n"
                   f"{lang('delete')}{lang('colon')}{code(delete_text)}\n")

        # Restricted Channel
        channel_text = (lambda x: lang("enabled") if x else lang("disabled"))(config.get("channel"))
        result += f"{lang('noporn_channel')}{lang('colon')}{code(channel_text)}\n"
    except Exception as e:
        logger.warning(f"Get config text error: {e}", exc_info=True)

    return result


def get_entity_text(message: Message, entity: MessageEntity) -> str:
    # Get a message's entity text
    result = ""
    try:
        text = get_text(message)
        if text and entity:
            offset = entity.offset
            length = entity.length
            text = text.encode("utf-16-le")
            result = text[offset * 2:(offset + length) * 2].decode("utf-16-le")
    except Exception as e:
        logger.warning(f"Get entity text error: {e}", exc_info=True)

    return result


def get_filename(message: Message, normal: bool = False) -> str:
    # Get file's filename
    text = ""
    try:
        if message.document:
            if message.document.file_name:
                text += message.document.file_name
        elif message.audio:
            if message.audio.file_name:
                text += message.audio.file_name

        if text:
            text = t2t(text, normal)
    except Exception as e:
        logger.warning(f"Get filename error: {e}", exc_info=True)

    return text


def get_forward_name(message: Message, normal: bool = False) -> str:
    # Get forwarded message's origin sender's name
    text = ""
    try:
        if message.forward_from:
            user = message.forward_from
            text = get_full_name(user, normal)
        elif message.forward_sender_name:
            text = message.forward_sender_name
        elif message.forward_from_chat:
            chat = message.forward_from_chat
            text = chat.title

        if text:
            text = t2t(text, normal)
    except Exception as e:
        logger.warning(f"Get forward name error: {e}", exc_info=True)

    return text


def get_full_name(user: User, normal: bool = False) -> str:
    # Get user's full name
    text = ""
    try:
        if user and not user.is_deleted:
            text = user.first_name
            if user.last_name:
                text += f" {user.last_name}"

        if text:
            text = t2t(text, normal)
    except Exception as e:
        logger.warning(f"Get full name error: {e}", exc_info=True)

    return text


def get_int(text: str) -> Optional[int]:
    # Get a int from a string
    result = None
    try:
        result = int(text)
    except Exception as e:
        logger.info(f"Get int error: {e}", exc_info=True)

    return result


def get_links(message: Message) -> List[str]:
    # Get a message's links
    result = []
    try:
        entities = message.entities or message.caption_entities
        if entities:
            for en in entities:
                link = ""
                if en.type == "url":
                    link = get_entity_text(message, en)
                elif en.url:
                    link = en.url

                link = get_stripped_link(link)
                if link:
                    result.append(link)

        if message.reply_markup and isinstance(message.reply_markup, InlineKeyboardMarkup):
            reply_markup = message.reply_markup
            if reply_markup.inline_keyboard:
                inline_keyboard = reply_markup.inline_keyboard
                if inline_keyboard:
                    for button_row in inline_keyboard:
                        for button in button_row:
                            if button:
                                if button.url:
                                    url = get_stripped_link(button.url)
                                    if url:
                                        result.append(get_stripped_link(url))
    except Exception as e:
        logger.warning(f"Get links error: {e}", exc_info=True)

    return result


def get_md5sum(the_type: str, ctx: str) -> str:
    # Get the md5sum of a string or file
    result = ""
    try:
        if not ctx.strip():
            return ""

        if the_type == "file":
            hash_md5 = md5()
            with open(ctx, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)

            result = hash_md5.hexdigest()
        elif the_type == "string":
            result = md5(ctx.encode()).hexdigest()
    except Exception as e:
        logger.warning(f"Get md5sum error: {e}", exc_info=True)

    return result


def get_now() -> int:
    # Get time for now
    result = 0
    try:
        result = int(time())
    except Exception as e:
        logger.warning(f"Get now error: {e}", exc_info=True)

    return result


def get_report_record(message: Message) -> Dict[str, str]:
    # Get report message's full record
    record = {
        "project": "",
        "origin": "",
        "status": "",
        "uid": "",
        "level": "",
        "rule": "",
        "type": "",
        "game": "",
        "lang": "",
        "length": "",
        "freq": "",
        "score": "",
        "bio": "",
        "name": "",
        "from": "",
        "more": "",
        "unknown": ""
    }
    try:
        if not message.text:
            return record

        record_list = message.text.split("\n")
        for r in record_list:
            if re.search(f"^{lang('project')}{lang('colon')}", r):
                record_type = "project"
            elif re.search(f"^{lang('project_origin')}{lang('colon')}", r):
                record_type = "origin"
            elif re.search(f"^{lang('status')}{lang('colon')}", r):
                record_type = "status"
            elif re.search(f"^{lang('user_id')}{lang('colon')}", r):
                record_type = "uid"
            elif re.search(f"^{lang('level')}{lang('colon')}", r):
                record_type = "level"
            elif re.search(f"^{lang('rule')}{lang('colon')}", r):
                record_type = "rule"
            elif re.search(f"^{lang('message_type')}{lang('colon')}", r):
                record_type = "type"
            elif re.search(f"^{lang('message_game')}{lang('colon')}", r):
                record_type = "game"
            elif re.search(f"^{lang('message_lang')}{lang('colon')}", r):
                record_type = "lang"
            elif re.search(f"^{lang('message_len')}{lang('colon')}", r):
                record_type = "length"
            elif re.search(f"^{lang('message_freq')}{lang('colon')}", r):
                record_type = "freq"
            elif re.search(f"^{lang('user_score')}{lang('colon')}", r):
                record_type = "score"
            elif re.search(f"^{lang('user_bio')}{lang('colon')}", r):
                record_type = "bio"
            elif re.search(f"^{lang('user_name')}{lang('colon')}", r):
                record_type = "name"
            elif re.search(f"^{lang('from_name')}{lang('colon')}", r):
                record_type = "from"
            elif re.search(f"^{lang('more')}{lang('colon')}", r):
                record_type = "more"
            else:
                record_type = "unknown"

            record[record_type] = r.split(f"{lang('colon')}")[-1]
    except Exception as e:
        logger.warning(f"Get report record error: {e}", exc_info=True)

    return record


def get_stripped_link(link: str) -> str:
    # Get stripped link
    result = ""
    try:
        if not link.strip():
            return ""

        result = link.replace("http://", "")
        result = result.replace("https://", "")
        if result and result[-1] == "/":
            result = result[:-1]
    except Exception as e:
        logger.warning(f"Get stripped link error: {e}", exc_info=True)

    return result


def get_text(message: Message, normal: bool = False) -> str:
    # Get message's text, including link and mentioned user's name
    text = ""
    try:
        if not message:
            return ""

        the_text = message.text or message.caption
        if the_text:
            text += the_text
            entities = message.entities or message.caption_entities
            if entities:
                for en in entities:
                    if en.url:
                        text += f"\n{en.url}"

        if message.reply_markup and isinstance(message.reply_markup, InlineKeyboardMarkup):
            reply_markup = message.reply_markup
            if reply_markup.inline_keyboard:
                inline_keyboard = reply_markup.inline_keyboard
                if inline_keyboard:
                    for button_row in inline_keyboard:
                        for button in button_row:
                            if button:
                                if button.text:
                                    text += f"\n{button.text}"

                                if button.url:
                                    text += f"\n{button.url}"

        if text:
            text = t2t(text, normal)
    except Exception as e:
        logger.warning(f"Get text error: {e}", exc_info=True)

    return text


def lang(text: str) -> str:
    # Get the text
    result = ""
    try:
        result = glovar.lang.get(text, text)
    except Exception as e:
        logger.warning(f"Lang error: {e}", exc_info=True)

    return result


def message_link(message: Message) -> str:
    # Get a message link in a channel
    text = ""
    try:
        mid = message.message_id
        text = f"{get_channel_link(message)}/{mid}"
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


def t2t(text: str, normal: bool, printable: bool = True) -> str:
    # Convert the string, text to text
    try:
        if not text:
            return ""

        if normal:
            for special in ["spc", "spe"]:
                text = "".join(eval(f"glovar.{special}_dict").get(t, t) for t in text)

            text = normalize("NFKC", text)

        if printable:
            text = "".join(t for t in text if t.isprintable() or t in {"\n", "\r", "\t"})

        if glovar.zh_cn:
            text = convert(text, config="t2s.json")
    except Exception as e:
        logger.warning(f"T2T error: {e}", exc_info=True)

    return text


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
        text = general_link(f"{uid}", f"tg://user?id={uid}")
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
