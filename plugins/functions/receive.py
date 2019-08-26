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
from json import loads
from typing import Any

from pyrogram import Client, InlineKeyboardButton, InlineKeyboardMarkup, Message

from .. import glovar
from .etc import code, crypt_str, get_text, thread
from .etc import user_mention
from .file import crypt_file, delete_file, get_new_path, get_downloaded_path, save
from .filters import is_declared_message, is_nsfw_media, is_nsfw_user_id
from .group import get_message
from .ids import init_group_id, init_user_id
from .telegram import send_report_message
from .user import terminate_nsfw_user

# Enable logging
logger = logging.getLogger(__name__)


def receive_bad_user(data: dict) -> bool:
    # Receive bad users that other bots shared
    try:
        uid = data["id"]
        bad_type = data["type"]
        if bad_type == "user":
            glovar.bad_ids["users"].add(uid)
            save("bad_ids")
            return True
    except Exception as e:
        logger.warning(f"Receive bad user error: {e}", exc_info=True)

    return False


def receive_config_commit(data: dict) -> bool:
    # Receive config commit
    try:
        gid = data["group_id"]
        config = data["config"]
        glovar.configs[gid] = config
        save("configs")

        return True
    except Exception as e:
        logger.warning(f"Receive config commit error: {e}", exc_info=True)

    return False


def receive_config_reply(client: Client, data: dict) -> bool:
    # Receive config reply
    try:
        gid = data["group_id"]
        uid = data["user_id"]
        link = data["config_link"]
        text = (f"管理员：{user_mention(uid)}\n"
                f"操作：{code('更改设置')}\n"
                f"说明：{code('请点击下方按钮进行设置')}")
        markup = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "前往设置",
                        url=link
                    )
                ]
            ]
        )
        thread(send_report_message, (180, client, gid, text, None, markup))

        return True
    except Exception as e:
        logger.warning(f"Receive config reply error: {e}", exc_info=True)

    return False


def receive_file_data(client: Client, message: Message, decrypt: bool = False) -> Any:
    # Receive file's data from exchange channel
    data = None
    try:
        if message.document:
            file_id = message.document.file_id
            path = get_downloaded_path(client, file_id)
            if path:
                if decrypt:
                    # Decrypt the file, save to the tmp directory
                    path_decrypted = get_new_path()
                    crypt_file("decrypt", path, path_decrypted)
                    path_final = path_decrypted
                else:
                    # Read the file directly
                    path_decrypted = ""
                    path_final = path

                with open(path_final, "rb") as f:
                    data = pickle.load(f)

                thread(delete_file, (path,))
                thread(delete_file, (path_decrypted,))
    except Exception as e:
        logger.warning(f"Receive file error: {e}", exc_info=True)

    return data


def receive_preview(client: Client, message: Message, data: dict) -> bool:
    # Receive message's preview
    try:
        gid = data["group_id"]
        if glovar.admin_ids.get(gid):
            uid = data["user_id"]
            mid = data["message_id"]
            preview = receive_file_data(client, message)
            if preview:
                image = preview["image"]
                if image:
                    image_path = get_new_path()
                    image.save(image_path, "PNG")
                    if (not is_declared_message(gid, mid)
                            and not is_nsfw_user_id(gid, uid)):
                        if is_nsfw_media(client, image_path):
                            url = preview["url"]
                            glovar.url_list.add(url)
                            the_message = get_message(client, gid, mid)
                            if the_message:
                                terminate_nsfw_user(client, the_message, "media")

        return True
    except Exception as e:
        logger.warning(f"Receive preview error: {e}", exc_info=True)

    return False


def receive_text_data(message: Message) -> dict:
    # Receive text's data from exchange channel
    data = {}
    try:
        text = get_text(message)
        if text:
            data = loads(text)
    except Exception as e:
        logger.warning(f"Receive data error: {e}")

    return data


def receive_declared_message(data: dict) -> bool:
    # Update declared message's id
    try:
        gid = data["group_id"]
        mid = data["message_id"]
        if glovar.admin_ids.get(gid):
            if init_group_id(gid):
                glovar.declared_message_ids[gid].add(mid)
                return True
    except Exception as e:
        logger.warning(f"Update declared id error: {e}", exc_info=True)

    return False


def receive_user_score(project: str, data: dict) -> bool:
    # Receive and update user's score
    try:
        project = project.lower()
        uid = data["id"]
        init_user_id(uid)
        score = data["score"]
        glovar.user_ids[uid][project] = score
        save("user_ids")

        return True
    except Exception as e:
        logger.warning(f"Receive user score error: {e}", exc_info=True)

    return False


def receive_watch_user(data: dict) -> bool:
    # Receive watch users that other bots shared
    try:
        watch_type = data["type"]
        uid = data["id"]
        until = data["until"]

        # Decrypt the data
        until = crypt_str("decrypt", until, glovar.key)
        until = int(until)

        # Add to list
        if watch_type == "ban":
            glovar.watch_ids["ban"][uid] = until
        elif watch_type == "delete":
            glovar.watch_ids["delete"][uid] = until
        else:
            return False

        return True
    except Exception as e:
        logger.warning(f"Receive watch user error: {e}", exc_info=True)

    return False
