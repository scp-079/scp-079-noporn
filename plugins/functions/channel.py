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
from time import sleep
from typing import List, Optional, Union

from pyrogram import Chat, Client, Message
from pyrogram.errors import FloodWait

from .. import glovar
from .etc import code, general_link, format_data, thread, user_mention
from .file import crypt_file, save
from .telegram import get_group_info, send_document, send_message

# Enable logging
logger = logging.getLogger(__name__)


def ask_for_help(client: Client, level: str, gid: int, uid: int, group: str = "single") -> bool:
    # Let USER help to delete all message from user, or ban user globally
    try:
        data = {
                "group_id": gid,
                "user_id": uid
        }
        if level == "delete":
            data["type"] = group

        share_data(
            client=client,
            receivers=["USER"],
            action="help",
            action_type=level,
            data=data
        )
        return True
    except Exception as e:
        logger.warning(f"Ask for help error: {e}", exc_info=True)

    return False


def declare_message(client: Client, level: str, gid: int, mid: int) -> bool:
    # Declare a message
    try:
        glovar.declared_message_ids[level][gid].add(mid)
        share_data(
            client=client,
            receivers=glovar.receivers_declare,
            action="declare",
            action_type=level,
            data={
                "group_id": gid,
                "message_id": mid
            }
        )
        return True
    except Exception as e:
        logger.warning(f"Declare message error: {e}", exc_info=True)

    return False


def exchange_to_hide(client: Client) -> bool:
    # Let other bots exchange data in the hide channel instead
    try:
        glovar.should_hide = True
        text = format_data(
            sender="EMERGENCY",
            receivers=["EMERGENCY"],
            action="backup",
            action_type="hide",
            data=True
        )
        thread(send_message, (client, glovar.hide_channel_id, text))
        return True
    except Exception as e:
        logger.warning(f"Exchange to hide error: {e}", exc_info=True)

    return False


def forward_evidence(client: Client, message: Message, level: str, rule: str) -> Optional[Union[bool, int]]:
    # Forward the message to the logging channel as evidence
    result = None
    try:
        if not message or not message.from_user:
            return result

        uid = message.from_user.id
        flood_wait = True
        while flood_wait:
            flood_wait = False
            try:
                result = message.forward(glovar.logging_channel_id)
            except FloodWait as e:
                flood_wait = True
                sleep(e.x + 1)
            except Exception as e:
                logger.info(f"Forward evidence message error: {e}", exc_info=True)
                return False

        result = result.message_id
        text = (f"项目编号：{code(glovar.sender)}\n"
                f"用户 ID：{code(uid)}\n"
                f"操作等级：{code(level)}\n"
                f"规则：{code(rule)}\n")
        thread(send_message, (client, glovar.logging_channel_id, text, result))
    except Exception as e:
        logger.warning(f"Forward evidence error: {e}", exc_info=True)

    return result


def get_debug_text(client: Client, context: Union[int, Chat]) -> str:
    # Get a debug message text prefix, accept int or Chat
    if isinstance(context, int):
        info_para = context
        id_para = context
    else:
        info_para = context
        id_para = context.id

    group_name, group_link = get_group_info(client, info_para)
    text = (f"项目编号：{general_link(glovar.project_name, glovar.project_link)}\n"
            f"群组名称：{general_link(group_name, group_link)}\n"
            f"群组 ID：{code(id_para)}\n")

    return text


def send_debug(client: Client, chat: Chat, action: str, uid: int, mid: int, eid: int) -> bool:
    # Send the debug message
    text = get_debug_text(client, chat)
    text += (f"用户 ID：{user_mention(uid)}\n"
             f"执行操作：{code(action)}\n"
             f"触发消息：{general_link(mid, f'https://t.me/{glovar.logging_channel_username}/{eid}')}\n")
    thread(send_message, (client, glovar.debug_channel_id, text))

    return False


def share_bad_user(client: Client, uid: int) -> bool:
    # Share a bad user with other bots
    try:
        share_data(
            client=client,
            receivers=glovar.receivers_bad,
            action="add",
            action_type="bad",
            data={
                "id": uid,
                "type": "user"
            }
        )
        return True
    except Exception as e:
        logger.warning(f"Share bad user error: {e}", exc_info=True)

    return False


def share_data(client: Client, receivers: List[str], action: str, action_type: str, data: Union[dict, int, str],
               file: str = None) -> bool:
    # Use this function to share data in the exchange channel
    try:
        if glovar.sender in receivers:
            receivers.remove(glovar.sender)

        if glovar.should_hide:
            channel_id = glovar.hide_channel_id
        else:
            channel_id = glovar.exchange_channel_id

        if file:
            text = format_data(
                sender=glovar.sender,
                receivers=receivers,
                action=action,
                action_type=action_type,
                data=data
            )
            crypt_file("encrypt", f"data/{file}", f"tmp/{file}")
            result = send_document(client, channel_id, f"tmp/{file}", text)
        else:
            text = format_data(
                sender=glovar.sender,
                receivers=receivers,
                action=action,
                action_type=action_type,
                data=data
            )
            result = send_message(client, channel_id, text)

        if result is False:
            exchange_to_hide(client)
            thread(share_data, (client, receivers, action, action_type, data, file))

        return True
    except Exception as e:
        logger.warning(f"Share data error: {e}", exc_info=True)

    return False


def share_watch_ban_user(client: Client, uid: int, until: str) -> bool:
    # Share a watch ban user with other bots
    try:
        share_data(
            client=client,
            receivers=glovar.receivers_status,
            action="add",
            action_type="watch",
            data={
                "id": uid,
                "type": "ban",
                "until": until
            }
        )
        return True
    except Exception as e:
        logger.warning(f"Share watch ban user error: {e}", exc_info=True)


def update_score(client: Client, uid: int) -> bool:
    # Update a user's score, share it
    try:
        nsfw_count = len(glovar.user_ids[uid]["nsfw"])
        noporn_score = nsfw_count * 0.6
        glovar.user_ids[uid]["score"]["noporn"] = noporn_score
        save("user_ids")
        share_data(
            client=client,
            receivers=glovar.receivers_status,
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
