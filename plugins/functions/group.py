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
from typing import Optional

from pyrogram import Chat, Client, Message

from .. import glovar
from .etc import thread
from .file import save
from .telegram import delete_messages, get_chat, get_messages, leave_chat

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


def get_description(client: Client, gid: int) -> str:
    # Get group's description
    result = ""
    try:
        group = get_group(client, gid)
        if group and group.description:
            result = group.description
    except Exception as e:
        logger.warning(f"Get description error: {e}", exc_info=True)

    return result


def get_group(client: Client, gid: int) -> Optional[Chat]:
    # Get the group
    result = None
    try:
        cache = glovar.chats.get(gid)
        if cache:
            result = cache
        else:
            result = get_chat(client, gid)
    except Exception as e:
        logger.warning(f"Get group error: {e}", exc_info=True)

    return result


def get_group_sticker(client: Client, gid: int) -> str:
    # Get group sticker set name
    result = ""
    try:
        group = get_group(client, gid)
        if group and group.sticker_set_name:
            result = group.sticker_set_name
    except Exception as e:
        logger.warning(f"Get group sticker error: {e}", exc_info=True)

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


def get_pinned(client: Client, gid: int) -> Optional[Message]:
    # Get group's pinned message
    result = None
    try:
        group = get_group(client, gid)
        if group and group.pinned_message:
            result = group.pinned_message
    except Exception as e:
        logger.warning(f"Get pinned error: {e}", exc_info=True)

    return result


def leave_group(client: Client, gid: int) -> bool:
    # Leave a group, clear it's data
    try:
        glovar.left_group_ids.add(gid)
        thread(leave_chat, (client, gid))

        glovar.admin_ids.pop(gid, None)
        save("admin_ids")

        glovar.configs.pop(gid, None)
        save("configs")

        return True
    except Exception as e:
        logger.warning(f"Leave group error: {e}", exc_info=True)

    return False
