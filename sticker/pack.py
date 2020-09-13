# Copyright (c) 2020 Tulir Asokan
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from hashlib import sha256
import argparse
import os.path
import asyncio
import string
import json

import magic

from .lib import matrix, util


def convert_name(name: str) -> str:
    name_translate = {
        ord(" "): ord("_"),
    }
    allowed_chars = string.ascii_letters + string.digits + "_-/.#"
    return "".join(filter(lambda char: char in allowed_chars, name.translate(name_translate)))


async def main(args: argparse.Namespace) -> None:
    await matrix.load_config(args.config)

    dirname = os.path.basename(os.path.abspath(args.path))
    meta_path = os.path.join(args.path, "pack.json")
    try:
        with open(meta_path) as pack_file:
            pack = json.load(pack_file)
            print(f"Loaded existing pack meta from {meta_path}")
    except FileNotFoundError:
        pack = {
            "title": args.title or dirname,
            "id": args.id or convert_name(dirname),
            "stickers": [],
        }
        old_stickers = {}
    else:
        old_stickers = {sticker["id"]: sticker for sticker in pack["stickers"]}
        pack["stickers"] = []
    for file in sorted(os.listdir(args.path)):
        if file.startswith("."):
            continue
        path = os.path.join(args.path, file)
        if not os.path.isfile(path):
            continue
        mime = magic.from_file(path, mime=True)
        if not mime.startswith("image/"):
            continue

        try:
            with open(path, "rb") as image_file:
                image_data = image_file.read()
        except Exception as e:
            print(f"Failed to read {file}: {e}")
            continue
        print(f"Processing {file}", end="", flush=True)
        name = os.path.splitext(file)[0]

        # If the name starts with "number-", remove the prefix
        name_split = name.split("-", 1)
        if len(name_split) == 2 and name_split[0].isdecimal():
            name = name_split[1]

        sticker_id = f"sha256:{sha256(image_data).hexdigest()}"
        print(".", end="", flush=True)
        if sticker_id in old_stickers:
            pack["stickers"].append({
                **old_stickers[sticker_id],
                "body": name,
            })
            print(f".. using existing upload")
        else:
            image_data, width, height = util.convert_image(image_data)
            print(".", end="", flush=True)
            mxc = await matrix.upload(image_data, "image/png", file)
            print(".", end="", flush=True)
            sticker = util.make_sticker(mxc, width, height, len(image_data), name)
            sticker["id"] = sticker_id
            pack["stickers"].append(sticker)
            print(" uploaded", flush=True)
    with open(meta_path, "w") as pack_file:
        json.dump(pack, pack_file)
    print(f"Wrote pack to {meta_path}")


parser = argparse.ArgumentParser()
parser.add_argument("--config",
                    help="Path to JSON file with Matrix homeserver and access_token",
                    type=str, default="config.json")
parser.add_argument("--title", help="Override the sticker pack displayname", type=str)
parser.add_argument("--id", help="Override the sticker pack ID", type=str)
parser.add_argument("path", help="Path to the sticker pack directory", type=str)


def cmd():
    asyncio.get_event_loop().run_until_complete(main(parser.parse_args()))


if __name__ == "__main__":
    cmd()
