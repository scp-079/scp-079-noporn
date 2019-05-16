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
from copy import deepcopy

from pyrogram import Client, Filters, InlineKeyboardButton, InlineKeyboardMarkup

from .. import glovar
from ..functions.channel import get_debug_text
from ..functions.etc import code, receive_data, thread, user_mention
from ..functions.file import save
from ..functions.filters import class_c, class_d, class_e, declared_ban_message, exchange_channel, hide_channel
from ..functions.filters import is_declared_ban_message_id, is_nsfw_user_id
from ..functions.filters import is_nsfw_media, is_restricted_channel, new_group, test_group
from ..functions.group import get_message, leave_group
from ..functions.user import receive_watch_user, terminate_nsfw_user
from ..functions.ids import init_group_id, init_user_id
from ..functions.telegram import get_admins, send_message, send_report_message
from ..functions.tests import porn_test

# Enable logging
logger = logging.getLogger(__name__)


@Client.on_message(Filters.incoming & Filters.group & ~test_group & Filters.media
                   & ~class_c & ~class_d & ~class_e & ~declared_ban_message)
def check(client, message):
    try:
        gid = message.chat.id
        if glovar.configs[gid].get("channel") and is_restricted_channel(message):
            terminate_nsfw_user(client, message, "channel")
        elif is_nsfw_media(client, message):
            terminate_nsfw_user(client, message, "media")
    except Exception as e:
        logger.warning(f"Check error: {e}", exc_info=True)


@Client.on_message(Filters.incoming & Filters.channel & hide_channel
                   & ~Filters.command(glovar.all_commands, glovar.prefix))
def exchange_emergency(_, message):
    try:
        # Read basic information
        data = receive_data(message)
        sender = data["from"]
        receivers = data["to"]
        action = data["action"]
        action_type = data["type"]
        data = data["data"]
        if "EMERGENCY" in receivers:
            if sender == "EMERGENCY":
                if action == "backup":
                    if action_type == "hide":
                        glovar.should_hide = data
    except Exception as e:
        logger.warning(f"Exchange emergency error: {e}", exc_info=True)


@Client.on_message(Filters.incoming & Filters.group & Filters.new_chat_members & new_group)
def init_group(client, message):
    try:
        gid = message.chat.id
        invited_by = message.from_user.id
        text = get_debug_text(client, message.chat)
        # Check permission
        if invited_by == glovar.user_id:
            # Update group's admin list
            if init_group_id(gid):
                admin_members = get_admins(client, gid)
                if admin_members:
                    glovar.admin_ids[gid] = {admin.user.id for admin in admin_members if not admin.user.is_bot}
                    save("admin_ids")
                    text += f"状态：{code('已加入群组')}"
                else:
                    thread(leave_group, (client, gid))
                    text += (f"状态：{code('已退出群组')}\n"
                             f"原因：{code('获取管理员列表失败')}")
        else:
            leave_group(client, gid)
            if gid in glovar.left_group_ids:
                return
            else:
                glovar.left_group_ids.add(gid)

            text += (f"状态：{code('已退出群组')}\n"
                     f"原因：{code('未授权使用')}\n"
                     f"邀请人：{user_mention(invited_by)}")

        thread(send_message, (client, glovar.debug_channel_id, text))
    except Exception as e:
        logger.warning(f"Init group error: {e}", exc_info=True)


@Client.on_message(Filters.channel & exchange_channel
                   & ~Filters.command(glovar.all_commands, glovar.prefix))
