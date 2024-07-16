# maunium-stickerpicker - A fast and simple Matrix sticker picker widget.
# Copyright (C) 2020 Tulir Asokan
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
from functools import partial
from io import BytesIO
import os.path
import json
import tempfile
import mimetypes

try:
    import magic
except ImportError:
    print("[Warning] Magic is not installed, using file extensions to guess mime types")
    magic = None
from PIL import Image

from . import matrix

open_utf8 = partial(open, encoding='UTF-8')


def guess_mime(data: bytes) -> str:
    mime = None
    if magic:
        try:
            return magic.Magic(mime=True).from_buffer(data)
        except Exception:
            pass
    else:
        with tempfile.NamedTemporaryFile(delete=False) as temp:
            temp.write(data)
            temp.close()
            mime, _ = mimetypes.guess_type(temp.name)
    return mime or "image/png"


def video_to_gif(data: bytes, mime: str) -> bytes:
    from moviepy.editor import VideoFileClip
    ext = mimetypes.guess_extension(mime)
    with tempfile.NamedTemporaryFile(suffix=ext) as temp:
        temp.write(data)
        temp.flush()
        with tempfile.NamedTemporaryFile(suffix=".gif") as gif:
            clip = VideoFileClip(temp.name)
            clip.write_gif(gif.name, logger=None)
            gif.seek(0)
            return gif.read()


def _convert_image(data: bytes) -> (bytes, int, int):
    image: Image.Image = Image.open(BytesIO(data)).convert("RGBA")
    new_file = BytesIO()
    image.save(new_file, "png")
    w, h = image.size
    if w > 256 or h > 256:
        # Set the width and height to lower values so clients wouldn't show them as huge images
        if w > h:
            h = int(h / (w / 256))
            w = 256
        else:
            w = int(w / (h / 256))
            h = 256
    return new_file.getvalue(), w, h


def convert_image(data: bytes) -> (bytes, str, int, int):
    mimetype = guess_mime(data)
    if mimetype.startswith("video/"):
        data = video_to_gif(data, mimetype)
        print(".", end="", flush=True)
        mimetype = "image/gif"
    try:
        rlt = _convert_image(data)
        return  rlt[0], mimetype, rlt[1], rlt[2]
    except Exception as e:
        print(f"Error converting image, mimetype: {mimetype}")
        ext = mimetypes.guess_extension(mimetype)
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp:
            temp.write(data)
            print(f"Saved to {temp.name}")
        raise e


def add_to_index(name: str, output_dir: str) -> None:
    index_path = os.path.join(output_dir, "index.json")
    try:
        with open_utf8(index_path) as index_file:
            index_data = json.load(index_file)
    except (FileNotFoundError, json.JSONDecodeError):
        index_data = {"packs": []}
    if "homeserver_url" not in index_data and matrix.homeserver_url:
        index_data["homeserver_url"] = matrix.homeserver_url
    if name not in index_data["packs"]:
        index_data["packs"].append(name)
        with open_utf8(index_path, "w") as index_file:
            json.dump(index_data, index_file, indent="  ")
        print(f"Added {name} to {index_path}")


def make_sticker(mxc: str, width: int, height: int, size: int,
                 mimetype: str, body: str = "") -> matrix.StickerInfo:
    return {
        "body": body,
        "url": mxc,
        "info": {
            "w": width,
            "h": height,
            "size": size,
            "mimetype": mimetype,

            # Element iOS compatibility hack
            "thumbnail_url": mxc,
            "thumbnail_info": {
                "w": width,
                "h": height,
                "size": size,
                "mimetype": mimetype,
            },
        },
        "msgtype": "m.sticker",
    }
