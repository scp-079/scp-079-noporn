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
from typing import Union

from pyrogram import Client, Filters, Message

from .. import glovar
from .channel import get_content
from .etc import get_now, get_links
from .file import delete_file, get_downloaded_path, save
from .ids import init_group_id
from .image import get_file_id, get_porn

# Enable logging
logger = logging.getLogger(__name__)


def is_class_c(_, message: Message) -> bool:
    # Check if the message is Class C object
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
    # Check if the message is Class D object
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


def is_class_e(_, message: Message) -> bool:
    # Check if the message is Class E object
    try:
        content = get_content(None, message)
        if content:
            if (content in glovar.except_ids["long"]
                    or content in glovar.except_ids["temp"]
                    or glovar.contents.get(content, "") == "sfw"):
                return True
    except Exception as e:
        logger.warning(f"Is class e error: {e}", exc_info=True)

    return False


def is_declared_message(_, message: Message) -> bool:
    # Check if the message is declared by other bots
    try:
        if message.chat:
            gid = message.chat.id
            mid = message.message_id
            return is_declared_message_id(gid, mid)
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


class_c = Filters.create(
    func=is_class_c,
    name="Class C"
)

class_d = Filters.create(
    func=is_class_d,
    name="Class D"
)

class_e = Filters.create(
    func=is_class_e,
    name="Class E"
)

declared_message = Filters.create(
    func=is_declared_message,
    name="Declared message"
)

exchange_channel = Filters.create(
    func=is_exchange_channel,
    name="Exchange Channel"
)

hide_channel = Filters.create(
    func=is_hide_channel,
    name="Hide Channel"
)

new_group = Filters.create(
    func=is_new_group,
    name="New Group"
)

test_group = Filters.create(
    func=is_test_group,
    name="Test Group"
)


def is_declared_message_id(gid: int, mid: int) -> bool:
    # Check if the message's ID is declared by other bots
    try:
        if mid in glovar.declared_message_ids.get(gid, set()):
            return True
    except Exception as e:
        logger.warning(f"Is declared message id error: {e}", exc_info=True)

    return False


def is_detected_user(message: Message) -> bool:
    # Check if the message is sent by a detected user
    try:
        if message.from_user:
            gid = message.chat.id
            uid = message.from_user.id
            return is_detected_user_id(gid, uid)
    except Exception as e:
        logger.warning(f"Is detected user error: {e}", exc_info=True)

    return False


def is_detected_user_id(gid: int, uid: int) -> bool:
    # Check if the user_id is detected in the group
    try:
        user = glovar.user_ids.get(uid, {})
        if user:
            status = user["detected"].get(gid, 0)
            now = get_now()
            if now - status < glovar.punish_time:
                return True
    except Exception as e:
        logger.warning(f"Is detected user id error: {e}", exc_info=True)

    return False


def is_high_score_user(message: Message) -> Union[bool, float]:
    # Check if the message is sent by a high score user
    try:
        if message.from_user:
            uid = message.from_user.id
            user = glovar.user_ids.get(uid, {})
            if user:
                score = 0.0
                try:
                    user = glovar.user_ids.get(uid, {})
                    if user:
                        score = (user["score"].get("captcha", 0.0)
                                 + user["score"].get("clean", 0.0)
                                 + user["score"].get("lang", 0.0)
                                 + user["score"].get("long", 0.0)
                                 + user["score"].get("noflood", 0.0)
                                 + user["score"].get("noporn", 0.0)
                                 + user["score"].get("nospam", 0.0)
                                 + user["score"].get("recheck", 0.0)
                                 + user["score"].get("warn", 0.0))
                except Exception as e:
                    logger.warning(f"Get score error: {e}", exc_info=True)

                if score >= 3.0:
                    return score
    except Exception as e:
        logger.warning(f"Is high score user error: {e}", exc_info=True)

    return False


def is_nsfw_media(client: Client, message: Union[str, Message]) -> bool:
    # Check if it is NSFW media, accept Message or file id
    need_delete = []
    if glovar.lock["image"].acquire():
        try:
            if isinstance(message, Message):
                if is_detected_user(message) and (message.media or message.entities):
                    return True

                # If the message has been recorded as NSFW
                content = get_content(client, message)
                if content:
                    if glovar.contents.get(content, "") == "nsfw":
                        return True

                file_id = get_file_id(message)
                image_path = get_downloaded_path(client, file_id)
                if is_declared_message(None, message):
                    return False
            else:
                file_id = "PREVIEW"
                image_path = message

            if image_path:
                need_delete.append(image_path)
                porn = get_porn(image_path)
                if porn > glovar.threshold_porn:
                    if file_id != "PREVIEW":
                        glovar.contents[file_id] = "nsfw"

                    return True
                else:
                    if file_id != "PREVIEW":
                        glovar.contents[file_id] = "sfw"
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
        links = get_links(message)
        for link in links:
            if glovar.contents.get(link, "") == "nsfw":
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


def is_watch_ban(message: Message) -> bool:
    # Check if the message is sent by a watch ban user
    try:
        if message.from_user:
            uid = message.from_user.id
            now = get_now()
            until = glovar.watch_ids["ban"].get(uid, 0)
            if now < until:
                return True
    except Exception as e:
        logger.warning(f"Is watch ban error: {e}", exc_info=True)

    return False


def is_watch_delete(message: Message) -> bool:
    # Check if the message is sent by a watch delete user
    try:
        if message.from_user:
            uid = message.from_user.id
            now = get_now()
            until = glovar.watch_ids["delete"].get(uid, 0)
            if now < until:
                return True
    except Exception as e:
        logger.warning(f"Is watch delete error: {e}", exc_info=True)

    return False
