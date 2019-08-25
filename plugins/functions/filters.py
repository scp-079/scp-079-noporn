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
from copy import deepcopy
from time import time
from typing import Union

from pyrogram import Client, Filters, Message

from .. import glovar
from .channel import get_content
from .etc import get_text
from .file import delete_file, get_downloaded_path, save
from .ids import init_group_id
from .image import get_file_id, get_porn

# Enable logging
logger = logging.getLogger(__name__)


def is_class_c(_, message: Message) -> bool:
    # Check if the user who sent the message is Class C personnel
    try:
        if message.from_user:
            uid = message.from_user.id
            gid = message.chat.id
            if init_group_id(gid):
                if uid in glovar.admin_ids.get(gid, set()) or uid in glovar.bot_ids or message.from_user.is_self:
                    return True
    except Exception as e:
        logger.warning(f"Is class c error: {e}", exc_info=True)

    return False


def is_class_d(_, message: Message) -> bool:
    # Check if the user who sent the message is Class D personnel
    try:
        if message.from_user:
            uid = message.from_user.id
            if uid in glovar.bad_ids["users"]:
                return True

        if message.forward_from:
            fid = message.forward_from.id
            if fid in glovar.bad_ids["users"]:
                return True

        if message.forward_from_chat:
            cid = message.forward_from_chat.id
            if cid in glovar.bad_ids["channels"]:
                return True
    except Exception as e:
        logger.warning(f"Is class d error: {e}", exc_info=True)

    return False


def is_declared_message(_, message: Message) -> bool:
    # Check if the message is declared by other bots
    try:
        if isinstance(message, int):
            gid = _
            mid = message
        else:
            if message.chat:
                gid = message.chat.id
                mid = message.message_id
            else:
                return False

        if mid in glovar.declared_message_ids.get(gid, set()):
            return True
    except Exception as e:
        logger.warning(f"Is declared message error: {e}", exc_info=True)

    return False


def is_exchange_channel(_, message: Message) -> bool:
    # Check if the message is sent from the exchange channel
    try:
        if message.chat:
            cid = message.chat.id
            if glovar.should_hide:
                if cid == glovar.hide_channel_id:
                    return True
            elif cid == glovar.exchange_channel_id:
                return True
    except Exception as e:
        logger.warning(f"Is exchange channel error: {e}", exc_info=True)

    return False


def is_hide_channel(_, message: Message) -> bool:
    # Check if the message is sent from the hide channel
    try:
        if message.chat:
            cid = message.chat.id
            if cid == glovar.hide_channel_id:
                return True
    except Exception as e:
        logger.warning(f"Is hide channel error: {e}", exc_info=True)

    return False


def is_high_score_user(_, message: Message) -> Union[bool, float, int]:
    # Check if the message is sent by a high score user
    try:
        if message.from_user:
            uid = message.from_user.id
            user = glovar.user_ids.get(uid, {})
            if user:
                score = 0
                try:
                    user = glovar.user_ids.get(uid, {})
                    if user:
                        score = (user["score"].get("captcha", 0)
                                 + user["score"].get("clean", 0)
                                 + user["score"].get("lang", 0)
                                 + user["score"].get("long", 0)
                                 + user["score"].get("noflood", 0)
                                 + user["score"].get("noporn", 0)
                                 + user["score"].get("nospam", 0)
                                 + user["score"].get("recheck", 0)
                                 + user["score"].get("warn", 0))
                except Exception as e:
                    logger.warning(f"Get score error: {e}", exc_info=True)

                if score >= 3:
                    return score
    except Exception as e:
        logger.warning(f"Is high score user error: {e}", exc_info=True)

    return False


def is_new_group(_, message: Message) -> bool:
    # Check if the bot joined a new group
    try:
        if message.new_chat_members:
            new_users = message.new_chat_members
            if new_users:
                for user in new_users:
                    if user.is_self:
                        return True
        elif message.group_chat_created or message.supergroup_chat_created:
            return True
    except Exception as e:
        logger.warning(f"Is new group error: {e}", exc_info=True)

    return False


def is_nsfw_user(_, message: Message) -> bool:
    # Check if the message is sent by a NSFW user
    try:
        if message.from_user:
            gid = message.chat.id
            uid = message.from_user.id
            return is_nsfw_user_id(gid, uid)
    except Exception as e:
        logger.warning(f"Is NSFW user error: {e}", exc_info=True)

    return False


def is_nsfw_user_id(gid: int, uid: int) -> bool:
    # Check if the user_id is NSFW in the group
    try:
        user = glovar.user_ids.get(uid, {})
        if user:
            status = user["nsfw"].get(gid, 0)
            now = int(time())
            if now - status < glovar.punish_time:
                return True
    except Exception as e:
        logger.warning(f"Is NSFW user id error: {e}", exc_info=True)

    return False


