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

from pyrogram import Client, Filters, InlineKeyboardButton, InlineKeyboardMarkup, Message

from .. import glovar
from ..functions.channel import get_debug_text, get_content, receive_file_data, receive_text_data
from ..functions.etc import code, thread, user_mention
from ..functions.file import get_new_path, save
from ..functions.filters import class_c, class_d, declared_message, exchange_channel, hide_channel
from ..functions.filters import is_class_e, is_declared_message, is_nsfw_user_id
from ..functions.filters import is_nsfw_media, is_nsfw_url, is_restricted_channel, new_group, test_group
from ..functions.group import get_message, leave_group, update_declared_id
from ..functions.user import receive_watch_user, terminate_nsfw_user
from ..functions.ids import init_group_id, init_user_id
from ..functions.telegram import get_admins, send_message, send_report_message
from ..functions.tests import porn_test

# Enable logging
logger = logging.getLogger(__name__)


@Client.on_message(Filters.incoming & Filters.group & ~test_group
                   & ~class_c & ~class_d & ~declared_message)
def check(client: Client, message: Message):
    # Check the messages sent from groups
    try:
        gid = message.chat.id
        # Restricted channel
        if glovar.configs[gid].get("channel") and is_restricted_channel(message):
            terminate_nsfw_user(client, message, "channel")
        # Content not in except lists
        elif not is_class_e(message):
            # NSFW url
            if is_nsfw_url(message):
                terminate_nsfw_user(client, message, "url")
            # NSFW media
            elif message.media and is_nsfw_media(client, message):
                terminate_nsfw_user(client, message, "media")
    except Exception as e:
        logger.warning(f"Check error: {e}", exc_info=True)


@Client.on_message(Filters.incoming & Filters.channel & hide_channel
                   & ~Filters.command(glovar.all_commands, glovar.prefix), group=-1)
def exchange_emergency(_: Client, message: Message):
    # Sent emergency channel transfer request
    try:
        # Read basic information
        data = receive_text_data(message)
        if data:
            sender = data["from"]
            receivers = data["to"]
            action = data["action"]
            action_type = data["type"]
            data = data["data"]
            if "EMERGENCY" in receivers:
                if action == "backup":
                    if action_type == "hide":
                        if data is True:
                            glovar.should_hide = data
                        elif data is False and sender == "MANAGE":
                            glovar.should_hide = data
    except Exception as e:
        logger.warning(f"Exchange emergency error: {e}", exc_info=True)


@Client.on_message(Filters.incoming & Filters.group
                   & (Filters.new_chat_members | Filters.group_chat_created | Filters.supergroup_chat_created)
                   & new_group)
def init_group(client: Client, message: Message):
    # Initiate new groups
    try:
        gid = message.chat.id
        text = get_debug_text(client, message.chat)
        invited_by = message.from_user.id
        # Check permission
        if invited_by == glovar.user_id:
            # Remove the left status
            if gid in glovar.left_group_ids:
                glovar.left_group_ids.discard(gid)

            # Update group's admin list
            if init_group_id(gid):
                admin_members = get_admins(client, gid)
                if admin_members:
                    glovar.admin_ids[gid] = {admin.user.id for admin in admin_members
                                             if not admin.user.is_bot and not admin.user.is_deleted}
                    save("admin_ids")
                    text += f"状态：{code('已加入群组')}\n"
                else:
                    thread(leave_group, (client, gid))
                    text += (f"状态：{code('已退出群组')}\n"
                             f"原因：{code('获取管理员列表失败')}\n")
        else:
            if gid in glovar.left_group_ids:
                return leave_group(client, gid)

            leave_group(client, gid)
            text += (f"状态：{code('已退出群组')}\n"
                     f"原因：{code('未授权使用')}\n"
                     f"邀请人：{user_mention(invited_by)}\n")

        thread(send_message, (client, glovar.debug_channel_id, text))
    except Exception as e:
        logger.warning(f"Init group error: {e}", exc_info=True)


@Client.on_message(Filters.incoming & Filters.channel & exchange_channel
                   & ~Filters.command(glovar.all_commands, glovar.prefix))
