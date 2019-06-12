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
from json import dumps, loads
from time import sleep
from typing import Any, List, Optional, Union

from pyrogram import Chat, Client, Message
from pyrogram.errors import FloodWait

from .. import glovar
from .etc import code, code_block, general_link, get_text, message_link, thread
from .file import crypt_file, delete_file, get_new_path, get_downloaded_path, save
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


def declare_message(client: Client, gid: int, mid: int) -> bool:
    # Declare a message
    try:
        glovar.declared_message_ids[gid].add(mid)
        share_data(
            client=client,
            receivers=glovar.receivers_declare,
            action="update",
            action_type="declare",
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


def forward_evidence(client: Client, message: Message, level: str, rule: str,
                     more: str = None) -> Optional[Union[bool, Message]]:
    # Forward the message to the logging channel as evidence
    result = None
    try:
        uid = message.from_user.id
        text = (f"项目编号：{code(glovar.sender)}\n"
                f"用户 ID：{code(uid)}\n"
                f"操作等级：{code(level)}\n"
                f"规则：{code(rule)}\n")
        if more:
            text += f"附加信息：{code(more)}\n"

        flood_wait = True
        while flood_wait:
            flood_wait = False
            try:
                result = message.forward(
                    chat_id=glovar.logging_channel_id,
                    disable_notification=True
                )
            except FloodWait as e:
                flood_wait = True
                sleep(e.x + 1)
            except Exception as e:
                logger.info(f"Forward evidence message error: {e}", exc_info=True)
                return False

        result = result.message_id
        result = send_message(client, glovar.logging_channel_id, text, result)
    except Exception as e:
        logger.warning(f"Forward evidence error: {e}", exc_info=True)

    return result


def get_debug_text(client: Client, context: Union[int, Chat]) -> str:
    # Get a debug message text prefix, accept int or Chat
    text = ""
    try:
        if isinstance(context, int):
            group_id = context
        else:
            group_id = context.id

        group_name, group_link = get_group_info(client, context)
        text = (f"项目编号：{general_link(glovar.project_name, glovar.project_link)}\n"
                f"群组名称：{general_link(group_name, group_link)}\n"
                f"群组 ID：{code(group_id)}\n")
    except Exception as e:
        logger.warning(f"Get debug text error: {e}", exc_info=True)

    return text


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


def send_debug(client: Client, chat: Chat, action: str, uid: int, mid: int, em: Message) -> bool:
    # Send the debug message
    try:
        text = get_debug_text(client, chat)
        text += (f"用户 ID：{code(uid)}\n"
                 f"执行操作：{code(action)}\n"
                 f"触发消息：{general_link(mid, message_link(em))}\n")
        thread(send_message, (client, glovar.debug_channel_id, text))
        return True
    except Exception as e:
        logger.warning(f"Send debug error: {e}", exc_info=True)

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
               file: str = None, encrypt: bool = True) -> bool:
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
            if encrypt:
                # Encrypt the file, save to the tmp directory
                file_path = get_new_path()
                crypt_file("encrypt", file, file_path)
            else:
                # Send directly
                file_path = file

            result = send_document(client, channel_id, file_path, text)
            # Delete the tmp file
            if result and "tmp/" in file_path:
                thread(delete_file, (file_path,))
        else:
            text = format_data(
                sender=glovar.sender,
                receivers=receivers,
                action=action,
                action_type=action_type,
                data=data
            )
            result = send_message(client, channel_id, text)

        # Sending failed due to channel issue
        if result is False:
            # Use hide channel instead
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
