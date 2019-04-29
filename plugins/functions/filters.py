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
from time import time
from typing import Union

from pyrogram import Client, Filters, Message

from .. import glovar
from .ids import init_group_id
from .image import get_file_id, get_image_path, get_porn


# Enable logging
logger = logging.getLogger(__name__)


def is_class_c(_, message: Message) -> bool:
    try:
        uid = message.from_user.id
        gid = message.chat.id
        init_group_id(gid)
        if uid in glovar.admin_ids.get(gid, set()) or uid in glovar.bot_ids or message.from_user.is_self:
            return True
    except Exception as e:
        logger.warning(f"Is class c error: {e}", exc_info=True)

    return False


def is_class_d(_, message: Message) -> bool:
    try:
        uid = message.from_user.id
        if uid in glovar.bad_ids["users"]:
            return True

        if message.forward_from_chat:
            cid = message.forward_from_chat.id
            if cid in glovar.bad_ids["channels"]:
                return True
    except Exception as e:
        logger.warning(f"Is class d error: {e}", exc_info=True)


def is_class_e(_, message: Message) -> bool:
    try:
        uid = message.from_user.id
        if uid in glovar.except_ids["users"]:
            return True

        if message.forward_from_chat:
            cid = message.forward_from_chat.id
            if cid in glovar.except_ids["channels"]:
                return True
    except Exception as e:
        logger.warning(f"Is class e error: {e}", exc_info=True)

    return False


def is_declared_message(_, message: Message) -> bool:
    try:
        gid = message.chat.id
        mid = message.message_id
        if (mid == glovar.declared_message_ids["ban"].get(gid)
                or mid == glovar.declared_message_ids["delete"].get(gid)):
            return True
    except Exception as e:
        logger.warning(f"Is declared message error: {e}", exc_info=True)

    return False


def is_declared_ban_message(_, message: Message) -> bool:
    try:
        gid = message.chat.id
        mid = message.message_id
        return is_declared_ban_message_id(gid, mid)
    except Exception as e:
        logger.warning(f"Is declared ban message error: {e}", exc_info=True)

    return False


def is_declared_ban_message_id(gid: int, mid: int) -> bool:
    try:
        if mid == glovar.declared_message_ids["ban"].get(gid):
            return True
    except Exception as e:
        logger.warning(f"Is declared ban message id error: {e}", exc_info=True)

    return False


def is_declared_delete_message(_, message: Message) -> bool:
    try:
        gid = message.chat.id
        mid = message.message_id
        if mid == glovar.declared_message_ids["delete"].get(gid):
            return True
    except Exception as e:
        logger.warning(f"Is declared delete message error: {e}", exc_info=True)

    return False


def is_exchange_channel(_, message: Message) -> bool:
    try:
        cid = message.chat.id
        if cid == glovar.exchange_channel_id:
            return True
    except Exception as e:
        logger.warning(f"Is exchange channel error: {e}", exc_info=True)

    return False


def is_high_score_user(_, message: Message) -> bool:
    try:
        uid = message.from_user.id
        user = glovar.user_ids.get(uid, {})
        if user:
            score = user["score"]["lang"] + user["score"]["noflood"] + user["score"]["noporn"] + user["score"]["warn"]
            if score >= 3:
                return True
    except Exception as e:
        logger.warning(f"Is high score user error: {e}", exc_info=True)

    return False


def is_new_group(_, message: Message) -> bool:
    try:
        new_users = message.new_chat_members
        for user in new_users:
            if user.is_self:
                return True
    except Exception as e:
        logger.warning(f"Is new group error: {e}", exc_info=True)

    return False


def is_nsfw_user(_, message: Message) -> bool:
    try:
        gid = message.chat.id
        uid = message.from_user.id
        return is_nsfw_user_id(gid, uid)
    except Exception as e:
        logger.warning(f"Is NSFW user error: {e}", exc_info=True)

    return False


def is_nsfw_user_id(gid: int, uid: int) -> bool:
    try:
        user = glovar.user_ids.get(uid, {})
        if user:
            status = user["nsfw"].get(gid, 0)
            now = int(time())
            if now - status < 300:
                return True
    except Exception as e:
        logger.warning(f"Is NSFW user id error: {e}", exc_info=True)

    return False


def is_test_group(_, message: Message) -> bool:
    try:
        cid = message.chat.id
        if cid == glovar.test_group_id:
            return True
    except Exception as e:
        logger.warning(f"Is test group error: {e}", exc_info=True)

    return False


def is_watch_ban(_, message: Message) -> bool:
    try:
        uid = message.from_user.id
        status = glovar.watch_ids["ban"].get(uid, 0)
        now = int(time())
        if now - status < 14400:
            return True
    except Exception as e:
        logger.warning(f"Is watch ban error: {e}", exc_info=True)

    return False


def is_watch_delete(_, message: Message) -> bool:
    try:
        uid = message.from_user.id
        status = glovar.watch_ids["delete"].get(uid, 0)
        now = int(time())
        if now - status < 10800:
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

class_e = Filters.create(
    name="Class E",
    func=is_class_e
)

declared_message = Filters.create(
    name="Declared message",
    func=is_declared_message
)

declared_ban_message = Filters.create(
    name="Declared ban message",
    func=is_declared_ban_message
)

declared_delete_message = Filters.create(
    name="Declared delete message",
    func=is_declared_delete_message
)

exchange_channel = Filters.create(
    name="Exchange Channel",
    func=is_exchange_channel
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


def is_nsfw_media(client: Client, message: Union[str, Message]) -> bool:
    try:
        if isinstance(message, Message):
            target_user = is_nsfw_user(None, message)
            if target_user and (message.media or message.entities):
                return True

            file_id = get_file_id(message)
        else:
            file_id = message

        image_path = get_image_path(client, file_id)
        if image_path:
            porn = get_porn(image_path)
            if porn > 0.8:
                return True
    except Exception as e:
        logger.warning(f"Is NSFW media error: {e}", exc_info=True)

    return False