def process_data(client: Client, message: Message):
    # Process the data in exchange channel
    try:
        data = receive_text_data(message)
        if data:
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
                    if action == "add":
                        the_id = data["id"]
                        the_type = data["type"]
                        if action_type == "bad":
                            if the_type == "user":
                                glovar.bad_ids["users"].add(the_id)
                                save("bad_ids")
                        elif action_type == "watch":
                            receive_watch_user(the_type, the_id, data["until"])

                    elif action == "update":
                        if action_type == "declare":
                            group_id = data["group_id"]
                            message_id = data["message_id"]
                            update_declared_id(group_id, message_id)
                        elif action_type == "score":
                            uid = data["id"]
                            init_user_id(uid)
                            score = data["score"]
                            glovar.user_ids[uid]["score"]["clean"] = score
                            save("user_ids")

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

                    elif action == "update":
                        if action_type == "declare":
                            group_id = data["group_id"]
                            message_id = data["message_id"]
                            update_declared_id(group_id, message_id)
                        elif action_type == "score":
                            uid = data["id"]
                            init_user_id(uid)
                            score = data["score"]
                            glovar.user_ids[uid]["score"]["lang"] = score
                            save("user_ids")

                elif sender == "LONG":

                    if action == "add":
                        the_id = data["id"]
                        the_type = data["type"]
                        if action_type == "bad":
                            if the_type == "user":
                                glovar.bad_ids["users"].add(the_id)
                                save("bad_ids")
                        elif action_type == "watch":
                            receive_watch_user(the_type, the_id, data["until"])

                    elif action == "update":
                        if action_type == "declare":
                            group_id = data["group_id"]
                            message_id = data["message_id"]
                            update_declared_id(group_id, message_id)
                        elif action_type == "score":
                            uid = data["id"]
                            init_user_id(uid)
                            score = data["score"]
                            glovar.user_ids[uid]["score"]["long"] = score
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
                            content = get_content(client, the_id)
                            if content:
                                if the_type == "long":
                                    glovar.except_ids["long"].add(content)
                                elif the_type == "temp":
                                    glovar.except_ids["temp"].add(content)

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
                            content = get_content(client, the_id)
                            if content:
                                if the_type == "long":
                                    glovar.except_ids["long"].discard(content)
                                elif the_type == "temp":
                                    glovar.except_ids["temp"].discard(content)

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

                    elif action == "update":
                        if action_type == "declare":
                            group_id = data["group_id"]
                            message_id = data["message_id"]
                            update_declared_id(group_id, message_id)
                        elif action_type == "score":
                            uid = data["id"]
                            init_user_id(uid)
                            score = data["score"]
                            glovar.user_ids[uid]["score"]["noflood"] = score
                            save("user_ids")

                elif sender == "NOSPAM":

                    if action == "add":
                        the_id = data["id"]
                        the_type = data["type"]
                        if action_type == "bad":
                            if the_type == "user":
                                glovar.bad_ids["users"].add(the_id)
                                save("bad_ids")
                        elif action_type == "watch":
                            receive_watch_user(the_type, the_id, data["until"])

                    elif action == "update":
                        if action_type == "declare":
                            group_id = data["group_id"]
                            message_id = data["message_id"]
                            update_declared_id(group_id, message_id)
                        elif action_type == "score":
                            uid = data["id"]
                            init_user_id(uid)
                            score = data["score"]
                            glovar.user_ids[uid]["score"]["nospam"] = score
                            save("user_ids")

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

                    elif action == "update":
                        if action_type == "declare":
                            group_id = data["group_id"]
                            message_id = data["message_id"]
                            update_declared_id(group_id, message_id)
                        elif action_type == "score":
                            uid = data["id"]
                            init_user_id(uid)
                            score = data["score"]
                            glovar.user_ids[uid]["score"]["recheck"] = score
                            save("user_ids")

                elif sender == "REGEX":

                    if action == "update":
                        if action_type == "download":
                            file_name = data
                            words_data = receive_file_data(client, message, True)
                            if words_data:
                                if glovar.lock["regex"].acquire():
                                    try:
                                        pop_set = set(eval(f"glovar.{file_name}")) - set(words_data)
                                        new_set = set(words_data) - set(eval(f"glovar.{file_name}"))
                                        for word in pop_set:
                                            eval(f"glovar.{file_name}").pop(word, 0)

                                        for word in new_set:
                                            eval(f"glovar.{file_name}")[word] = 0

                                        save(file_name)
                                    except Exception as e:
                                        logger.warning(f"Update download regex error: {e}", exc_info=True)
                                    finally:
                                        glovar.lock["regex"].release()

                elif sender == "USER":

                    if action == "update":
                        if action_type == "preview":
                            # Get the preview data
                            gid = data["group_id"]
                            if glovar.admin_ids.get(gid):
                                uid = data["user_id"]
                                mid = data["message_id"]
                                preview = receive_file_data(client, message)
                                if preview:
                                    image = preview["image"]
                                    if image:
                                        image_path = get_new_path()
                                        image.save(image_path, "PNG")
                                        if (not is_declared_message(gid, mid)
                                                and not is_nsfw_user_id(gid, uid)):
                                            if is_nsfw_media(client, image_path):
                                                url = preview["url"]
                                                glovar.url_list.add(url)
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
def test(client: Client, message: Message):
    # Show test results in TEST group
    try:
        porn_test(client, message)
    except Exception as e:
        logger.warning(f"Test error: {e}", exc_info=True)
