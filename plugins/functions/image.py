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
from os.path import exists
from typing import Optional

from PIL import Image
from pyrogram import Client
from nsfw import classify

from .etc import random_str
from .telegram import download_media

# Enable logging
logger = logging.getLogger(__name__)


def get_image_path(client: Client, file_id: str) -> Optional[str]:
    final_path = None
    try:
        file_path = random_str(8)
        while exists(f"tmp/{file_path}"):
            file_path = random_str(8)

        final_path = download_media(client, file_id, file_path)
    except Exception as e:
        logger.warning(f"Get image path error: {e}", exc_info=True)

    return final_path


def get_porn(path):
    porn = 0
    try:
        image = Image.open(path)
        sfw, nsfw = classify(image)
        porn = nsfw
    except Exception as e:
        logger.warning(f"Get porn error: {e}", exc_info=True)

    return porn
