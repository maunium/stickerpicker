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
import numpy as np
import os.path
import subprocess
import json
import tempfile
import mimetypes

try:
    import magic
except ImportError:
    print("[Warning] Magic is not installed, using file extensions to guess mime types")
    magic = None
from PIL import Image, ImageSequence, ImageFilter

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
        with tempfile.NamedTemporaryFile() as temp:
            temp.write(data)
            temp.close()
            mime, _ = mimetypes.guess_type(temp.name)
    return mime or "image/png"


def _video_to_webp(data: bytes) -> bytes:
    mime = guess_mime(data)
    ext = mimetypes.guess_extension(mime)
    with tempfile.NamedTemporaryFile(suffix=ext) as video:
        video.write(data)
        video.flush()
        with tempfile.NamedTemporaryFile(suffix=".webp") as webp:
            print(".", end="", flush=True)
            ffmpeg_encoder_args = []
            if mime == "video/webm":
                encode = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=codec_name", "-of", "default=nokey=1:noprint_wrappers=1", video.name], capture_output=True, text=True).stdout.strip()
                ffmpeg_encoder = None
                if encode == "vp8":
                    ffmpeg_encoder = "libvpx"
                elif encode == "vp9":
                    ffmpeg_encoder = "libvpx-vp9"
                if ffmpeg_encoder:
                    ffmpeg_encoder_args = ["-c:v", ffmpeg_encoder]
            result = subprocess.run(["ffmpeg", "-y", "-threads", "auto", *ffmpeg_encoder_args, "-i", video.name, "-lossless", "1", webp.name],
                                    capture_output=True)
            if result.returncode != 0:
                raise RuntimeError(f"Run ffmpeg failed with code {result.returncode}, Error occurred:\n{result.stderr}")
            webp.seek(0)
            return webp.read()


def video_to_webp(data: bytes) -> bytes:
    mime = guess_mime(data)
    ext = mimetypes.guess_extension(mime)
    # run ffmpeg to fix duration
    with tempfile.NamedTemporaryFile(suffix=ext) as temp:
        temp.write(data)
        temp.flush()
        with tempfile.NamedTemporaryFile(suffix=ext) as temp_fixed:
            print(".", end="", flush=True)
            result = subprocess.run(["ffmpeg", "-y", "-threads", "auto", "-i", temp.name, "-codec", "copy", temp_fixed.name],
                                    capture_output=True)
            if result.returncode != 0:
                raise RuntimeError(f"Run ffmpeg failed with code {result.returncode}, Error occurred:\n{result.stderr}")
            temp_fixed.seek(0)
            data = temp_fixed.read()
    return _video_to_webp(data)


def process_frame(frame):
    """
    Process GIF frame, repair edges, ensure no white or semi-transparent pixels, while keeping color information intact.
    """
    frame = frame.convert('RGBA')

    # Decompose Alpha channel
    alpha = frame.getchannel('A')

    # Process Alpha channel with threshold, remove semi-transparent pixels
    # Threshold can be adjusted as needed (0-255), 128 is the middle value
    threshold = 128
    alpha = alpha.point(lambda x: 255 if x >= threshold else 0)

    # Process Alpha channel with MinFilter, remove edge noise
    alpha = alpha.filter(ImageFilter.MinFilter(3))

    # Process Alpha channel with MaxFilter, repair edges
    alpha = alpha.filter(ImageFilter.MaxFilter(3))

    # Apply processed Alpha channel back to image
    frame.putalpha(alpha)

    return frame


def webp_to_others(data: bytes, mimetype: str) -> bytes:
    format = mimetypes.guess_extension(mimetype)[1:]
    print(format)
    with Image.open(BytesIO(data)) as webp:
        with BytesIO() as img:
            print(".", end="", flush=True)
            webp.info.pop('background', None)

            if mimetype == "image/gif":
                frames = []
                duration = [100, ]

                for frame in ImageSequence.Iterator(webp):
                    frame = process_frame(frame)
                    frames.append(frame)
                    duration.append(frame.info.get('duration', duration[-1]))

                frames[0].save(img, format=format, save_all=True, lossless=True, quality=100, method=6,
                               append_images=frames[1:], loop=0, duration=duration[1:], disposal=2)
            else:
                webp.save(img, format=format, lossless=True, quality=100, method=6)

            img.seek(0)
            return img.read()