def is_test_group(_, message: Message) -> bool:
    # Check if the message is sent from the test group
    try:
        if message.chat:
            cid = message.chat.id
            if cid == glovar.test_group_id:
                return True
    except Exception as e:
        logger.warning(f"Is test group error: {e}", exc_info=True)

    return False


def is_watch_ban(_, message: Message) -> bool:
    # Check if the message is sent by a watch ban user
    try:
        if message.from_user:
            uid = message.from_user.id
            now = int(time())
            until = glovar.watch_ids["ban"].get(uid, 0)
            if now < until:
                return True
    except Exception as e:
        logger.warning(f"Is watch ban error: {e}", exc_info=True)

    return False


def is_watch_delete(_, message: Message) -> bool:
    # Check if the message is sent by a watch delete user
    try:
        if message.from_user:
            uid = message.from_user.id
            now = int(time())
            until = glovar.watch_ids["delete"].get(uid, 0)
            if now < until:
                return True
    except Exception as e:
        logger.warning(f"Is watch delete error: {e}", exc_info=True)

    return False


class_c = Filters.create(
    name="Class C",
    func=is_class_c
)

class_d = Filters.create(
    name="Class D",
    func=is_class_d
)

declared_message = Filters.create(
    name="Declared message",
    func=is_declared_message
)

exchange_channel = Filters.create(
    name="Exchange Channel",
    func=is_exchange_channel
)

hide_channel = Filters.create(
    name="Hide Channel",
    func=is_hide_channel
)

high_score_user = Filters.create(
    name="High score user",
    func=is_high_score_user
)

new_group = Filters.create(
    name="New Group",
    func=is_new_group
)

nsfw_user = Filters.create(
    name="NSFW User",
    func=is_nsfw_user
)

test_group = Filters.create(
    name="Test Group",
    func=is_test_group
)

watch_ban = Filters.create(
    name="Watch Ban",
    func=is_watch_ban
)

watch_delete = Filters.create(
    name="Watch Delete",
    func=is_watch_delete
)


def is_class_e(message: Message):
    # Check if the message is Class E object
    try:
        content = get_content(None, message)
        if content:
            if (content in glovar.except_ids["long"]
                    or content in glovar.except_ids["temp"]
                    or content in glovar.file_ids["sfw"]):
                return True
    except Exception as e:
        logger.warning(f"Is class e error: {e}", exc_info=True)

    return False


def is_nsfw_media(client: Client, message: Union[str, Message]) -> bool:
    # Check if it is NSFW media, accept Message or file id
    need_delete = []
    if glovar.lock["image"].acquire():
        try:
            if isinstance(message, Message):
                target_user = is_nsfw_user(None, message)
                if target_user and (message.media or message.entities):
                    return True

                file_id = get_file_id(message)
                # If the file_id has been recorded as NSFW media
                if file_id in glovar.file_ids["nsfw"]:
                    return True

                image_path = get_downloaded_path(client, file_id)
            else:
                file_id = "PREVIEW"
                image_path = message

            if image_path:
                need_delete.append(image_path)
                porn = get_porn(image_path)
                if porn > glovar.threshold_porn:
                    glovar.file_ids["nsfw"].add(file_id)
                    return True
                else:
                    glovar.file_ids["sfw"].add(file_id)
        except Exception as e:
            logger.warning(f"Is NSFW media error: {e}", exc_info=True)
        finally:
            glovar.lock["image"].release()
            for file in need_delete:
                delete_file(file)

    return False


def is_nsfw_url(message: Message) -> bool:
    # Check if the message include NSFW url
    try:
        text = get_text(message)
        if text:
            url_list = deepcopy(glovar.url_list)
            for url in url_list:
                if url in text:
                    return True
    except Exception as e:
        logger.warning(f"Is NSFW url error: {e}", exc_info=True)

    return False


def is_restricted_channel(message: Message) -> bool:
    # Check if the message is forwarded form restricted channel
    try:
        if message.forward_from_chat:
            if message.forward_from_chat.restriction_reason:
                return True
    except Exception as e:
        logger.warning(f"Is restricted channel error: {e}", exc_info=True)

    return False


def is_regex_text(word_type: str, text: str) -> bool:
    # Check if the text hit the regex rules
    try:
        for word in list(eval(f"glovar.{word_type}_words")):
            if re.search(word, text, re.I | re.S | re.M):
                count = eval(f"glovar.{word_type}_words").get(word, 0)
                count += 1
                eval(f"glovar.{word_type}_words")[word] = count
                save(f"{word_type}_words")

                return True
    except Exception as e:
        logger.warning(f"Is regex text error: {e}", exc_info=True)

    return False
