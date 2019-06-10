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

from pyrogram import Client, Message

from .. import glovar
from .etc import crypt_str, thread
from .channel import ask_for_help, declare_message, forward_evidence, send_debug, share_bad_user
from .channel import share_watch_ban_user, update_score
from .file import save
from .group import delete_message
from .filters import is_high_score_user, is_nsfw_user, is_watch_ban, is_watch_delete
from .ids import init_user_id
from .telegram import kick_chat_member

# Enable logging
logger = logging.getLogger(__name__)


def add_bad_user(client: Client, uid: int) -> bool:
    # Add a bad user, share it
    try:
        glovar.bad_ids["users"].add(uid)
        save("bad_ids")
        share_bad_user(client, uid)
        return True
    except Exception as e:
        logger.warning(f"Add bad user error: {e}", exc_info=True)

    return False


def add_nsfw_user(gid: int, uid: int) -> bool:
    # Add or update a NSFW user status
    try:
        init_user_id(uid)
        now = int(time())
        previous = glovar.user_ids[uid]["nsfw"].get(gid)
        glovar.user_ids[uid]["nsfw"][gid] = now
        return bool(previous)
    except Exception as e:
        logger.warning(f"Add NSFW user error: {e}", exc_info=True)

    return False


def add_watch_ban_user(client: Client, uid: int) -> bool:
    # Add a watch ban user, share it
    try:
        now = int(time())
        until = now + glovar.time_ban
        glovar.watch_ids["ban"][uid] = until
        until = str(until)
        until = crypt_str("encrypt", until, glovar.key)
        share_watch_ban_user(client, uid, until)
        return True
    except Exception as e:
        logger.warning(f"Add watch ban user error: {e}", exc_info=True)

    return False


def ban_user(client: Client, gid: int, uid: int) -> bool:
    # Ban a user
    try:
        thread(kick_chat_member, (client, gid, uid))
        return True
    except Exception as e:
        logger.warning(f"Ban user error: {e}", exc_info=True)

    return False


def receive_watch_user(watch_type: str, uid: int, until: str) -> bool:
    # Receive watch users that other bots shared
    try:
        until = crypt_str("decrypt", until, glovar.key)
        until = int(until)
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


def terminate_nsfw_user(client: Client, message: Message, the_type: str) -> bool:
    # Delete NSFW user's message, or ban the user
    try:
        if message.from_user:
            gid = message.chat.id
            uid = message.from_user.id
            mid = message.message_id
            if is_watch_ban(None, message):
                result = forward_evidence(client, message, "自动封禁", "敏感追踪")
                if result:
                    ban_user(client, gid, uid)
                    delete_message(client, gid, mid)
                    declare_message(client, gid, mid)
                    ask_for_help(client, "ban", gid, uid)
                    add_bad_user(client, uid)
                    send_debug(client, message.chat, "追踪封禁", uid, mid, result)
            elif is_high_score_user(None, message):
                result = forward_evidence(client, message, "自动封禁", "用户评分", f"{is_high_score_user(None, message)}")
                if result:
                    ban_user(client, gid, uid)
                    delete_message(client, gid, mid)
                    declare_message(client, gid, mid)
                    ask_for_help(client, "ban", gid, uid)
                    add_bad_user(client, uid)
                    send_debug(client, message.chat, "评分封禁", uid, mid, result)
            elif is_watch_delete(None, message):
                result = forward_evidence(client, message, "自动删除", "敏感追踪")
                if result:
                    delete_message(client, gid, mid)
                    declare_message(client, gid, mid)
                    ask_for_help(client, "delete", gid, uid, "global")
                    add_watch_ban_user(client, uid)
                    previous = add_nsfw_user(gid, uid)
                    if not previous:
                        update_score(client, uid)

                    send_debug(client, message.chat, "追踪删除", uid, mid, result)
            elif is_nsfw_user(None, message):
                delete_message(client, gid, mid)
                add_nsfw_user(gid, uid)
                declare_message(client, gid, mid)
            else:
                if the_type == "channel":
                    rule = "受限频道"
                else:
                    rule = "全局规则"

                result = forward_evidence(client, message, "自动删除", rule)
                if result:
                    delete_message(client, gid, mid)
                    previous = add_nsfw_user(gid, uid)
                    declare_message(client, gid, mid)
                    if not previous:
                        update_score(client, uid)

                    send_debug(client, message.chat, "自动删除", uid, mid, result)

            return True
    except Exception as e:
        logger.warning(f"Terminate user error: {e}", exc_info=True)

    return False