def is_uniform_animated_webp(data: bytes) -> bool:
    with Image.open(BytesIO(data)) as img:
        if img.n_frames <= 1:
            return True

        img_iter = ImageSequence.Iterator(img)
        first_frame = np.array(img_iter[0].convert("RGBA"))

        for frame in img_iter:
            current_frame = np.array(frame.convert("RGBA"))
            if not np.array_equal(first_frame, current_frame):
                return False

    return True


def webp_to_gif_or_png(data: bytes) -> bytes:
    with Image.open(BytesIO(data)) as image:
        # check if the webp is animated
        is_animated = getattr(image, "is_animated", False)
        if is_animated and not is_uniform_animated_webp(data):
            return webp_to_others(data, "image/gif")
        else:
            # convert to png
            return webp_to_others(data, "image/png")


def opermize_gif(data: bytes) -> bytes:
    with tempfile.NamedTemporaryFile() as gif:
        gif.write(data)
        gif.flush()
        # use gifsicle to optimize gif
        result = subprocess.run(["gifsicle", "--batch", "--optimize=3", "--colors=256", gif.name],
                                capture_output=True)
        if result.returncode != 0:
            raise RuntimeError(f"Run gifsicle failed with code {result.returncode}, Error occurred:\n{result.stderr}")
        gif.seek(0)
        return gif.read()


def _convert_image(data: bytes, mimetype: str) -> (bytes, int, int):
    with Image.open(BytesIO(data)) as image:
        with BytesIO() as new_file:
            # Determine if the image is a GIF
            is_animated = getattr(image, "is_animated", False)
            if is_animated:
                frames = [frame.convert("RGBA") for frame in ImageSequence.Iterator(image)]
                # Save the new GIF
                frames[0].save(
                    new_file,
                    format='GIF',
                    save_all=True,
                    append_images=frames[1:],
                    loop=image.info.get('loop', 0),  # Default loop to 0 if not present
                    duration=image.info.get('duration', 100),  # Set a default duration if not present
                    disposal=image.info.get('disposal', 2)  # Default to disposal method 2 (restore to background)
                )
                # Get the size of the first frame to determine resizing
                w, h = frames[0].size
            else:
                suffix = mimetypes.guess_extension(mimetype)
                if suffix:
                    suffix = suffix[1:]
                image = image.convert("RGBA")
                image.save(new_file, format=suffix)
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


def _convert_sticker(data: bytes) -> (bytes, str, int, int):
    mimetype = guess_mime(data)
    if mimetype.startswith("video/"):
        data = video_to_webp(data)
        print(".", end="", flush=True)
    elif mimetype.startswith("application/gzip"):
        print(".", end="", flush=True)
        # unzip file
        import gzip
        with gzip.open(BytesIO(data), "rb") as f:
            data = f.read()
            mimetype = guess_mime(data)
            suffix = mimetypes.guess_extension(mimetype)
            with tempfile.NamedTemporaryFile(suffix=suffix) as temp:
                temp.write(data)
                with tempfile.NamedTemporaryFile(suffix=".webp") as gif:
                    # run lottie_convert.py input output
                    print(".", end="", flush=True)
                    import subprocess
                    cmd = ["lottie_convert.py", temp.name, gif.name]
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    retcode = result.returncode
                    if retcode != 0:
                        raise RuntimeError(f"Run {cmd} failed with code {retcode}, Error occurred:\n{result.stderr}")
                    gif.seek(0)
                    data = gif.read()
    mimetype = guess_mime(data)
    if mimetype == "image/webp":
        data = webp_to_gif_or_png(data)
        mimetype = guess_mime(data)
    rlt = _convert_image(data, mimetype)
    data = rlt[0]
    if mimetype == "image/gif":
        print(".", end="", flush=True)
        data = opermize_gif(data)
    return data, mimetype, rlt[1], rlt[2]


def convert_sticker(data: bytes) -> (bytes, str, int, int):
    try:
        return _convert_sticker(data)
    except Exception as e:
        mimetype = guess_mime(data)
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
