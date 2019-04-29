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
from time import time
from copy import deepcopy

from pyrogram import Client, Filters

from .. import glovar
from ..functions.etc import bold, code, get_command_context, thread, user_mention
from ..functions.file import save
from ..functions.filters import is_class_c, test_group
from ..functions.group import get_debug_text
from ..functions.telegram import delete_messages, get_group_info, send_message, send_report_message
from ..functions.user import share_data

# Enable logging
logger = logging.getLogger(__name__)


@Client.on_message(Filters.incoming & Filters.group
                   & Filters.command(["config"], glovar.prefix))
def config(client, message):
    try:
        gid = message.chat.id
        mid = message.message_id
        # Check permission
        if is_class_c(None, message):
            command_list = list(filter(None, message.command))
            # Check command format
            if len(command_list) == 2 and re.search("^noporn$", command_list[1], re.I):
                now = int(time())
                # Check the config lock
                if now - glovar.configs[gid]["locked"] > 360:
                    # Set lock
                    glovar.configs[gid]["locked"] = now
                    # Ask CONFIG generate a config session
                    group_name, group_link = get_group_info(client, message.chat)
                    share_data(
                        client=client,
                        sender="NOPORN",
                        receivers=["CONFIG"],
                        action="config",
                        action_type="ask",
                        data={
                            "group_id": gid,
                            "group_name": group_name,
                            "group_link": group_link,
                            "user_id": message.from_user.id,
                            "config": glovar.configs[gid]
                        }
                    )
                    # Send a report message to debug channel
                    text = get_debug_text(client, message.chat)
                    text += (f"群管理：{user_mention(message.from_user.id)}\n"
                             f"操作：{'创建设置会话'}")
                    thread(send_message, (client, glovar.debug_channel_id, text))

        mids = [mid]
        thread(delete_messages, (client, gid, mids))
    except Exception as e:
        logger.warning(f"Config error: {e}", exc_info=True)


@Client.on_message(Filters.incoming & Filters.group
                   & Filters.command(["noporn_config"], glovar.prefix))
def noporn_config(client, message):
    try:
        gid = message.chat.id
        mid = message.message_id
        # Check permission
        if is_class_c(None, message):
            aid = message.from_user.id
            command_list = message.command
            success = True
            reason = "已更新"
            new_config = deepcopy(glovar.configs[gid])
            text = f"管理员：{user_mention(aid)}\n"
            # Check command format
            if len(command_list) > 1:
                now = int(time())
                # Check the config lock
                if now - new_config["locked"] > 360:
                    command_type = list(filter(None, command_list))[1]
                    if command_type == "show":
                        text += (f"操作：{code('查看设置')}\n"
                                 f"设置：{code((lambda x: '默认' if x else '自定义')(new_config.get('default')))}\n"
                                 f"过滤频道：{code((lambda x: '启用' if x else '禁用')(new_config.get('channel')))}\n"
                                 f"媒体复查：{code((lambda x: '启用' if x else '禁用')(new_config.get('recheck')))}")
                        thread(send_report_message, (15, client, gid, text))
                        mids = [mid]
                        thread(delete_messages, (client, gid, mids))
                        return
                    elif command_type == "default":
                        if not new_config["default"]:
                            new_config = deepcopy(glovar.default_config)
                    else:
                        command_context = get_command_context(message)
                        if command_context:
                            if command_type == "channel":
                                if command_context == "off":
                                    new_config["channel"] = False
                                elif command_context == "on":
                                    new_config["channel"] = True
                                else:
                                    success = False
                                    reason = "过滤选项有误"
                            elif command_type == "recheck":
                                if command_context == "off":
                                    new_config["recheck"] = False
                                elif command_context == "on":
                                    new_config["recheck"] = True
                                else:
                                    success = False
                                    reason = "复查选项有误"
                            else:
                                success = False
                                reason = "命令类别有误"
                        else:
                            success = False
                            reason = "命令选项缺失"

                        if success:
                            new_config["default"] = False
                else:
                    success = False
                    reason = "设置当前被锁定"
            else:
                success = False
                reason = "格式有误"

            if success and new_config != glovar.configs[gid]:
                glovar.configs[gid] = new_config
                save("configs")

            text += (f"操作：{code('更改设置')}\n"
                     f"状态：{code(reason)}")
            thread(send_report_message, ((lambda x: 10 if x else 5)(success), client, gid, text))

        mids = [mid]
        thread(delete_messages, (client, gid, mids))
    except Exception as e:
        logger.warning(f"Config error: {e}", exc_info=True)


@Client.on_message(Filters.incoming & Filters.group & test_group
                   & Filters.command(["version"], glovar.prefix))
def version(client, message):
    try:
        cid = message.chat.id
        mid = message.message_id
        text = f"版本：{bold(glovar.version)}"
        thread(send_message, (client, cid, text, mid))
    except Exception as e:
        logger.warning(f"Version error: {e}", exc_info=True)