def process_data(client, message):
    try:
        data = receive_data(message)
        sender = data["from"]
        receivers = data["to"]
        action = data["action"]
        action_type = data["type"]
        data = data["data"]
        # This will look awkward,
        # seems like it can be simplified,
        # but this is to ensure that the permissions are clear,
        # so it is intentionally written like this
        if glovar.sender in receivers:
            if sender == "CAPTCHA":

                if action == "update":
                    if action_type == "score":
                        uid = data["id"]
                        init_user_id(uid)
                        score = data["score"]
                        glovar.user_ids[uid]["score"]["captcha"] = score
                        save("user_ids")

            elif sender == "CLEAN":

                if action == "declare":
                    group_id = data["group_id"]
                    message_id = data["message_id"]
                    if glovar.configs.get(group_id):
                        if init_group_id(group_id):
                            if action_type == "ban":
                                glovar.declared_message_ids["ban"][group_id].add(message_id)
                            elif action_type == "delete":
                                glovar.declared_message_ids["delete"][group_id].add(message_id)

            elif sender == "CONFIG":

                if action == "config":
                    if action_type == "commit":
                        gid = data["group_id"]
                        config = data["config"]
                        glovar.configs[gid] = config
                        save("configs")
                    elif action_type == "reply":
                        gid = data["group_id"]
                        uid = data["user_id"]
                        link = data["config_link"]
                        text = (f"管理员：{user_mention(uid)}\n"
                                f"操作：{code('更改设置')}\n"
                                f"说明：{code('请点击下方按钮进行设置')}")
                        markup = InlineKeyboardMarkup(
                            [
                                [
                                    InlineKeyboardButton(
                                        "前往设置",
                                        url=link
                                    )
                                ]
                            ]
                        )
                        thread(send_report_message, (180, client, gid, text, None, markup))

            elif sender == "LANG":

                if action == "add":
                    the_id = data["id"]
                    the_type = data["type"]
                    if action_type == "bad":
                        if the_type == "user":
                            glovar.bad_ids["users"].add(the_id)
                            save("bad_ids")
                    elif action_type == "watch":
                        receive_watch_user(the_type, the_id, data["until"])

                elif action == "declare":
                    group_id = data["group_id"]
                    message_id = data["message_id"]
                    if glovar.configs.get(group_id):
                        if init_group_id(group_id):
                            if action_type == "ban":
                                glovar.declared_message_ids["ban"][group_id].add(message_id)
                            elif action_type == "delete":
                                glovar.declared_message_ids["delete"][group_id].add(message_id)

                elif action == "update":
                    if action_type == "score":
                        uid = data["id"]
                        init_user_id(uid)
                        score = data["score"]
                        glovar.user_ids[uid]["score"]["lang"] = score
                        save("user_ids")

            elif sender == "MANAGE":

                if action == "add":
                    the_id = data["id"]
                    the_type = data["type"]
                    if action_type == "bad":
                        if the_type == "channel":
                            glovar.bad_ids["channels"].add(the_id)
                            save("bad_ids")
                    elif action_type == "except":
                        if the_type == "channels":
                            glovar.except_ids["channels"].add(the_id)
                        elif the_type == "sticker":
                            glovar.except_ids["stickers"].add(the_id)
                        elif the_type == "tmp":
                            glovar.except_ids["tmp"].add(the_id)
                        elif the_type == "user":
                            glovar.except_ids["users"].add(the_id)

                        save("except_ids")

                elif action == "leave":
                    if action_type == "approve":
                        the_id = data["group_id"]
                        reason = data["reason"]
                        if action_type == "group":
                            text = get_debug_text(client, the_id)
                            text += (f"状态：{code('已退出该群组')}\n"
                                     f"原因：{code(reason)}")
                            leave_group(client, the_id)
                            thread(send_message, (client, glovar.debug_channel_id, text))

                elif action == "remove":
                    the_id = data["id"]
                    the_type = data["type"]
                    if action_type == "bad":
                        if the_type == "channel":
                            glovar.bad_ids["channels"].discard(the_id)
                        elif the_type == "user":
                            glovar.bad_ids["users"].discard(the_id)
                            glovar.watch_ids["ban"].pop(the_id, {})
                            glovar.watch_ids["delete"].pop(the_id, {})
                            if glovar.user_ids.get(the_id):
                                glovar.user_ids[the_id] = deepcopy(glovar.default_user_status)

                            save("user_ids")

                        save("bad_ids")
                    elif action_type == "except":
                        if the_type == "channel":
                            glovar.except_ids["channels"].discard(the_id)
                        elif the_type == "stickers":
                            glovar.except_ids["stickers"].discard(the_id)
                        elif the_type == "tmp":
                            glovar.except_ids["tmp"].discard(the_id)
                        elif the_type == "user":
                            glovar.except_ids["users"].discard(the_id)

                        save("except_ids")
                    elif action_type == "watch":
                        if the_type == "all":
                            glovar.watch_ids["ban"].pop(the_id, 0)
                            glovar.watch_ids["delete"].pop(the_id, 0)

            elif sender == "NOFLOOD":

                if action == "add":
                    the_id = data["id"]
                    the_type = data["type"]
                    if action_type == "bad":
                        if the_type == "user":
                            glovar.bad_ids["users"].add(the_id)
                            save("bad_ids")
                    elif action_type == "watch":
                        receive_watch_user(the_type, the_id, data["until"])

                elif action == "declare":
                    group_id = data["group_id"]
                    message_id = data["message_id"]
                    if glovar.configs.get(group_id):
                        if init_group_id(group_id):
                            if action_type == "ban":
                                glovar.declared_message_ids["ban"][group_id].add(message_id)
                            elif action_type == "delete":
                                glovar.declared_message_ids["delete"][group_id].add(message_id)

                elif action == "update":
                    if action_type == "score":
                        uid = data["id"]
                        init_user_id(uid)
                        score = data["score"]
                        glovar.user_ids[uid]["score"]["noflood"] = score
                        save("user_ids")

            elif sender == "NOPORN":

                if action == "add":
                    the_id = data["id"]
                    the_type = data["type"]
                    if action_type == "bad":
                        if the_type == "user":
                            glovar.bad_ids["users"].add(the_id)
                            save("bad_ids")
                    elif action_type == "watch":
                        receive_watch_user(the_type, the_id, data["until"])

                elif action == "declare":
                    group_id = data["group_id"]
                    message_id = data["message_id"]
                    if glovar.configs.get(group_id):
                        if init_group_id(group_id):
                            if action_type == "ban":
                                glovar.declared_message_ids["ban"][group_id].add(message_id)
                            elif action_type == "delete":
                                glovar.declared_message_ids["delete"][group_id].add(message_id)

                elif action == "update":
                    if action_type == "score":
                        uid = data["id"]
                        init_user_id(uid)
                        score = data["score"]
                        glovar.user_ids[uid]["score"]["noporn"] = score
                        save("user_ids")

            elif sender == "NOSPAM":

                if action == "add":
                    the_id = data["id"]
                    the_type = data["type"]
                    if action_type == "bad":
                        if the_type == "user":
                            glovar.bad_ids["users"].add(the_id)
                            save("bad_ids")

                elif action == "declare":
                    group_id = data["group_id"]
                    message_id = data["message_id"]
                    if glovar.configs.get(group_id):
                        if init_group_id(group_id):
                            if action_type == "ban":
                                glovar.declared_message_ids["ban"][group_id].add(message_id)
                            elif action_type == "delete":
                                glovar.declared_message_ids["delete"][group_id].add(message_id)

            elif sender == "RECHECK":

                if action == "add":
                    the_id = data["id"]
                    the_type = data["type"]
                    if action_type == "bad":
                        if the_type == "user":
                            glovar.bad_ids["users"].add(the_id)
                            save("bad_ids")
                    elif action_type == "watch":
                        receive_watch_user(the_type, the_id, data["until"])

                elif action == "declare":
                    group_id = data["group_id"]
                    message_id = data["message_id"]
                    if glovar.configs.get(group_id):
                        if init_group_id(group_id):
                            if action_type == "ban":
                                glovar.declared_message_ids["ban"][group_id].add(message_id)
                            elif action_type == "delete":
                                glovar.declared_message_ids["delete"][group_id].add(message_id)

                elif action == "update":
                    if action_type == "score":
                        uid = data["id"]
                        init_user_id(uid)
                        score = data["score"]
                        glovar.user_ids[uid]["score"]["recheck"] = score
                        save("user_ids")

            elif sender == "USER":

                if action == "update":
                    if action_type == "preview":
                        # Get the preview data
                        gid = data["group_id"]
                        if glovar.configs.get(gid):
                            uid = data["user_id"]
                            mid = data["message_id"]
                            file_id = data["image"]
                            if file_id:
                                if (not is_declared_ban_message_id(gid, mid)
                                        and not is_nsfw_user_id(gid, uid)):
                                    if is_nsfw_media(client, file_id):
                                        the_message = get_message(client, gid, mid)
                                        if the_message:
                                            terminate_nsfw_user(client, the_message, "media")

            elif sender == "WARN":

                if action == "update":
                    if action_type == "score":
                        uid = data["id"]
                        init_user_id(uid)
                        score = data["score"]
                        glovar.user_ids[uid]["score"]["warn"] = score
                        save("user_ids")

            elif sender == "WATCH":

                if action == "add":
                    the_id = data["id"]
                    the_type = data["type"]
                    if action_type == "watch":
                        receive_watch_user(the_type, the_id, data["until"])

    except Exception as e:
        logger.warning(f"Process data error: {e}", exc_info=True)


@Client.on_message(Filters.incoming & Filters.group & test_group & Filters.media
                   & ~Filters.command(glovar.all_commands, glovar.prefix))
def test(client, message):
    try:
        porn_test(client, message)
    except Exception as e:
        logger.warning(f"Test error: {e}", exc_info=True)
