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

from pyrogram import Client

from .. import glovar
from .etc import send_data, thread
from .file import save
from .telegram import send_message

# Enable logging
logger = logging.getLogger(__name__)


def ask_for_help(client: Client, level: str, gid: int, uid: int) -> bool:
    try:
        data = send_data(
            sender="NOPORN",
            receivers=["USER"],
            action="help",
            action_type=level,
            data={
                "group_id": gid,
                "user_id": uid
            }
        )
        thread(send_message, (client, glovar.exchange_channel_id, data))
        return True
    except Exception as e:
        logger.warning(f"Ask for help error: {e}", exc_info=True)

    return False


def update_score(client: Client, uid: int) -> bool:
    try:
        nsfw_count = len(glovar.user_ids[uid]["nsfw"])
        nsfw_score = nsfw_count * 0.6
        warn_score = glovar.user_ids[uid]["score"]["warn"]
        glovar.user_ids[uid]["score"]["total"] = nsfw_score + warn_score
        save("user_ids")
        exchange_text = send_data(
            sender="NOPORN",
            receivers=["NOSPAM"],
            action="update",
            action_type="score",
            data={
                "id": uid,
                "score": nsfw_score
            }
        )
        thread(send_message, (client, glovar.exchange_channel_id, exchange_text))
        return True
    except Exception as e:
        logger.warning(f"Update score error: {e}", exc_info=True)

    return False
