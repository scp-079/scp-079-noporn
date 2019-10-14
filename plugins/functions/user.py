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
from typing import Union

from pyrogram import ChatPermissions, Client, Message

from .. import glovar
from .etc import crypt_str, get_forward_name, get_full_name, get_now, lang, thread
from .channel import ask_for_help, declare_message, forward_evidence, send_debug, share_bad_user
from .channel import share_watch_user, update_score
from .file import save
from .group import delete_message
from .filters import is_class_d, is_declared_message, is_detected_user, is_high_score_user, is_limited_user
from .filters import is_new_user, is_promote_sticker, is_regex_text, is_watch_user
from .ids import init_user_id
from .telegram import kick_chat_member, restrict_chat_member

# Enable logging
logger = logging.getLogger(__name__)


def add_bad_user(client: Client, uid: int) -> bool:
    # Add a bad user, share it
    try:
        if uid in glovar.bad_ids["users"]:
            return True

        glovar.bad_ids["users"].add(uid)
        save("bad_ids")
        share_bad_user(client, uid)

        return True
    except Exception as e:
        logger.warning(f"Add bad user error: {e}", exc_info=True)

    return False


def add_detected_user(gid: int, uid: int, now: int) -> bool:
    # Add or update a detected user's status
    try:
        if not init_user_id(uid):
            return False

        previous = glovar.user_ids[uid]["detected"].get(gid)
        glovar.user_ids[uid]["detected"][gid] = now

        return bool(previous)
    except Exception as e:
        logger.warning(f"Add detected user error: {e}", exc_info=True)

    return False


def add_watch_user(client: Client, the_type: str, uid: int, now: int) -> bool:
    # Add a watch ban user, share it
    try:
        until = now + glovar.time_ban
        glovar.watch_ids[the_type][uid] = until
        until = str(until)
        until = crypt_str("encrypt", until, glovar.key)
        share_watch_user(client, the_type, uid, until)
        save("watch_ids")

        return True
    except Exception as e:
        logger.warning(f"Add watch user error: {e}", exc_info=True)

    return False


def ban_user(client: Client, gid: int, uid: Union[int, str]) -> bool:
    # Ban a user
    try:
        if glovar.configs[gid].get("restrict"):
            thread(restrict_chat_member, (client, gid, uid, ChatPermissions()))
        else:
            thread(kick_chat_member, (client, gid, uid))

        return True
    except Exception as e:
        logger.warning(f"Ban user error: {e}", exc_info=True)

    return False


def terminate_user(client: Client, message: Message, the_type: str) -> bool:
    # Delete user's message, or ban the user
    try:
        result = None

        # Check if it is necessary
        if is_class_d(None, message) or is_declared_message(None, message):
            return True

        gid = message.chat.id
        uid = message.from_user.id
        mid = message.message_id
        now = message.date or get_now()

        full_name = get_full_name(message.from_user, True)
        forward_name = get_forward_name(message, True)

        if ((is_regex_text("wb", full_name) or is_regex_text("wb", forward_name))
                and (full_name not in glovar.except_ids["long"] and forward_name not in glovar.except_ids["long"])):
            result = forward_evidence(
                client=client,
                message=message,
                level=lang("auto_ban"),
                rule=lang("name_examine")
            )
            if result:
                add_bad_user(client, uid)
                ban_user(client, gid, uid)
                delete_message(client, gid, mid)
                declare_message(client, gid, mid)
                ask_for_help(client, "ban", gid, uid)
                send_debug(
                    client=client,
                    chat=message.chat,
                    action=lang("name_ban"),
                    uid=uid,
                    mid=mid,
                    em=result
                )
        elif is_watch_user(message, "ban"):
            result = forward_evidence(
                client=client,
                message=message,
                level=lang("auto_ban"),
                rule=lang("watch_user")
            )
            if result:
                add_bad_user(client, uid)
                ban_user(client, gid, uid)
                delete_message(client, gid, mid)
                declare_message(client, gid, mid)
                ask_for_help(client, "ban", gid, uid)
                send_debug(
                    client=client,
                    chat=message.chat,
                    action=lang("watch_ban"),
                    uid=uid,
                    mid=mid,
                    em=result
                )
        elif is_high_score_user(message):
            score = is_high_score_user(message)
            result = forward_evidence(
                client=client,
                message=message,
                level=lang("auto_ban"),
                rule=lang("score_user"),
                score=score
            )
            if result:
                add_bad_user(client, uid)
                ban_user(client, gid, uid)
                delete_message(client, gid, mid)
                declare_message(client, gid, mid)
                ask_for_help(client, "ban", gid, uid)
                send_debug(
                    client=client,
                    chat=message.chat,
                    action=lang("score_ban"),
                    uid=uid,
                    mid=mid,
                    em=result
                )
        elif is_watch_user(message, "delete"):
            result = forward_evidence(
                client=client,
                message=message,
                level=lang("auto_delete"),
                rule=lang("watch_user")
            )
            if result:
                add_watch_user(client, "ban", uid, now)
                delete_message(client, gid, mid)
                declare_message(client, gid, mid)
                ask_for_help(client, "delete", gid, uid, "global")
                previous = add_detected_user(gid, uid, now)
                not previous and update_score(client, uid)
                send_debug(
                    client=client,
                    chat=message.chat,
                    action=lang("watch_delete"),
                    uid=uid,
                    mid=mid,
                    em=result
                )
        elif ((is_new_user(message.from_user, now) and is_promote_sticker(client, message))
              or is_new_user(message.from_user, now, gid)
              or is_limited_user(gid, message.from_user, now)):
            result = forward_evidence(
                client=client,
                message=message,
                level=lang("auto_delete"),
                rule=lang("watch_user"),
                more=lang("op_upgrade")
            )
            if result:
                add_watch_user(client, "ban", uid, now)
                delete_message(client, gid, mid)
                declare_message(client, gid, mid)
                ask_for_help(client, "delete", gid, uid, "global")
                previous = add_detected_user(gid, uid, now)
                not previous and update_score(client, uid)
                send_debug(
                    client=client,
                    chat=message.chat,
                    action=lang("watch_delete"),
                    uid=uid,
                    mid=mid,
                    em=result
                )
        elif is_detected_user(message) or uid in glovar.recorded_ids[gid] or the_type == "true":
            delete_message(client, gid, mid)
            add_detected_user(gid, uid, now)
            declare_message(client, gid, mid)
        else:
            if the_type == "channel":
                rule = lang("restricted_channel")
            else:
                rule = lang("rule_global")

            result = forward_evidence(
                client=client,
                message=message,
                level=lang("auto_delete"),
                rule=rule
            )
            if result:
                glovar.recorded_ids[gid].add(uid)
                delete_message(client, gid, mid)
                declare_message(client, gid, mid)
                previous = add_detected_user(gid, uid, now)
                not previous and update_score(client, uid)
                send_debug(
                    client=client,
                    chat=message.chat,
                    action=lang("auto_delete"),
                    uid=uid,
                    mid=mid,
                    em=result
                )

        return bool(result)
    except Exception as e:
        logger.warning(f"Terminate user error: {e}", exc_info=True)

    return False
