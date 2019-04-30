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

from pyrogram import Client

from .. import glovar
from .etc import thread
from .channel import ask_for_help, declare_message, forward_evidence, send_debug, share_bad_user
from .channel import share_data, share_watch_ban_user
from .file import save
from .group import delete_message
from ..functions.filters import is_high_score_user, is_nsfw_user, is_watch_ban, is_watch_delete
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
        glovar.user_ids[uid]["nsfw"][gid] = now
        return True
    except Exception as e:
        logger.warning(f"Add NSFW user error: {e}", exc_info=True)

    return False


def add_watch_ban_user(client: Client, uid: int) -> bool:
    # Add a watch ban user, share it
    try:
        now = int(time())
        glovar.watch_ids["ban"][uid] = now
        share_watch_ban_user(client, uid)
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


def get_score(uid: int) -> float:
    # Get a user's total score
    score = 0
    try:
        user = glovar.user_ids.get(uid, {})
        if user:
            score = (user["score"].get("captcha", 0)
                     + user["score"].get("lang", 0)
                     + user["score"].get("noflood", 0)
                     + user["score"].get("noporn", 0)
                     + user["score"].get("noporn-recheck", 0)
                     + user["score"].get("warn", 0))
    except Exception as e:
        logger.warning(f"Get score error: {e}", exc_info=True)

    return score


def terminate_nsfw_user(client, message):
    # Delete NSFW user's message, or ban the user
    gid = message.chat.id
    uid = message.from_user.id
    mid = message.message_id
    if is_watch_ban(None, message):
        result = forward_evidence(client, message, "ban", "敏感追踪")
        if result:
            ban_user(client, gid, uid)
            delete_message(client, gid, mid)
            declare_message(client, "ban", gid, mid)
            ask_for_help(client, "ban", gid, uid)
            add_bad_user(client, uid)
            send_debug(client, message.chat, "追踪封禁", uid, mid, result)
    elif is_high_score_user(None, message):
        result = forward_evidence(client, message, "ban", f"用户评分 {get_score(uid)}")
        if result:
            ban_user(client, gid, uid)
            delete_message(client, gid, mid)
            declare_message(client, "ban", gid, mid)
            ask_for_help(client, "ban", gid, uid)
            add_bad_user(client, uid)
            send_debug(client, message.chat, "评分封禁", uid, mid, result)
    elif is_watch_delete(None, message):
        result = forward_evidence(client, message, "delete", "敏感追踪")
        if result:
            delete_message(client, gid, mid)
            declare_message(client, "delete", gid, mid)
            ask_for_help(client, "delete", gid, uid)
            add_watch_ban_user(client, uid)
            add_nsfw_user(gid, uid)
            update_score(client, uid)
            send_debug(client, message.chat, "追踪删除", uid, mid, result)
    elif is_nsfw_user(None, message):
        delete_message(client, gid, mid)
        add_nsfw_user(gid, uid)
        declare_message(client, "delete", gid, mid)
    else:
        result = forward_evidence(client, message, "delete", "全局规则")
        if result:
            delete_message(client, gid, mid)
            add_nsfw_user(gid, uid)
            declare_message(client, "delete", gid, mid)
            update_score(client, uid)
            send_debug(client, message.chat, "delete", uid, mid, result)


def update_score(client: Client, uid: int) -> bool:
    # Update a user's score, share it
    try:
        nsfw_count = len(glovar.user_ids[uid]["nsfw"])
        noporn_score = nsfw_count * 0.6
        glovar.user_ids[uid]["score"]["noporn"] = noporn_score
        save("user_ids")
        share_data(
            client=client,
            sender="NOPORN",
            receivers=["CAPTCHA", "LANG", "NOSPAM", "NOFLOOD"],
            action="update",
            action_type="score",
            data={
                "id": uid,
                "score": noporn_score
            }
        )
        return True
    except Exception as e:
        logger.warning(f"Update score error: {e}", exc_info=True)

    return False
