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
from .channel import get_content
from .etc import code, get_int, get_md5sum, get_text, lang, thread, user_mention
from .file import get_downloaded_path
from .filters import is_class_e, is_detected_url, is_restricted_channel
from .image import get_file_id, get_color, get_porn
from .telegram import send_message

# Enable logging
logger = logging.getLogger(__name__)


def porn_test(client: Client, message: Message) -> bool:
    # Test image porn score in the test group
    try:
        message_text = get_text(message, True)
        if re.search(f"^{lang('admin')}{lang('colon')}[0-9]", message_text):
            aid = get_int(message_text.split("\n")[0].split("：")[1])
        else:
            aid = message.from_user.id

        text = ""

        # Detected record
        content = get_content(message)
        detection = glovar.contents.get(content, "")
        if detection:
            text += f"{lang('record_content')}{lang('colon')}{code('True')}\n"

        # Detected url
        detection = is_detected_url(message)
        if detection:
            text += f"{lang('record_link')}{lang('colon')}{code(code('True'))}\n"

        # Restricted channel
        if is_restricted_channel(message):
            text += f"{lang('restricted_channel')}{lang('colon')}{code('True')}\n"

        # Get the image
        file_id, file_ref, _ = get_file_id(message)
        image_path = get_downloaded_path(client, file_id, file_ref)
        image_hash = image_path and get_md5sum("file", image_path)

        # Get porn score
        porn = (image_path and get_porn(image_path))
        if porn:
            text += f"{lang('porn_score')}{lang('colon')}{code(f'{porn:.8f}')}\n"

        # Get color
        color = image_path and get_color(image_path)
        if color:
            text += f"{lang(lang('color'))}{lang('colon')}{code(color)}\n"

        if text:
            whitelisted = is_class_e(None, message) or image_hash in glovar.except_ids["temp"]
            text += f"{lang('white_listed')}{lang('colon')}{code(whitelisted)}\n"
            text = f"{lang('admin')}{lang('colon')}{user_mention(aid)}\n\n" + text
            thread(send_message, (client, glovar.test_group_id, text, message.message_id))

        return True
    except Exception as e:
        logger.warning(f"Porn test error: {e}", exc_info=True)

    return False
