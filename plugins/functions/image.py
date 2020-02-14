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

from PIL import Image
from pyrogram import Client, Message
from nsfw import classify

from .. import glovar
from .etc import get_md5sum, thread
from .file import delete_file, get_downloaded_path

# Enable logging
logger = logging.getLogger(__name__)


def get_color(path: str) -> bool:
    # Get the picture's color, check if most of it is yellow
    try:
        image = Image.open(path).convert('YCbCr')
        w, h = image.size
        data = image.getdata()
        cnt = 0

        for i, ycbcr in enumerate(data):
            y, cb, cr = ycbcr

            if 86 <= cb <= 117 and 140 <= cr <= 168:
                cnt += 1

        if cnt > w * h * 0.3:
            return True
    except Exception as e:
        logger.warning(f"Get color error: {e}", exc_info=True)

    return False


def get_file_id(message: Message) -> (str, str, bool):
    # Get media message's image file id
    file_id = ""
    file_ref = ""
    big = False
    try:
        if (message.photo
                or (message.sticker and not message.sticker.is_animated)
                or message.document
                or message.game):
            if message.photo:
                file_id = message.photo.file_id
                file_ref = message.photo.file_ref
            elif message.sticker:
                file_id = message.sticker.file_id
                file_ref = message.sticker.file_ref
            elif message.document:
                if (message.document.mime_type
                        and "image" in message.document.mime_type
                        and "gif" not in message.document.mime_type
                        and message.document.file_size
                        and message.document.file_size < glovar.image_size):
                    file_id = message.document.file_id
                    file_ref = message.document.file_ref
            elif message.game:
                file_id = message.game.photo.file_id
                file_ref = message.game.photo.file_ref

        if file_id:
            big = True
        elif ((message.animation and message.animation.thumbs)
              or (message.audio and message.audio.thumbs)
              or (message.video and message.video.thumbs)
              or (message.video_note and message.video_note.thumbs)
              or (message.document and message.document.thumbs)):
            if message.animation:
                file_id = message.animation.thumbs[-1].file_id
                file_ref = message.animation.file_ref
            elif message.audio:
                file_id = message.audio.thumbs[-1].file_id
                file_ref = message.audio.file_ref
            elif message.video:
                file_id = message.video.thumbs[-1].file_id
                file_ref = message.video.file_ref
            elif message.video_note:
                file_id = message.video_note.thumbs[-1].file_id
                file_ref = message.video_note.file_ref
            elif message.document:
                file_id = message.document.thumbs[-1].file_id
                file_ref = message.document.file_ref
    except Exception as e:
        logger.warning(f"Get image status error: {e}", exc_info=True)

    return file_id, file_ref, big


def get_image_hash(client: Client, message: Message) -> str:
    # Get the image's hash
    result = ""
    try:
        file_id, file_ref, big = get_file_id(message)

        if not file_id:
            return ""

        image_path = get_downloaded_path(client, file_id, file_ref)

        if not image_path:
            return ""

        result = get_md5sum("file", image_path)
        thread(delete_file, (image_path,))
    except Exception as e:
        logger.warning(f"Get image hash error: {e}", exc_info=True)

    return result


def get_porn(path: str) -> float:
    # Get porn score
    result = 0
    try:
        image = Image.open(path)
        sfw, nsfw = classify(image)
        result = nsfw
    except Exception as e:
        logger.warning(f"Get porn error: {e}", exc_info=True)

    return result
