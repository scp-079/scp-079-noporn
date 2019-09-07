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
from json import dumps
from typing import List, Optional, Union

from pyrogram import Chat, Client, Message
from pyrogram.errors import FloodWait

from .. import glovar
from .etc import code, code_block, general_link, get_forward_name, get_full_name, get_md5sum, get_text, message_link
from .etc import thread, wait_flood
from .file import crypt_file, data_to_file, delete_file, get_new_path, save
from .image import get_file_id
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
            receivers=glovar.receivers["declare"],
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
        share_data(
            client=client,
            receivers=["EMERGENCY"],
            action="backup",
            action_type="hide",
            data=True
        )
        text = (f"项目编号：{code(glovar.sender)}\n"
                f"发现状况：{code('数据交换频道失效')}\n"
                f"自动处理：{code('启用 1 号协议')}\n")
        thread(send_message, (client, glovar.critical_channel_id, text))

        return True
    except Exception as e:
        logger.warning(f"Exchange to hide error: {e}", exc_info=True)

    return False


def format_data(sender: str, receivers: List[str], action: str, action_type: str,
                data: Union[bool, dict, int, str] = None) -> str:
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


def forward_evidence(client: Client, message: Message, level: str, rule: str, score: float = 0.0,
                     more: str = None) -> Optional[Union[bool, Message]]:
    # Forward the message to the logging channel as evidence
    result = None
    try:
        uid = message.from_user.id
        text = (f"项目编号：{code(glovar.sender)}\n"
                f"用户 ID：{code(uid)}\n"
                f"操作等级：{code(level)}\n"
                f"规则：{code(rule)}\n")

        if message.game:
            text += f"消息类别：{code('游戏')}\n"
        elif message.service:
            text += f"消息类别：{code('服务消息')}\n"

        if "评分" in rule:
            text += f"用户得分：{code(score)}\n"

        if "名称" in rule:
            name = get_full_name(message.from_user)
            if name:
                text += f"用户昵称：{code(name)}\n"

            forward_name = get_forward_name(message)
            if forward_name and forward_name != name:
                text += f"来源名称：{code(forward_name)}\n"

        if message.contact or message.location or message.venue or message.video_note or message.voice:
            text += f"附加信息：{code('可能涉及隐私而未转发')}\n"
        elif message.game or message.service:
            text += f"附加信息：{code('此类消息无法转发至频道')}\n"
        elif more:
            text += f"附加信息：{code(more)}\n"

        # DO NOT try to forward these types of message
        if (message.contact or message.location
                or message.venue
                or message.video_note
                or message.voice
                or message.game
                or message.service):
            result = send_message(client, glovar.logging_channel_id, text)
            return result

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
                wait_flood(e)
            except Exception as e:
                logger.info(f"Forward evidence message error: {e}", exc_info=True)
                return False

        result = result.message_id
        result = send_message(client, glovar.logging_channel_id, text, result)
    except Exception as e:
        logger.warning(f"Forward evidence error: {e}", exc_info=True)

    return result


def get_content(message: Message) -> str:
    # Get the message that will be added to except_ids, return the file_id or text's hash
    result = ""
    try:
        if message:
            file_id, _ = get_file_id(message)
            text = get_text(message)
            if file_id:
                result += file_id
            elif text:
                result += get_md5sum("string", text)
    except Exception as e:
        logger.warning(f"Get content error: {e}", exc_info=True)

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
            receivers=glovar.receivers["bad"],
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


def share_data(client: Client, receivers: List[str], action: str, action_type: str, data: Union[bool, dict, int, str],
               file: str = None, encrypt: bool = True) -> bool:
    # Use this function to share data in the exchange channel
    try:
        if glovar.sender in receivers:
            receivers.remove(glovar.sender)

        if receivers:
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
                if result:
                    for f in {file, file_path}:
                        if "tmp/" in f:
                            thread(delete_file, (f,))
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
                thread(share_data, (client, receivers, action, action_type, data, file, encrypt))

            return True
    except Exception as e:
        logger.warning(f"Share data error: {e}", exc_info=True)

    return False


def share_regex_count(client: Client, word_type: str) -> bool:
    # Use this function to share regex count to REGEX
    try:
        if glovar.regex[word_type]:
            file = data_to_file(eval(f"glovar.{word_type}_words"))
            share_data(
                client=client,
                receivers=["REGEX"],
                action="update",
                action_type="count",
                data=f"{word_type}_words",
                file=file
            )

        return True
    except Exception as e:
        logger.warning(f"Share regex update error: {e}", exc_info=True)

    return False


def share_watch_user(client: Client, the_type: str, uid: int, until: str) -> bool:
    # Share a watch ban user with other bots
    try:
        share_data(
            client=client,
            receivers=glovar.receivers["watch"],
            action="add",
            action_type="watch",
            data={
                "id": uid,
                "type": the_type,
                "until": until
            }
        )

        return True
    except Exception as e:
        logger.warning(f"Share watch user error: {e}", exc_info=True)


def update_score(client: Client, uid: int) -> bool:
    # Update a user's score, share it
    try:
        count = len(glovar.user_ids[uid]["detected"])
        score = count * 0.6
        glovar.user_ids[uid]["score"][glovar.sender.lower()] = score
        save("user_ids")
        share_data(
            client=client,
            receivers=glovar.receivers["score"],
            action="update",
            action_type="score",
            data={
                "id": uid,
                "score": score
            }
        )

        return True
    except Exception as e:
        logger.warning(f"Update score error: {e}", exc_info=True)

    return False
