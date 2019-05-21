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

from pyrogram import Client, Message

from .. import glovar
from .etc import code, thread, user_mention
from .file import get_downloaded_path
from .image import get_file_id, get_porn
from .telegram import send_message

# Enable logging
logger = logging.getLogger(__name__)


def porn_test(client: Client, message: Message) -> bool:
    # Test image porn score in the test group
    if glovar.lock_image.acquire():
        try:
            file_id = get_file_id(message)
            image_path = get_downloaded_path(client, file_id)
            if image_path:
                aid = message.from_user.id
                porn = get_porn(image_path)
                text = (f"管理员：{user_mention(aid)}\n\n"
                        f"NSFW 得分：{code(porn)}")
                thread(send_message, (client, glovar.test_group_id, text, message.message_id))
            return True
        except Exception as e:
            logger.warning(f"Porn test error: {e}", exc_info=True)
        finally:
            glovar.lock_image.release()

    return False
