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

from pyrogram import Client, Message

from .. import glovar
from .etc import code, get_int, get_text, thread, user_mention
from .file import get_downloaded_path
from .filters import is_class_e, is_nsfw_url, is_restricted_channel
from .image import get_file_id, get_color, get_porn
from .telegram import send_message

# Enable logging
logger = logging.getLogger(__name__)


def porn_test(client: Client, message: Message) -> bool:
    # Test image porn score in the test group
    if glovar.lock["image"].acquire():
        try:
            file_id = get_file_id(message)
            if file_id:
                image_path = get_downloaded_path(client, file_id)
                if image_path:
                    message_text = get_text(message)
                    if re.search("^管理员：[0-9]", message_text):
                        aid = get_int(message_text.split("\n")[0].split("：")[1])
                    else:
                        aid = message.from_user.id

                    porn = get_porn(image_path)
                    color = get_color(image_path)
                    text = (f"管理员：{user_mention(aid)}\n\n"
                            f"NSFW 得分：{code(f'{porn:.8f}')}\n"
                            f"NSFW 记录：{code(file_id in glovar.file_ids['nsfw'])}\n"
                            f"NSFW 链接：{code(is_nsfw_url(message))}\n"
                            f"白名单：{code(is_class_e(None, message))}\n"
                            f"受限频道：{code(is_restricted_channel(message))}\n"
                            f"敏感颜色：{code(color)}\n")
                    thread(send_message, (client, glovar.test_group_id, text, message.message_id))
            
                    return True
        except Exception as e:
            logger.warning(f"Porn test error: {e}", exc_info=True)
        finally:
            glovar.lock["image"].release()

    return False
