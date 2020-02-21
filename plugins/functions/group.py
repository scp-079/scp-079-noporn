# SCP-079-NOPORN - Auto delete NSFW media messages
# Copyright (C) 2019-2020 SCP-079 <https://scp-079.org>
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
from typing import Optional

from pyrogram import Chat, ChatMember, Client, Message

from .. import glovar
from .etc import code, lang, t2t, thread
from .file import save
from .ids import init_group_id
from .telegram import delete_messages, get_chat, get_chat_member, get_messages, leave_chat

# Enable logging
logger = logging.getLogger(__name__)


def delete_message(client: Client, gid: int, mid: int) -> bool:
    # Delete a single message
    try:
        if not gid or not mid:
            return True

        mids = [mid]
        thread(delete_messages, (client, gid, mids))

        return True
    except Exception as e:
        logger.warning(f"Delete message error: {e}", exc_info=True)

    return False


def get_config_text(config: dict) -> str:
    # Get config text
    result = ""
    try:
        # Basic
        default_text = (lambda x: lang("default") if x else lang("custom"))(config.get("default"))
        delete_text = (lambda x: lang("enabled") if x else lang("disabled"))(config.get("delete"))
        restrict_text = (lambda x: lang("enabled") if x else lang("disabled"))(config.get("restrict"))
        result += (f"{lang('config')}{lang('colon')}{code(default_text)}\n"
                   f"{lang('delete')}{lang('colon')}{code(delete_text)}\n"
                   f"{lang('restrict')}{lang('colon')}{code(restrict_text)}\n")

        # Restricted Channel
        channel_text = (lambda x: lang("enabled") if x else lang("disabled"))(config.get("channel"))
        result += f"{lang('noporn_channel')}{lang('colon')}{code(channel_text)}\n"
    except Exception as e:
        logger.warning(f"Get config text error: {e}", exc_info=True)

    return result


def get_description(client: Client, gid: int, cache: bool = True) -> str:
    # Get group's description
    result = ""
    try:
        group = get_group(client, gid, cache)

        if group and group.description:
            result = t2t(group.description, False, False)
    except Exception as e:
        logger.warning(f"Get description error: {e}", exc_info=True)

    return result


def get_group(client: Client, gid: int, cache: bool = True) -> Optional[Chat]:
    # Get the group
    result = None
    try:
        the_cache = glovar.chats.get(gid)

        if the_cache:
            result = the_cache
        else:
            result = get_chat(client, gid)

        if cache and result:
            glovar.chats[gid] = result
    except Exception as e:
        logger.warning(f"Get group error: {e}", exc_info=True)

    return result


def get_group_sticker(client: Client, gid: int, cache: bool = True) -> str:
    # Get group sticker set name
    result = ""
    try:
        group = get_group(client, gid, cache)

        if group and group.sticker_set_name:
            result = group.sticker_set_name
    except Exception as e:
        logger.warning(f"Get group sticker error: {e}", exc_info=True)

    return result


def get_member(client: Client, gid: int, uid: int, cache: bool = True) -> Optional[ChatMember]:
    # Get a member in the group
    result = None
    try:
        if not init_group_id(gid):
            return None

        the_cache = glovar.members[gid].get(uid)

        if the_cache:
            result = the_cache
        else:
            result = get_chat_member(client, gid, uid)

        if cache and result:
            glovar.members[gid][uid] = result
    except Exception as e:
        logger.warning(f"Get member error: {e}", exc_info=True)

    return result


def get_message(client: Client, gid: int, mid: int) -> Optional[Message]:
    # Get a single message
    result = None
    try:
        mids = [mid]
        result = get_messages(client, gid, mids)

        if result:
            result = result[0]
    except Exception as e:
        logger.warning(f"Get message error: {e}", exc_info=True)

    return result


def get_pinned(client: Client, gid: int, cache: bool = True) -> Optional[Message]:
    # Get group's pinned message
    result = None
    try:
        group = get_group(client, gid, cache)

        if group and group.pinned_message:
            result = group.pinned_message
    except Exception as e:
        logger.warning(f"Get pinned error: {e}", exc_info=True)

    return result


def leave_group(client: Client, gid: int) -> bool:
    # Leave a group, clear it's data
    try:
        glovar.left_group_ids.add(gid)
        save("left_group_ids")
        thread(leave_chat, (client, gid))

        glovar.admin_ids.pop(gid, None)
        save("admin_ids")

        glovar.trust_ids.pop(gid, set())
        save("trust_ids")

        glovar.configs.pop(gid, None)
        save("configs")

        glovar.declared_message_ids.pop(gid, set())
        glovar.members.pop(gid, {})
        glovar.recorded_ids.pop(gid, set())

        return True
    except Exception as e:
        logger.warning(f"Leave group error: {e}", exc_info=True)

    return False
